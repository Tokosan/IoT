#ifndef Paramet
#define Paramet

    typedef struct Config
    {
        int8_t status;
        int8_t ID_Protocol;
        int32_t BMI270_Sampling;
        int32_t BMI270_Acc_Sensibility; 
        int32_t BMI270_Gyro_Sensibility; 
        int32_t BME688_Sampling;
        int32_t Discontinuous_Time;
        int32_t Port_TCP;
        int32_t Port_UDP;
        int32_t Host_Ip_Addr;
        char Ssid[10];
        char Pass[10];
    } Config;

#endif

#ifndef Sensor_Data
#define Sensor_Data
    typedef struct Sensor_Data
    {
        int8_t Batt_level;
        int8_t Timestamp[4];
        int8_t Temp;
        int8_t Press[4];
        int8_t Hum;
        int8_t Co[4];
        int8_t RMS[4];
        int8_t Amp_x_bmi[4];
        int8_t Frec_x_bmi[4];
        int8_t Amp_y_bmi[4];
        int8_t Frec_y_bmi[4];
        int8_t Amp_z_bmi[4];
        int8_t Frec_z_bmi[4];

        int16_t BMI270_Acc_x[2000]; 
        int16_t BMI270_Acc_y[2000];
        int16_t BMI270_Acc_z[2000];
        int16_t BMI270_Gir_x[2000];
        int16_t BMI270_Gir_y[2000];
        int16_t BMI270_Gir_z[2000];
    }Sensor_Data;
#endif
