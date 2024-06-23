#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_sleep.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "lwip/err.h"
#include "lwip/sockets.h"  // Para sockets
#include "lwip/sys.h"
#include "nvs_flash.h"

// Credenciales de WiFi

#define WIFI_SSID "iot-wifi"
#define WIFI_PASSWORD "iotdcc123"

#define SERVER_IP "10.20.1.1"  // IP del servidor (su computador o raspberry)
int SERVER_PORT = 1235;
int SERVER_COMM_PORT = 12350;

typedef uint8_t byte1_t;
typedef uint16_t byte2_t;
typedef uint32_t byte4_t;

// Tamano de los paquetes segun el protocolo
#define PACKET_SIZE_BASE 12
#define PACKET_SIZE_P0 12 + 1
#define PACKET_SIZE_P1 12 + 1 + 4
#define PACKET_SIZE_P2 12 + 1 + 4 + 10
#define PACKET_SIZE_P3 12 + 1 + 4 + 10 + 7 * 4
#define PACKET_SIZE_P4_S 12 + 1 + 4 + 10  // primer envio de datos
#define PACKET_SIZE_P4_L 12 + 1000        // 48 paquetes siguientes

// Tiempos
#define TIME_BETWEEN_PACKETS 100  // usado para el protocolo 4
#define TIME_BETWEEN_SEND 1000    // usado para UDP

// Variables de WiFi
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT BIT1
static const char *TAG = "WIFI";
static int s_retry_num = 0;
static EventGroupHandle_t s_wifi_event_group;

// Variables globales de la comunicacion
int comm_socket;
int main_socket;
char protocol;
char TL;
byte1_t MAC[6];
byte1_t *header;
struct sockaddr_in server_comm_addr;

void print_packet(char *packet) {
    printf("Header: ");
    // Imprimir header
    // 1. ID Mensaje
    printf("ID Mensaje:   %02X%02X\n", packet[0], packet[1]);
    // 2. MAC
    printf("MAC: ");
    for (int i = 2; i < 8; i++)
        printf("%02X", packet[i]);
    printf("\n");
    // 3. TL
    printf("TL:           %d\n", packet[8]);
    // 4. Protocolo
    printf("Protocolo:    %d\n", packet[9]);
    // 5. Longitud
    printf("Longitud:     %d\n", (packet[11] << 8) | packet[10]);

    if (protocol == '4') {
        return;
    }

    // Imprimimos body
    printf("Body: ");
    // 1. Bateria
    printf("Bateria:      %d\n", packet[12]);
    // 2. Timestamp
    if (protocol >= '1')
        printf("Timestamp:    %d\n", (packet[16] << 24) | (packet[15] << 16) | (packet[14] << 8) | packet[13]);
    // 3. THPC
    if (protocol >= '2') {
        printf("Temperatura:  %d\n", packet[17]);
        printf("Humedad:      %d\n", packet[18]);
        printf("Presion:      %d\n", (packet[22] << 24) | (packet[21] << 16) | (packet[20] << 8) | packet[19]);
        printf("CO:           %f\n", *((float *)(packet + 23)));
    }
    // 4. IMU
    if (protocol == '3') {
        printf("RMS:          %f\n", *((float *)(packet + 27)));
        printf("Amplitud X:   %f\n", *((float *)(packet + 31)));
        printf("Frecuencia X: %f\n", *((float *)(packet + 35)));
        printf("Amplitud Y:   %f\n", *((float *)(packet + 39)));
        printf("Frecuencia Y: %f\n", *((float *)(packet + 43)));
        printf("Amplitud Z:   %f\n", *((float *)(packet + 47)));
        printf("Frecuencia Z: %f\n", *((float *)(packet + 51)));
    }
}

char *create_base_packet(int size) {
    char *packet = malloc(size);

    byte1_t len1 = (size >> 8) & 0xFF;
    byte1_t len0 = size & 0xFF;

    memcpy(packet, header, 12);
    memcpy(packet + 10, &len0, 1);
    memcpy(packet + 11, &len1, 1);

    return packet;
}

void set_id(char *packet, byte2_t id_packet) {
    ESP_LOGI("set_id", "Seteando id: %d", id_packet);
    memcpy(packet, (byte1_t *)&id_packet, 2);
}

void create_header() {
    header = malloc(12);
    memcpy(header + 2, MAC, 6);
    byte1_t _TL = TL - '0';
    byte1_t _protocol = protocol - '0';
    memcpy(header + 8, &_TL, 1);
    memcpy(header + 9, &_protocol, 1);
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

int socket_udp(int port) {
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr.s_addr);

    // Crear un socket UDP (SOCK_DGRAM)
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Error al crear el socket");
        return -1;
    }

    int connection_status = connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
    // Conectar al servidor
    if (connection_status != 0) {
        ESP_LOGE(TAG, "Error al conectar por UDP");
        close(sock);
        return -1;
    }

    ESP_LOGI(TAG, "Conexion por socket UDP exitosa!");
    // seteamos el timeout a 5 segundos de salida y 5 segundos de entrada
    struct timeval tv;
    tv.tv_sec = 5;
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&tv, sizeof tv);
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char *)&tv, sizeof tv);

    if (port == SERVER_COMM_PORT) {
        server_comm_addr = server_addr;
        comm_socket = sock;
    }

    return 0;
}

int socket_tcp(int port) {
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr.s_addr);

    // Crear un socket TCP (SOCK_STREAM)
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Error al crear el socket");
        return -1;
    }

    int connection_status = connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
    // Conectar al servidor
    if (connection_status != 0) {
        ESP_LOGE(TAG, "Error al conectar por TCP");
        close(sock);
        return -2;
    }

    ESP_LOGI(TAG, "Conexion por socket TCP exitosa!");

    // seteamos el timeout a 5 segundos de salida y 5 segundos de entrada
    struct timeval tv;
    tv.tv_sec = 5;
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&tv, sizeof tv);
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char *)&tv, sizeof tv);

    if (port == SERVER_COMM_PORT) {
        server_comm_addr = server_addr;
        comm_socket = sock;
    } else {
        main_socket = sock;
    }
    return 0;
}

byte4_t random_int(int min, int max) {
    return rand() % (max - min + 1) + min;
}

float random_float(float min, float max) {
    float base = (float)rand() / RAND_MAX;
    return base * (max - min) + min;
}

// 0 1 2 3 4
void append_battery(char *packet) {
    // generamos un numero aleatorio entre 1 y 100
    byte1_t battery = random_int(1, 100);
    ESP_LOGI("append_battery", "Bateria: %d", battery);
    memcpy(packet + PACKET_SIZE_BASE, (byte1_t *)&battery, 1);
}

// 1 2 3 4
void append_timestamp(char *packet) {
    byte4_t timestamp = time(NULL);
    memcpy(packet + PACKET_SIZE_P0, (byte1_t *)&timestamp, 4);
}

// 2 3 4
void append_thpc(char *packet) {
    byte1_t temp = random_int(5, 30);
    byte1_t hum = random_int(30, 80);
    byte4_t pres = random_int(1000, 1200);
    float co = random_float(30, 200);
    memcpy(packet + PACKET_SIZE_P1, (byte1_t *)&temp, 1);
    memcpy(packet + PACKET_SIZE_P1 + 1, (byte1_t *)&hum, 1);
    memcpy(packet + PACKET_SIZE_P1 + 2, (byte1_t *)&pres, 4);
    memcpy(packet + PACKET_SIZE_P1 + 6, (byte1_t *)&co, 4);
}

// 3
void append_imu(char *packet) {
    float amp_x = random_float(0.0059, 0.12);
    float amp_y = random_float(0.0041, 0.11);
    float amp_z = random_float(0.0080, 0.15);
    float freq_x = random_float(29.0, 31.0);
    float freq_y = random_float(59.0, 61.0);
    float freq_z = random_float(89.0, 91.0);
    float rms = sqrt((amp_x * amp_x + amp_y * amp_y + amp_z * amp_z) / 3);

    memcpy(packet + PACKET_SIZE_P2, (byte1_t *)&rms, 4);
    memcpy(packet + PACKET_SIZE_P2 + 4, (byte1_t *)&amp_x, 4);
    memcpy(packet + PACKET_SIZE_P2 + 8, (byte1_t *)&freq_x, 4);
    memcpy(packet + PACKET_SIZE_P2 + 12, (byte1_t *)&amp_y, 4);
    memcpy(packet + PACKET_SIZE_P2 + 16, (byte1_t *)&freq_y, 4);
    memcpy(packet + PACKET_SIZE_P2 + 20, (byte1_t *)&amp_z, 4);
    memcpy(packet + PACKET_SIZE_P2 + 24, (byte1_t *)&freq_z, 4);
}

void send_packet(char *packet, int size) {
    if (protocol == '0') {
        // TCP
        send(comm_socket, packet, size, 0);
    } else {
        // UDP
        sendto(comm_socket, packet, size, 0, (struct sockaddr *)&server_comm_addr, sizeof(server_comm_addr));
    }
}

// ------ PROTOCOLO 0 ------ //
void protocol0() {
    char *packet;
    byte2_t id_packet = random_int(0, 255) << 8;  // id compartida por distintos paquetes del mismo mensaje
    packet = create_base_packet(PACKET_SIZE_P0);
    set_id(packet, id_packet);
    append_battery(packet);
    send_packet(packet, PACKET_SIZE_P0);
    print_packet(packet);
    free(packet);
}

// ------ PROTOCOLO 1 ------ //
void protocol1() {
    char *packet;
    byte2_t id_packet = random_int(0, 255) << 8;  // id compartida por distintos paquetes del mismo mensaje
    packet = create_base_packet(PACKET_SIZE_P1);
    set_id(packet, id_packet);
    append_battery(packet);
    append_timestamp(packet);
    send_packet(packet, PACKET_SIZE_P1);
    print_packet(packet);
    free(packet);
}

// ------ PROTOCOLO 2 ------- //
// Battery | Timestamp | THPC //
void protocol2() {
    char *packet;
    byte2_t id_packet = random_int(0, 255) << 8;  // id compartida por distintos paquetes del mismo mensaje
    packet = create_base_packet(PACKET_SIZE_P2);
    set_id(packet, id_packet);
    append_battery(packet);
    append_timestamp(packet);
    append_thpc(packet);
    send_packet(packet, PACKET_SIZE_P2);
    print_packet(packet);
    free(packet);
}

// ------ PROTOCOLO 3 ------------- //
// Battery | Timestamp | THPC | IMU //
void protocol3() {
    char *packet;
    byte2_t id_packet = random_int(0, 255) << 8;  // id compartida por distintos paquetes del mismo mensaje
    packet = create_base_packet(PACKET_SIZE_P3);
    set_id(packet, id_packet);
    append_battery(packet);
    append_timestamp(packet);
    append_thpc(packet);
    append_imu(packet);
    send_packet(packet, PACKET_SIZE_P3);
    print_packet(packet);
    free(packet);
}

// ------ PROTOCOLO 4 ------------- //
// Battery | Timestamp | THPC | KPI //
void protocol4() {
    char *packet;
    byte1_t id_main = random_int(0, 255);  // id compartida por distintos paquetes del mismo mensaje
    byte1_t n_packets = 49;                      // cantidad de paquetes de este mensaje
    byte2_t id_packet = (id_main << 8);          // leer README
    packet = create_base_packet(PACKET_SIZE_P4_S);
    set_id(packet, id_packet);
    append_battery(packet);
    append_timestamp(packet);
    append_thpc(packet);
    // Aqui mandamos el primer paquete
    send_packet(packet, PACKET_SIZE_P4_S);
    free(packet);

    // y procedemos a generar los otros 48 paquetes
    // generamos nuestros 6 arreglos de 2000 floats
    float *acc_x = (float *)malloc(2000 * 4);
    float *acc_y = (float *)malloc(2000 * 4);
    float *acc_z = (float *)malloc(2000 * 4);
    float *r_gyr_x = (float *)malloc(2000 * 4);
    float *r_gyr_y = (float *)malloc(2000 * 4);
    float *r_gyr_z = (float *)malloc(2000 * 4);

    for (int i = 0; i < 2000; i++) {
        acc_x[i] = random_float(-16.0, 16.0);
        acc_y[i] = random_float(-16.0, 16.0);
        acc_z[i] = random_float(-16.0, 16.0);
        r_gyr_x[i] = random_float(-1000.0, 1000.0);
        r_gyr_y[i] = random_float(-1000.0, 1000.0);
        r_gyr_z[i] = random_float(-1000.0, 1000.0);
    }

    float *arrays[6] = {acc_x, acc_y, acc_z, r_gyr_x, r_gyr_y, r_gyr_z};

    // mandamos paquetes de a 1000 + 12 bytes (PACKET_SIZE_P4_L)
    for (byte1_t i = 0; i < n_packets - 1; i++) {
        id_packet = (id_main << 8) | (i + 1);
        packet = create_base_packet(PACKET_SIZE_P4_L);
        set_id(packet, id_packet);

        memcpy(packet + 12, arrays[i / 8] + (i % 8) * 250, 1000);
        ESP_LOGI("P4", "Sending packet %d", i);
        send_packet(packet, PACKET_SIZE_P4_L);
        print_packet(packet);
        free(packet);
        vTaskDelay(TIME_BETWEEN_PACKETS / portTICK_PERIOD_MS);
    }

    for (int i = 0; i < 6; i++) {
        free(arrays[i]);
    }
}

// Usamos arreglos para las funciones
typedef void (*func_ptr_prot)();
typedef int (*func_ptr_sock)();
func_ptr_prot func_protocol_array[5] = {protocol0, protocol1, protocol2, protocol3, protocol4};
func_ptr_sock func_socket_array[2] = {socket_tcp, socket_udp};

int check_changes() {
    ESP_LOGI("check_changes", "Revisando si hubo cambios en el protocolo o TL");
    char rx_buffer[128];
    int rx_len = recv(main_socket, rx_buffer, sizeof(rx_buffer) - 1, 0);
    if (rx_len < 0) {
        ESP_LOGE("check_changes", "Error al recibir datos");
        return -1;
    }

    if (rx_len == 0) {
        ESP_LOGI("check_changes", "No se recibieron datos");
        return -1;
    }

    if (rx_len != 2) {
        ESP_LOGI("check_changes", "Se recibio otro mensaje: %s", rx_buffer);
        return -1;
    }

    if (rx_buffer[0] != protocol || rx_buffer[1] != TL) {
        protocol = rx_buffer[0];
        TL = rx_buffer[1];
        ESP_LOGI("check_changes", "Nueva configuracion: protocolo %c, TL %c", protocol, TL);
        return 1;
    }

    return 0;
}

void start_communication() {
    // invocamos a la funcion correspondiente segun protocol y TL
    int res;

    ESP_LOGI("start_communication", "Creando socket de comunicacion...");
    res = func_socket_array[TL - '0'](SERVER_COMM_PORT);
    if (res < 0) {
        return;
    }
    ESP_LOGI("start_communication", "Socket de comunicacion creado!");

    ESP_LOGI("start_communication", "Creando header...");
    create_header();
    ESP_LOGI("start_communication", "Header creado!");

    // dependiendo del TL, reiniciamos o mandamos perpetuamente
    if (TL == '0') {
        ESP_LOGI("start_communication", "TL 0, mandamos una vez y dormimos!");
        func_protocol_array[protocol - '0']();
    } else {
        ESP_LOGI("start_communication", "TL 1, mandamos perpetuamente!");
        while (TL == '1') {
            func_protocol_array[protocol - '0']();
            vTaskDelay(1000 / portTICK_PERIOD_MS);
            // revisamos si hubo algun cambio en el protocolo o TL
            res = check_changes();
            if (res < 0) {
                // hubo un error :c
                break;
            }
            if (res == 0) {
                // no hubo cambios
                continue;
            }
            if (res > 0) {
                // si hubo un cambio!
                free(header);
                create_header();
                continue;
            }
        }
    }
}

void clean() {
    close(main_socket);
    close(comm_socket);
    free(header);
}

int get_ids() {
    ESP_LOGI("get_ids", "Solicitando protocolo y capa de transporte");
    char *buff = malloc(strlen("get_ids") + 4);
    char *getter = "get_ids";
    memcpy(buff, getter, strlen(getter));
    byte4_t t = time(NULL);
    memcpy(buff + strlen(getter), (byte1_t *)&t, 4);
    send(main_socket, buff, 11, 0);
    free(buff);

    // esperamos la respuesta para decidir que hacer
    char rx_buffer[128];
    int max_try = 2;
    while (max_try--) {
        int rx_len = recv(main_socket, rx_buffer, sizeof(rx_buffer) - 1, 0);
        printf("rx_len: %d\n", rx_len);
        if (rx_len < 0) {
            ESP_LOGE(TAG, "Error al recibir datos");
            max_try--;
        } else {
            break;
        }
    }

    if (max_try == 0)
        return -2;

    protocol = rx_buffer[0];
    TL = rx_buffer[1];
    ESP_LOGI("get_ids", "Protocolo: %c, TL: %c", protocol, TL);
    return 0;
}

void app_main(void) {
    srand(time(NULL));
    int res;
    nvs_init();
    wifi_init_sta(WIFI_SSID, WIFI_PASSWORD);
    ESP_LOGI(TAG, "Conectado a WiFi!\n");

    // obtenemos e imprimimos la mac adress de la ESP32
    esp_read_mac(MAC, ESP_MAC_WIFI_STA);

    // creamos el main_socket
    res = socket_tcp(SERVER_PORT);
    if (res < 0) {
        esp_deep_sleep(10);
    }

    // solicitamos el protocolo y la capa de transporte
    res = get_ids();
    if (res < 0) {
        ESP_LOGE("main", "Error al obtener protocolo y TL");
        esp_deep_sleep(10);
    }

    // comenzamos la comunicacion
    start_communication();
    clean();  // se cierran los sockets y se libera memoria
    ESP_LOGI("main", "Fin del programa, durmiendo 1 segundo...");
    esp_deep_sleep(1 * 1000000);
}
