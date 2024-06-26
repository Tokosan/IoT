#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "esp_bt.h"
#include "esp_bt_defs.h"
#include "esp_bt_device.h"
#include "esp_bt_main.h"
#include "esp_event.h"
#include "esp_gap_ble_api.h"
#include "esp_gatt_common_api.h"
#include "esp_gatts_api.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_sleep.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "lwip/err.h"
#include "lwip/sockets.h"  // Para sockets
#include "lwip/sys.h"
#include "nvs_flash.h"
#include "sdkconfig.h"

// si esta esto seteado a TRUE, lo unico que hara la ESP es dejar el status en 0 y apagarse.
#define BOOT false

#define GATTS_TAG "GATTS_DEMO"
static void gatts_profile_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param);
#define GATTS_SERVICE_UUID_A 0x00FF
#define GATTS_CHAR_UUID_A 0xFF01  // Caracteristicas
#define GATTS_DESCR_UUID_A 0x3333
#define GATTS_NUM_HANDLE_A 4
#define DEVICE_NAME "ESP 32"
#define TEST_MANUFACTURER_DATA_LEN 17
#define GATTS_DEMO_CHAR_VAL_LEN_MAX 0x40
#define PREPARE_BUF_MAX_SIZE 1024

// BLE
static uint8_t char1_str[] = {0x11, 0x22, 0x33};
static esp_gatt_char_prop_t a_property = 0;
static esp_attr_value_t gatts_demo_char1_val = {
    .attr_max_len = GATTS_DEMO_CHAR_VAL_LEN_MAX,
    .attr_len = sizeof(char1_str),
    .attr_value = char1_str,
};
static uint8_t adv_config_done = 0;
#define adv_config_flag (1 << 0)
#define scan_rsp_config_flag (1 << 1)

static uint8_t adv_service_uuid128[32] = {
    /* LSB <--------------------------------------------------------------------------------> MSB */
    // first uuid, 16bit, [12],[13] is the value
    0xfb,
    0x34,
    0x9b,
    0x5f,
    0x80,
    0x00,
    0x00,
    0x80,
    0x00,
    0x10,
    0x00,
    0x00,
    0xEE,
    0x00,
    0x00,
    0x00,
    // second uuid, 32bit, [12], [13], [14], [15] is the value
    0xfb,
    0x34,
    0x9b,
    0x5f,
    0x80,
    0x00,
    0x00,
    0x80,
    0x00,
    0x10,
    0x00,
    0x00,
    0xFF,
    0x00,
    0x00,
    0x00,
};

// The length of adv data must be less than 31 bytes
// static uint8_t test_manufacturer[TEST_MANUFACTURER_DATA_LEN] =  {0x12, 0x23, 0x45, 0x56};
// adv data
static esp_ble_adv_data_t adv_data = {
    .set_scan_rsp = false,
    .include_name = true,
    .include_txpower = false,
    .min_interval = 0x0006,  // slave connection min interval, Time = min_interval * 1.25 msec
    .max_interval = 0x0010,  // slave connection max interval, Time = max_interval * 1.25 msec
    .appearance = 0x00,
    .manufacturer_len = 0,        // TEST_MANUFACTURER_DATA_LEN,
    .p_manufacturer_data = NULL,  //&test_manufacturer[0],
    .service_data_len = 0,
    .p_service_data = NULL,
    .service_uuid_len = sizeof(adv_service_uuid128),
    .p_service_uuid = adv_service_uuid128,
    .flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT),
};
// scan response data
static esp_ble_adv_data_t scan_rsp_data = {
    .set_scan_rsp = true,
    .include_name = true,
    .include_txpower = true,
    //.min_interval = 0x0006,
    //.max_interval = 0x0010,
    .appearance = 0x00,
    .manufacturer_len = 0,        // TEST_MANUFACTURER_DATA_LEN,
    .p_manufacturer_data = NULL,  //&test_manufacturer[0],
    .service_data_len = 0,
    .p_service_data = NULL,
    .service_uuid_len = sizeof(adv_service_uuid128),
    .p_service_uuid = adv_service_uuid128,
    .flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT),
};
static esp_ble_adv_params_t adv_params = {
    .adv_int_min = 0x20,
    .adv_int_max = 0x40,
    .adv_type = ADV_TYPE_IND,
    .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
    //.peer_addr            =
    //.peer_addr_type       =
    .channel_map = ADV_CHNL_ALL,
    .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};
#define PROFILE_NUM 2
#define PROFILE_APP_ID 0

typedef uint8_t byte1_t;
typedef uint16_t byte2_t;
typedef uint32_t byte4_t;

// Tamano de los paquetes segun el protocolo
#define PACKET_SIZE_BASE 1
#define PACKET_SIZE_P1 6
#define PACKET_SIZE_P2 16
#define PACKET_SIZE_P3 20
#define PACKET_SIZE_P4 44

int packet_len[] = {
    PACKET_SIZE_BASE,
    PACKET_SIZE_P1,
    PACKET_SIZE_P2,
    PACKET_SIZE_P3,
    PACKET_SIZE_P4
};

typedef struct Config {
    int32_t status;
    int32_t id_protocol;
    int32_t bmi_samp;
    int32_t acc_sens;
    int32_t gyr_sens;
    int32_t bme_samp;
    int32_t disc_time;
    int32_t tcp_port;
    int32_t udp_port;
    char host_ip_addr[16];
    char ssid[10];
    char pass[10];
} Config;

Config config;
byte1_t *packet;

struct gatts_profile_inst {
    esp_gatts_cb_t gatts_cb;
    uint16_t gatts_if;
    uint16_t app_id;
    uint16_t conn_id;
    uint16_t service_handle;
    esp_gatt_srvc_id_t service_id;
    uint16_t char_handle;
    esp_bt_uuid_t char_uuid;
    esp_gatt_perm_t perm;
    esp_gatt_char_prop_t property;
    uint16_t descr_handle;
    esp_bt_uuid_t descr_uuid;
};

void generate_packet();
void set_config();
void get_config();
void print_config();

/* One gatt-based profile one app_id and one gatts_if, this array will store the gatts_if returned by ESP_GATTS_REG_EVT */
static struct gatts_profile_inst gl_profile_tab[PROFILE_NUM] = {
    [PROFILE_APP_ID] = {
        .gatts_cb = gatts_profile_event_handler,
        .gatts_if = ESP_GATT_IF_NONE, /* Not get the gatt_if, so initial is ESP_GATT_IF_NONE */
    },
};

typedef struct {
    uint8_t *prepare_buf;
    int prepare_len;
} prepare_type_env_t;

static prepare_type_env_t a_prepare_write_env;

void example_write_event_env(esp_gatt_if_t gatts_if, prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param);
void example_exec_write_event_env(prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param);

static void gap_event_handler(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param) {
    switch (event) {
#ifdef CONFIG_SET_RAW_ADV_DATA
    case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT:
        adv_config_done &= (~adv_config_flag);
        if (adv_config_done == 0) {
            esp_ble_gap_start_advertising(&adv_params);
        }
        break;
    case ESP_GAP_BLE_SCAN_RSP_DATA_RAW_SET_COMPLETE_EVT:
        adv_config_done &= (~scan_rsp_config_flag);
        if (adv_config_done == 0) {
            esp_ble_gap_start_advertising(&adv_params);
        }
        break;
#else
    case ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT:
        adv_config_done &= (~adv_config_flag);
        if (adv_config_done == 0) {
            esp_ble_gap_start_advertising(&adv_params);
        }
        break;
    case ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT:
        adv_config_done &= (~scan_rsp_config_flag);
        if (adv_config_done == 0) {
            esp_ble_gap_start_advertising(&adv_params);
        }
        break;
#endif
    case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        // advertising start complete event to indicate advertising start successfully or failed
        if (param->adv_start_cmpl.status != ESP_BT_STATUS_SUCCESS) {
            ESP_LOGE(GATTS_TAG, "Advertising start failed");
        }
        break;
    case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        if (param->adv_stop_cmpl.status != ESP_BT_STATUS_SUCCESS) {
            ESP_LOGE(GATTS_TAG, "Advertising stop failed");
        } else {
            ESP_LOGI(GATTS_TAG, "Stop adv successfully");
        }
        break;
    case ESP_GAP_BLE_UPDATE_CONN_PARAMS_EVT:
        ESP_LOGI(GATTS_TAG, "update connection params status = %d, min_int = %d, max_int = %d,conn_int = %d,latency = %d, timeout = %d",
                 param->update_conn_params.status,
                 param->update_conn_params.min_int,
                 param->update_conn_params.max_int,
                 param->update_conn_params.conn_int,
                 param->update_conn_params.latency,
                 param->update_conn_params.timeout);
        break;
    case ESP_GAP_BLE_SET_PKT_LENGTH_COMPLETE_EVT:
        ESP_LOGI(GATTS_TAG, "packet length updated: rx = %d, tx = %d, status = %d",
                 param->pkt_data_length_cmpl.params.rx_len,
                 param->pkt_data_length_cmpl.params.tx_len,
                 param->pkt_data_length_cmpl.status);
        break;
    default:
        break;
    }
}

void example_write_event_env(esp_gatt_if_t gatts_if, prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param) {
    esp_gatt_status_t status = ESP_GATT_OK;
    if (param->write.need_rsp) {
        if (param->write.is_prep) {
            if (param->write.offset > PREPARE_BUF_MAX_SIZE) {
                status = ESP_GATT_INVALID_OFFSET;
            } else if ((param->write.offset + param->write.len) > PREPARE_BUF_MAX_SIZE) {
                status = ESP_GATT_INVALID_ATTR_LEN;
            }
            if (status == ESP_GATT_OK && prepare_write_env->prepare_buf == NULL) {
                prepare_write_env->prepare_buf = (uint8_t *)malloc(PREPARE_BUF_MAX_SIZE * sizeof(uint8_t));
                prepare_write_env->prepare_len = 0;
                if (prepare_write_env->prepare_buf == NULL) {
                    ESP_LOGE(GATTS_TAG, "Gatt_server prep no mem");
                    status = ESP_GATT_NO_RESOURCES;
                }
            }

            esp_gatt_rsp_t *gatt_rsp = (esp_gatt_rsp_t *)malloc(sizeof(esp_gatt_rsp_t));
            if (gatt_rsp) {
                gatt_rsp->attr_value.len = param->write.len;
                gatt_rsp->attr_value.handle = param->write.handle;
                gatt_rsp->attr_value.offset = param->write.offset;
                gatt_rsp->attr_value.auth_req = ESP_GATT_AUTH_REQ_NONE;
                memcpy(gatt_rsp->attr_value.value, param->write.value, param->write.len);
                esp_err_t response_err = esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, status, gatt_rsp);
                if (response_err != ESP_OK) {
                    ESP_LOGE(GATTS_TAG, "Send response error\n");
                }
                free(gatt_rsp);
            } else {
                ESP_LOGE(GATTS_TAG, "malloc failed, no resource to send response error\n");
                status = ESP_GATT_NO_RESOURCES;
            }
            if (status != ESP_GATT_OK) {
                return;
            }
            memcpy(prepare_write_env->prepare_buf + param->write.offset,
                   param->write.value,
                   param->write.len);
            prepare_write_env->prepare_len += param->write.len;

        } else {
            esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, status, NULL);
        }
    }
}

void example_exec_write_event_env(prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param) {
    if (param->exec_write.exec_write_flag == ESP_GATT_PREP_WRITE_EXEC) {
        ESP_LOG_BUFFER_HEX(GATTS_TAG, prepare_write_env->prepare_buf, prepare_write_env->prepare_len);
    } else {
        ESP_LOGI(GATTS_TAG, "ESP_GATT_PREP_WRITE_CANCEL");
    }
    if (prepare_write_env->prepare_buf) {
        free(prepare_write_env->prepare_buf);
        prepare_write_env->prepare_buf = NULL;
    }
    prepare_write_env->prepare_len = 0;
}

static void gatts_profile_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param) {
    switch (event) {
    case ESP_GATTS_REG_EVT:
        ESP_LOGI(GATTS_TAG, "REGISTER_APP_EVT, status %d, app_id %d", param->reg.status, param->reg.app_id);
        gl_profile_tab[PROFILE_APP_ID].service_id.is_primary = true;
        gl_profile_tab[PROFILE_APP_ID].service_id.id.inst_id = 0x00;
        gl_profile_tab[PROFILE_APP_ID].service_id.id.uuid.len = ESP_UUID_LEN_16;
        gl_profile_tab[PROFILE_APP_ID].service_id.id.uuid.uuid.uuid16 = GATTS_SERVICE_UUID_A;

        esp_err_t set_dev_name_ret = esp_ble_gap_set_device_name(DEVICE_NAME);
        if (set_dev_name_ret) {
            ESP_LOGE(GATTS_TAG, "set device name failed, error code = %x", set_dev_name_ret);
        }
#ifdef CONFIG_SET_RAW_ADV_DATA
        esp_err_t raw_adv_ret = esp_ble_gap_config_adv_data_raw(raw_adv_data, sizeof(raw_adv_data));
        if (raw_adv_ret) {
            ESP_LOGE(GATTS_TAG, "config raw adv data failed, error code = %x ", raw_adv_ret);
        }
        adv_config_done |= adv_config_flag;
        esp_err_t raw_scan_ret = esp_ble_gap_config_scan_rsp_data_raw(raw_scan_rsp_data, sizeof(raw_scan_rsp_data));
        if (raw_scan_ret) {
            ESP_LOGE(GATTS_TAG, "config raw scan rsp data failed, error code = %x", raw_scan_ret);
        }
        adv_config_done |= scan_rsp_config_flag;
#else
        // config adv data
        esp_err_t ret = esp_ble_gap_config_adv_data(&adv_data);
        if (ret) {
            ESP_LOGE(GATTS_TAG, "config adv data failed, error code = %x", ret);
        }
        adv_config_done |= adv_config_flag;
        // config scan response data
        ret = esp_ble_gap_config_adv_data(&scan_rsp_data);
        if (ret) {
            ESP_LOGE(GATTS_TAG, "config scan response data failed, error code = %x", ret);
        }
        adv_config_done |= scan_rsp_config_flag;

#endif
        esp_ble_gatts_create_service(gatts_if, &gl_profile_tab[PROFILE_APP_ID].service_id, GATTS_NUM_HANDLE_A);
        break;
    case ESP_GATTS_READ_EVT: {
        ESP_LOGI(GATTS_TAG, "GATT_READ_EVT, conn_id %d, trans_id %" PRIu32 ", handle %d", param->read.conn_id, param->read.trans_id, param->read.handle);
        esp_gatt_rsp_t rsp;
        memset(&rsp, 0, sizeof(esp_gatt_rsp_t));
        rsp.attr_value.handle = param->read.handle;

        // generamos el paquete correspondiente
        protocol = config.id_protocol;
        generate_packet();

        rsp.attr_value.len = packet_len[protocol];
        for (int i = 0; i < rsp.attr_value.len; i++) {
            rsp.attr_value.value[i] = packet[i];
        }
        esp_ble_gatts_send_response(gatts_if, param->read.conn_id, param->read.trans_id,
                                    ESP_GATT_OK, &rsp);
        
        if (config.status == 31) {
            esp_deep_sleep(1000 * config.disc_time);
        }

        break;
    }
    case ESP_GATTS_WRITE_EVT: {
        ESP_LOGI(GATTS_TAG, "GATT_WRITE_EVT, conn_id %d, trans_id %" PRIu32 ", handle %d", param->write.conn_id, param->write.trans_id, param->write.handle);
        if (!param->write.is_prep) {
            printf("Configuracion recibida: ");
            // since write.value is a uint8_t*, we write it as hexadecimal
            for (int i = 0; i < param->write.len; i++) {
                printf("%02x ", param->write.value[i]);
            }
            uint8_t *data = param->write.value;
            // si es que recibimos algo aca entonces es una configuracion y tenemos que guardarla!
            config.status = data[0];
            config.id_protocol = data[1];

            // HARDCODEADO!!!
            // no se por que
            data += 2;
            // pero aparecen dos bytes nada que ver al principio
            // HARDCODEADO!!!

            config.bmi_samp = (data[5] << 24) | (data[4] << 16) | (data[3] << 8) | data[2];
            config.acc_sens = (data[9] << 24) | (data[8] << 16) | (data[7] << 8) | data[6];
            config.gyr_sens = (data[13] << 24) | (data[12] << 16) | (data[11] << 8) | data[10];
            config.bme_samp = (data[17] << 24) | (data[16] << 16) | (data[15] << 8) | data[14];
            config.disc_time = (data[21] << 24) | (data[20] << 16) | (data[19] << 8) | data[18];
            config.tcp_port = (data[25] << 24) | (data[24] << 16) | (data[23] << 8) | data[22];
            config.udp_port = (data[29] << 24) | (data[28] << 16) | (data[27] << 8) | data[26];

            int i = 30;
            int j = 0;
            while (data[i] != 0) {
                config.ssid[j] = data[i];
                i++;
                j++;
            }
            config.ssid[j] = 0;
            i++;
            j = 0;
            while (data[i] != 0) {
                config.pass[j] = data[i];
                i++;
                j++;
            }
            config.pass[j] = 0;
            i++;
            j = 0;
            while (data[i] != 0) {
                config.host_ip_addr[j] = data[i];
                i++;
                j++;
            }
            config.host_ip_addr[j] = 0;

            // guardamos la configuracion en NVS
            print_config();
            set_config();

            ESP_LOGI(GATTS_TAG, "GATT_WRITE_EVT, value len %d, value :", param->write.len);
            ESP_LOG_BUFFER_HEX(GATTS_TAG, param->write.value, param->write.len);
            if (gl_profile_tab[PROFILE_APP_ID].descr_handle == param->write.handle && param->write.len == 2) {
                uint16_t descr_value = param->write.value[1] << 8 | param->write.value[0];
                if (descr_value == 0x0001) {
                    if (a_property & ESP_GATT_CHAR_PROP_BIT_NOTIFY) {
                        ESP_LOGI(GATTS_TAG, "notify enable");
                        uint8_t notify_data[15];
                        for (int i = 0; i < sizeof(notify_data); ++i) {
                            notify_data[i] = i % 0xff;
                        }
                        // the size of notify_data[] need less than MTU size
                        esp_ble_gatts_send_indicate(gatts_if, param->write.conn_id, gl_profile_tab[PROFILE_APP_ID].char_handle,
                                                    sizeof(notify_data), notify_data, false);
                    }
                } else if (descr_value == 0x0002) {
                    if (a_property & ESP_GATT_CHAR_PROP_BIT_INDICATE) {
                        ESP_LOGI(GATTS_TAG, "indicate enable");
                        uint8_t indicate_data[15];
                        for (int i = 0; i < sizeof(indicate_data); ++i) {
                            indicate_data[i] = i % 0xff;
                        }
                        // the size of indicate_data[] need less than MTU size
                        esp_ble_gatts_send_indicate(gatts_if, param->write.conn_id, gl_profile_tab[PROFILE_APP_ID].char_handle,
                                                    sizeof(indicate_data), indicate_data, true);
                    }
                } else if (descr_value == 0x0000) {
                    ESP_LOGI(GATTS_TAG, "notify/indicate disable ");
                } else {
                    ESP_LOGE(GATTS_TAG, "unknown descr value");
                    ESP_LOG_BUFFER_HEX(GATTS_TAG, param->write.value, param->write.len);
                }
            }
        }
        example_write_event_env(gatts_if, &a_prepare_write_env, param);
        break;
    }
    case ESP_GATTS_EXEC_WRITE_EVT:
        ESP_LOGI(GATTS_TAG, "ESP_GATTS_EXEC_WRITE_EVT");
        esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, ESP_GATT_OK, NULL);
        example_exec_write_event_env(&a_prepare_write_env, param);
        break;
    case ESP_GATTS_MTU_EVT:
        ESP_LOGI(GATTS_TAG, "ESP_GATTS_MTU_EVT, MTU %d", param->mtu.mtu);
        break;
    case ESP_GATTS_UNREG_EVT:
        break;
    case ESP_GATTS_CREATE_EVT:
        ESP_LOGI(GATTS_TAG, "CREATE_SERVICE_EVT, status %d,  service_handle %d", param->create.status, param->create.service_handle);
        gl_profile_tab[PROFILE_APP_ID].service_handle = param->create.service_handle;
        gl_profile_tab[PROFILE_APP_ID].char_uuid.len = ESP_UUID_LEN_16;
        gl_profile_tab[PROFILE_APP_ID].char_uuid.uuid.uuid16 = GATTS_CHAR_UUID_A;

        esp_ble_gatts_start_service(gl_profile_tab[PROFILE_APP_ID].service_handle);
        a_property = ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_WRITE | ESP_GATT_CHAR_PROP_BIT_NOTIFY;
        esp_err_t add_char_ret = esp_ble_gatts_add_char(gl_profile_tab[PROFILE_APP_ID].service_handle, &gl_profile_tab[PROFILE_APP_ID].char_uuid,
                                                        ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
                                                        a_property,
                                                        &gatts_demo_char1_val, NULL);
        if (add_char_ret) {
            ESP_LOGE(GATTS_TAG, "add char failed, error code =%x", add_char_ret);
        }
        break;
    case ESP_GATTS_ADD_INCL_SRVC_EVT:
        break;
    case ESP_GATTS_ADD_CHAR_EVT: {
        uint16_t length = 0;
        const uint8_t *prf_char;

        ESP_LOGI(GATTS_TAG, "ADD_CHAR_EVT, status %d,  attr_handle %d, service_handle %d",
                 param->add_char.status, param->add_char.attr_handle, param->add_char.service_handle);
        gl_profile_tab[PROFILE_APP_ID].char_handle = param->add_char.attr_handle;
        gl_profile_tab[PROFILE_APP_ID].descr_uuid.len = ESP_UUID_LEN_16;
        gl_profile_tab[PROFILE_APP_ID].descr_uuid.uuid.uuid16 = ESP_GATT_UUID_CHAR_CLIENT_CONFIG;
        esp_err_t get_attr_ret = esp_ble_gatts_get_attr_value(param->add_char.attr_handle, &length, &prf_char);
        if (get_attr_ret == ESP_FAIL) {
            ESP_LOGE(GATTS_TAG, "ILLEGAL HANDLE");
        }

        ESP_LOGI(GATTS_TAG, "the gatts demo char length = %x", length);
        for (int i = 0; i < length; i++) {
            ESP_LOGI(GATTS_TAG, "prf_char[%x] =%x", i, prf_char[i]);
        }
        esp_err_t add_descr_ret = esp_ble_gatts_add_char_descr(gl_profile_tab[PROFILE_APP_ID].service_handle, &gl_profile_tab[PROFILE_APP_ID].descr_uuid,
                                                               ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE, NULL, NULL);
        if (add_descr_ret) {
            ESP_LOGE(GATTS_TAG, "add char descr failed, error code =%x", add_descr_ret);
        }
        break;
    }
    case ESP_GATTS_ADD_CHAR_DESCR_EVT:
        gl_profile_tab[PROFILE_APP_ID].descr_handle = param->add_char_descr.attr_handle;
        ESP_LOGI(GATTS_TAG, "ADD_DESCR_EVT, status %d, attr_handle %d, service_handle %d",
                 param->add_char_descr.status, param->add_char_descr.attr_handle, param->add_char_descr.service_handle);
        break;
    case ESP_GATTS_DELETE_EVT:
        break;
    case ESP_GATTS_START_EVT:
        ESP_LOGI(GATTS_TAG, "SERVICE_START_EVT, status %d, service_handle %d",
                 param->start.status, param->start.service_handle);
        break;
    case ESP_GATTS_STOP_EVT:
        break;
    case ESP_GATTS_CONNECT_EVT: {
        esp_ble_conn_update_params_t conn_params = {0};
        memcpy(conn_params.bda, param->connect.remote_bda, sizeof(esp_bd_addr_t));
        /* For the IOS system, please reference the apple official documents about the ble connection parameters restrictions. */
        conn_params.latency = 0;
        conn_params.max_int = 0x20;  // max_int = 0x20*1.25ms = 40ms
        conn_params.min_int = 0x10;  // min_int = 0x10*1.25ms = 20ms
        conn_params.timeout = 400;   // timeout = 400*10ms = 4000ms
        ESP_LOGI(GATTS_TAG, "ESP_GATTS_CONNECT_EVT, conn_id %d, remote %02x:%02x:%02x:%02x:%02x:%02x:",
                 param->connect.conn_id,
                 param->connect.remote_bda[0], param->connect.remote_bda[1], param->connect.remote_bda[2],
                 param->connect.remote_bda[3], param->connect.remote_bda[4], param->connect.remote_bda[5]);
        gl_profile_tab[PROFILE_APP_ID].conn_id = param->connect.conn_id;
        // start sent the update connection parameters to the peer device.
        esp_ble_gap_update_conn_params(&conn_params);
        break;
    }
    case ESP_GATTS_DISCONNECT_EVT:
        ESP_LOGI(GATTS_TAG, "ESP_GATTS_DISCONNECT_EVT, disconnect reason 0x%x", param->disconnect.reason);
        esp_ble_gap_start_advertising(&adv_params);
        break;
    case ESP_GATTS_CONF_EVT:
        ESP_LOGI(GATTS_TAG, "ESP_GATTS_CONF_EVT, status %d attr_handle %d", param->conf.status, param->conf.handle);
        if (param->conf.status != ESP_GATT_OK) {
            ESP_LOG_BUFFER_HEX(GATTS_TAG, param->conf.value, param->conf.len);
        }
        break;
    case ESP_GATTS_OPEN_EVT:
    case ESP_GATTS_CANCEL_OPEN_EVT:
    case ESP_GATTS_CLOSE_EVT:
    case ESP_GATTS_LISTEN_EVT:
    case ESP_GATTS_CONGEST_EVT:
    default:
        break;
    }
}

static void gatts_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param) {
    /* If event is register event, store the gatts_if for each profile */
    if (event == ESP_GATTS_REG_EVT) {
        if (param->reg.status == ESP_GATT_OK) {
            gl_profile_tab[param->reg.app_id].gatts_if = gatts_if;
        } else {
            ESP_LOGI(GATTS_TAG, "Reg app failed, app_id %04x, status %d",
                     param->reg.app_id,
                     param->reg.status);
            return;
        }
    }

    /* If the gatts_if equal to profile A, call profile A cb handler,
     * so here call each profile's callback */
    do {
        int idx;
        for (idx = 0; idx < PROFILE_NUM; idx++) {
            if (gatts_if == ESP_GATT_IF_NONE || /* ESP_GATT_IF_NONE, not specify a certain gatt_if, need to call every profile cb function */
                gatts_if == gl_profile_tab[idx].gatts_if) {
                if (gl_profile_tab[idx].gatts_cb) {
                    gl_profile_tab[idx].gatts_cb(event, gatts_if, param);
                }
            }
        }
    } while (0);
}

void print_packet() {
    // 1. Bateria
    printf("Bateria:      %d\n", packet[1]);
    printf("Timestamp:    %d\n", (packet[5] << 24) | (packet[4] << 16) | (packet[3] << 8) | packet[2]);
    // 3. THPC
    if (protocol >= 2) {
        printf("Temperatura:  %d\n", packet[6]);
        printf("Humedad:      %d\n", packet[7]);
        // probar *((float *)(packet + 8))
        printf("Presion:      %d\n", (packet[11] << 24) | (packet[10] << 16) | (packet[9] << 8) | packet[8]);
        printf("CO:           %f\n", *((float *)(packet + 23)));
    }
    // 4. IMU
    if (protocol == 3) {
        printf("RMS:          %f\n", *((float *)(packet + 27 - 11)));
        printf("Amplitud X:   %f\n", *((float *)(packet + 31 - 11)));
        printf("Frecuencia X: %f\n", *((float *)(packet + 35 - 11)));
        printf("Amplitud Y:   %f\n", *((float *)(packet + 39 - 11)));
        printf("Frecuencia Y: %f\n", *((float *)(packet + 43 - 11)));
        printf("Amplitud Z:   %f\n", *((float *)(packet + 47 - 11)));
        printf("Frecuencia Z: %f\n", *((float *)(packet + 51 - 11)));
    }
}

void event_handler(void *arg, esp_event_base_t event_base, int32_t event_id,
                   void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT &&
               event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < 10) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
        ESP_LOGI(TAG, "connect to the AP fail");
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void wifi_init_sta(char *ssid, char *password) {
    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

    wifi_config_t wifi_config;
    memset(&wifi_config, 0, sizeof(wifi_config_t));

    // Set the specific fields
    strcpy((char *)wifi_config.sta.ssid, WIFI_SSID);
    strcpy((char *)wifi_config.sta.password, WIFI_PASSWORD);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "wifi_init_sta finished.");

    EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
                                           WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                           pdFALSE, pdFALSE, portMAX_DELAY);

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "connected to ap SSID:%s password:%s", ssid, password);
    } else if (bits & WIFI_FAIL_BIT) {
        ESP_LOGI(TAG, "Failed to connect to SSID:%s, password:%s", ssid, password);
    } else {
        ESP_LOGE(TAG, "UNEXPECTED EVENT");
    }

    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        IP_EVENT, IP_EVENT_STA_GOT_IP, instance_got_ip));
    ESP_ERROR_CHECK(esp_event_handler_instance_unregister(
        WIFI_EVENT, ESP_EVENT_ANY_ID, instance_any_id));
    vEventGroupDelete(s_wifi_event_group);
}

void nvs_init() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

int32_t random_int(int min, int max) {
    return rand() % (max - min + 1) + min;
}

float random_float(float min, float max) {
    float base = (float)rand() / RAND_MAX;
    return base * (max - min) + min;
}

// 1 2 3 4 5
void append_battery() {
    // generamos un numero aleatorio entre 1 y 100
    byte1_t battery = random_int(1, 100);
    printf("Battery: %d\n", battery);
    memcpy(packet + PACKET_SIZE_BASE, (byte1_t *)&battery, 1);
}

// 1 2 3 4 5
void append_timestamp() {
    byte4_t timestamp = time(NULL);
    printf("Timestamp: %ld\n", timestamp);
    memcpy(packet + PACKET_SIZE_BASE + 1, (byte1_t *)&timestamp, 4);
}

// 2 3 4 5
void append_thpc() {
    byte1_t temp = random_int(5, 30);
    byte1_t hum = random_int(30, 80);
    byte4_t pres = random_int(1000, 1200);
    byte4_t co = random_int(30, 200);
    printf("Temperatura: %d\n", temp);
    printf("Humedad: %d\n", hum);
    printf("Presion: %ld\n", pres);
    printf("CO: %ld\n", co);
    memcpy(packet + PACKET_SIZE_P1, (byte1_t *)&temp, 1);
    memcpy(packet + PACKET_SIZE_P1 + 1, (byte1_t *)&hum, 1);
    memcpy(packet + PACKET_SIZE_P1 + 2, (byte1_t *)&pres, 4);
    memcpy(packet + PACKET_SIZE_P1 + 6, (byte1_t *)&co, 4);
}

// 3 4
void append_imu() {
    float amp_x = random_float(0.0059, 0.12);
    float amp_y = random_float(0.0041, 0.11);
    float amp_z = random_float(0.0080, 0.15);
    float freq_x = random_float(29.0, 31.0);
    float freq_y = random_float(59.0, 61.0);
    float freq_z = random_float(89.0, 91.0);
    float rms = sqrt((amp_x * amp_x + amp_y * amp_y + amp_z * amp_z) / 3);

    printf("RMS: %f\n", rms);
    printf("Amplitud X: %f\n", amp_x);
    printf("Frecuencia X: %f\n", freq_x);
    printf("Amplitud Y: %f\n", amp_y);
    printf("Frecuencia Y: %f\n", freq_y);
    printf("Amplitud Z: %f\n", amp_z);
    printf("Frecuencia Z: %f\n", freq_z);

    memcpy(packet + PACKET_SIZE_P2, (byte1_t *)&rms, 4);
    memcpy(packet + PACKET_SIZE_P2 + 4, (byte1_t *)&amp_x, 4);
    memcpy(packet + PACKET_SIZE_P2 + 8, (byte1_t *)&freq_x, 4);
    memcpy(packet + PACKET_SIZE_P2 + 12, (byte1_t *)&amp_y, 4);
    memcpy(packet + PACKET_SIZE_P2 + 16, (byte1_t *)&freq_y, 4);
    memcpy(packet + PACKET_SIZE_P2 + 20, (byte1_t *)&amp_z, 4);
    memcpy(packet + PACKET_SIZE_P2 + 24, (byte1_t *)&freq_z, 4);
}

void append_rms() {
    float amp_x = random_float(0.0059, 0.12);
    float amp_y = random_float(0.0041, 0.11);
    float amp_z = random_float(0.0080, 0.15);
    float rms = sqrt((amp_x * amp_x + amp_y * amp_y + amp_z * amp_z) / 3);
    printf("RMS: %f\n", rms);
    memcpy(packet + PACKET_SIZE_P2, (byte1_t *)&rms, 4);
}

void generate_packet() {
    packet = (byte1_t *)malloc(packet_len[protocol]);
    packet[0] = (byte1_t)protocol;  // id_protocol
    append_battery();
    append_timestamp();
    if (protocol >= 2) {
        append_thpc();
    }
    if (protocol == 3 || protocol == 4) {
        append_rms();
    }
    if (protocol == 4) {
        append_imu();
    }
}

void set_config() {
    // Open
    printf("\n");
    printf("Opening Non-Volatile Storage (NVS) handle... ");
    nvs_handle_t my_handle;

    // Intentamos abrir el storage "config"
    esp_err_t ret = nvs_open("config", NVS_READWRITE, &my_handle);
    if (ret != ESP_OK) {
        printf("Error (%s) opening NVS handle!\n", esp_err_to_name(ret));
        return;
    }
    printf("Done\n");

    // Set
    ret = nvs_set_i32(my_handle, "status", config.status);
    if (ret != ESP_OK) {
        printf("Error (%s) setting status!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "id_protocol", config.id_protocol);
    if (ret != ESP_OK) {
        printf("Error (%s) setting id_protocol!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "bmi_samp", config.bmi_samp);
    if (ret != ESP_OK) {
        printf("Error (%s) setting bmi_samp!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "acc_sens", config.acc_sens);
    if (ret != ESP_OK) {
        printf("Error (%s) setting acc_sens!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "gyr_sens", config.gyr_sens);
    if (ret != ESP_OK) {
        printf("Error (%s) setting gyr_sens!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "disc_time", config.disc_time);
    if (ret != ESP_OK) {
        printf("Error (%s) setting disc_time!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "tcp_port", config.tcp_port);
    if (ret != ESP_OK) {
        printf("Error (%s) setting tcp_port!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_i32(my_handle, "udp_port", config.udp_port);
    if (ret != ESP_OK) {
        printf("Error (%s) setting udp_port!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_str(my_handle, "ssid", config.ssid);
    if (ret != ESP_OK) {
        printf("Error (%s) setting ssid!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_str(my_handle, "pass", config.pass);
    if (ret != ESP_OK) {
        printf("Error (%s) setting pass!\n", esp_err_to_name(ret));
        return;
    }
    ret = nvs_set_str(my_handle, "host_ip_addr", config.host_ip_addr);
    if (ret != ESP_OK) {
        printf("Error (%s) setting host_ip_addr!\n", esp_err_to_name(ret));
        return;
    }

    printf("Committing updates in NVS ... ");
    ret = nvs_commit(my_handle);
    printf((ret != ESP_OK) ? "Failed!\n" : "Done\n");
    nvs_close(my_handle);
}

void get_config() {
    // Open
    printf("\n");
    printf("Opening Non-Volatile Storage (NVS) handle... ");
    nvs_handle_t my_handle;

    // Intentamos abrir el storage "config"
    esp_err_t ret = nvs_open("config", NVS_READWRITE, &my_handle);
    if (ret != ESP_OK) {
        printf("Error (%s) opening NVS handle!\n", esp_err_to_name(ret));
        return;
    }
    printf("Done\n");

    // Read
    printf("Reading status from NVS ... ");
    nvs_get_i32(my_handle, "status", &config.status);
    nvs_get_i32(my_handle, "id_protocol", &config.id_protocol);
    nvs_get_i32(my_handle, "bmi_samp", &config.bmi_samp);
    nvs_get_i32(my_handle, "acc_sens", &config.acc_sens);
    nvs_get_i32(my_handle, "gyr_sens", &config.gyr_sens);
    nvs_get_i32(my_handle, "disc_time", &config.disc_time);
    nvs_get_i32(my_handle, "tcp_port", &config.tcp_port);
    nvs_get_i32(my_handle, "udp_port", &config.udp_port);
    size_t wifi_len = 0;
    size_t host_len = 0;
    
    nvs_get_str(my_handle, "ssid", config.ssid, &wifi_len);
    nvs_get_str(my_handle, "ssid", config.ssid, &wifi_len);

    nvs_get_str(my_handle, "pass", config.pass, &wifi_len);
    nvs_get_str(my_handle, "pass", config.pass, &wifi_len);

    nvs_get_str(my_handle, "host_ip_addr", config.host_ip_addr, &host_len);
    nvs_get_str(my_handle, "host_ip_addr", config.host_ip_addr, &host_len);
}

void print_config() {
    printf("\n");
    printf("--------------------------------------------------\n");
    printf("Status:       %ld\n", config.status);
    printf("id_protocol:  %ld\n", config.id_protocol);
    printf("bmi_samp:     %ld\n", config.bmi_samp);
    printf("acc_sens:     %ld\n", config.acc_sens);
    printf("gyr_sens:     %ld\n", config.gyr_sens);
    printf("disc_time:    %ld\n", config.disc_time);
    printf("tcp_port:     %ld\n", config.tcp_port);
    printf("udp_port:     %ld\n", config.udp_port);
    printf("ssid:         %s\n", config.ssid);
    printf("pass:         %s\n", config.pass);
    printf("host_ip_addr: %s\n", config.host_ip_addr);
    printf("--------------------------------------------------\n");
}

void app_main(void) {
    // Initialize NVS
    esp_err_t ret;
    ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    if (BOOT) {
        set_status(0);
        return;
    }

    get_config();
    print_config();

    protocol = config.id_protocol;

    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ret = esp_bt_controller_init(&bt_cfg);
    if (ret) {
        ESP_LOGE(GATTS_TAG, "%s initialize controller failed: %s", __func__, esp_err_to_name(ret));
        return;
    }

    ret = esp_bt_controller_enable(ESP_BT_MODE_BLE);
    if (ret) {
        ESP_LOGE(GATTS_TAG, "%s enable controller failed: %s", __func__, esp_err_to_name(ret));
        return;
    }

    ret = esp_bluedroid_init();
    if (ret) {
        ESP_LOGE(GATTS_TAG, "%s init bluetooth failed: %s", __func__, esp_err_to_name(ret));
        return;
    }
    ret = esp_bluedroid_enable();
    if (ret) {
        ESP_LOGE(GATTS_TAG, "%s enable bluetooth failed: %s", __func__, esp_err_to_name(ret));
        return;
    }

    ret = esp_ble_gatts_register_callback(gatts_event_handler);
    if (ret) {
        ESP_LOGE(GATTS_TAG, "gatts register error, error code = %x", ret);
        return;
    }
    ret = esp_ble_gap_register_callback(gap_event_handler);
    if (ret) {
        ESP_LOGE(GATTS_TAG, "gap register error, error code = %x", ret);
        return;
    }
    ret = esp_ble_gatts_app_register(PROFILE_APP_ID);
    if (ret) {
        ESP_LOGE(GATTS_TAG, "gatts app register error, error code = %x", ret);
        return;
    }

    esp_err_t local_mtu_ret = esp_ble_gatt_set_local_mtu(500);
    if (local_mtu_ret) {
        ESP_LOGE(GATTS_TAG, "set local  MTU failed, error code = %x", local_mtu_ret);
    }
}
