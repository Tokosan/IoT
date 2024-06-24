from struct import unpack, pack
from db import get_config

def print_packet(packet: dict) -> None:
    protocol = packet['protocol']
    print(f"Bateria:         {packet['batt_level']}")
    print(f"Timestamp:       {packet['timestamp']}")
    if protocol >= 2:
        print(f"Temperatura:     {packet['temp']}")
        print(f"Humedad:         {packet['hum']}")
        print(f"Presion:         {packet['press']}")
        print(f"CO:              {packet['co']}")
    if protocol == 3 or protocol == 4:
        print(f"RMS:             {packet['rms']}")
    if protocol == 4:
        print(f"RMS:             {packet['rms']}")
        print(f"Amplitud X:      {packet['amp_x']}")
        print(f"Frequencia X:    {packet['freq_x']}")
        print(f"Amplitud Y:      {packet['amp_y']}")
        print(f"Frequencia Y:    {packet['freq_y']}")
        print(f"Amplitud Z:      {packet['amp_z']}")
        print(f"Frequencia Z:    {packet['freq_z']}")
    if protocol == 5:
        print(f"Acc X:           [{packet['acc_x'][0]}, {packet['acc_x'][1]} ... ]")
        print(f"Acc Y:           [{packet['acc_y'][0]}, {packet['acc_y'][1]} ... ]")
        print(f"Acc Z:           [{packet['acc_z'][0]}, {packet['acc_z'][1]} ... ]")
        print(f"Rotational X:    [{packet['r_gyr_x'][0]}, {packet['r_gyr_x'][1]} ... ]")
        print(f"Rotational Y:    [{packet['r_gyr_y'][0]}, {packet['r_gyr_y'][1]} ... ]")
        print(f"Rotational Z:    [{packet['r_gyr_z'][0]}, {packet['r_gyr_z'][1]} ... ]")
    print("\n")

# 1 2 3 4 5
def parse_battery(data: bytes) -> int:
    battery_level = unpack('B', data[0:1])[0]
    ret = {
        "batt_level": battery_level
    }
    return ret

# 1 2 3 4 5
def parse_timestamp(data: bytes):
    timestamp = unpack('i', data[1:5])[0]
    ret = {
        "timestamp": timestamp
    }
    return ret

# 2 3 4 5
def parse_thpc(data: bytes) -> dict:
    temperature = unpack('B', data[5:6])[0]
    humidity    = unpack('B', data[6:7])[0]
    pressure    = unpack('i', data[7:11])[0]
    co          = unpack('i', data[11:15])[0]
    ret = {
        "temp":  temperature,
        "hum":   humidity,
        "press": pressure,
        "co":    co
    }
    return ret

# 1
def parse_rms(data: bytes) -> dict:
    rms = unpack('f', data[15:19])[0]
    ret = {
        "rms": rms
    }
    return ret

# 4
def parse_imu(data: bytes) -> dict:
    imu = unpack('6f', data[19:43])
    ret = {
        "amp_x":  imu[0],
        "freq_x": imu[1],
        "amp_y":  imu[2],
        "freq_y": imu[3],
        "amp_z":  imu[4],
        "freq_z": imu[5]
    }
    return ret


def prepare_kpi():
    return {
        "acc_x": [None] * 2000,
        "acc_y": [None] * 2000,
        "acc_z": [None] * 2000,
        "r_gyr_x": [None] * 2000,
        "r_gyr_y": [None] * 2000,
        "r_gyr_z": [None] * 2000
    }

# 5
def old_parse_kpi(packet: dict, data: bytes, i: int) -> dict:
    keys = ["acc_x", "acc_y", "acc_z", "r_gyr_x", "r_gyr_y", "r_gyr_z"]
    try:
        array = unpack('250f', data[12:1012])
    except:
        array = [-10000000] * 250
    target = packet[keys[i // 8]]
    for j in range(250):
        target[(i % 8) * 250 + j] = array[j]
    packet[keys[i // 8]] = target
    return packet


def parse_packet(data: bytes) -> None:
    packet = {}
    
    protocol = packet['protocol'] = unpack('B', data[0:1])[0]
    data = data[1:]
    
    # Get battery level (protocol 1, 2, 3, 4, 5)
    packet.update(parse_battery(data))
    packet.update(parse_timestamp(data))
    
    # Get THPC data
    if protocol >= 2:
        packet.update(parse_thpc(data))

    # Get RMS data
    if protocol == 3 or protocol == 4:
        packet.update(parse_rms(data))

    # Get IMU data
    if protocol == 4:
        packet.update(parse_imu(data))
    
    return packet

def encode_config():
    config = get_config()
    data = pack(
        f'2B 7i {len(config["ssid"])+1}s {len(config["pass"])+1}s {len(config["host_ip_addr"])+1}s',
        int(config["status"]),
        int(config["id_protocol"]),
        int(config["acc_sampling"]),
        int(config["acc_sensibility"]),
        int(config["gyro_sensibility"]),
        int(config["bme668_sampling"]),
        int(config["discontinuos_time"]),
        int(config["tcp_port"]),
        int(config["udp_port"]),
        (config["ssid"] + '\0').encode(),
        (config["pass"] + '\0').encode(),
        (config["host_ip_addr"] + '\0').encode()
    )
    return data

def bytes_hex(data):
    data_string = data.hex()
    return ' '.join(a + b for a,b in zip(data_string[::2], data_string[1::2]))

if __name__ == "__main__":
    config = get_config()
    data = encode_config(config)
    # imprimimos el paquete en hexadecimal
    print("Paquete: ", bytes_hex(data))