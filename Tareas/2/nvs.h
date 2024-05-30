/* 
 * Copyright (C) 2019 Center for Industry 4.0
 * All Rights Reserved
 *
 * Center_for_Industry_4.0_LICENSE_PLACEHOLDER
 * Desarrolladores: Enrique Germani, Luciano Radrigan
 */

#define SYSTEM_STATUS 1
#define SAMP_FREQ 2
#define TIME_SEG 3
#define ACC_SEN 4
#define GYR_SEN 5
#define ACC_ANY 6
#define RF_CAL 7
#define SEL_ID 8

int Write_NVS(int32_t data, int key);
int Read_NVS(int32_t* data,int key);