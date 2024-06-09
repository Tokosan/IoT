import datetime
from struct import unpack
from input_collector import get_last_config

def print_packet(packet: dict) -> None:
    config = get_last_config()
    protocol = int(config["id_protocol"])
    # print(f"ID dispositivo:  {packet['id_device']}")
    # print(f"MAC address:     {packet['mac']}")
    # print(f"TL:              {packet['transport_layer']}")
    # print(f"Protocolo:       {packet['protocol']}")
    # print(f"Packet length:   {packet['packet_length']}")
    print(f"Bateria:         {packet['batt_level']}")
    if protocol > 0:
        print(f"Timestamp:       {packet['timestamp']}")
    if protocol > 1:
        print(f"Temperatura:     {packet['temp']}")
        print(f"Humedad:         {packet['hum']}")
        print(f"Presion:         {packet['press']}")
        print(f"CO:              {packet['co']}")
    if protocol == 3:
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

# LA CONEXION BLE NO TIENE HEADERS

# def parse_header(packet: bytes) -> dict:
#     id_device = unpack('H', packet[0:2])[0]
#     id_device = hex(id_device)[2:].zfill(4)
#
#     mac_string = packet[2:8].hex()
#     mac = ':'.join(a + b for a, b in zip(mac_string[::2], mac_string[1::2]))
#
#     # id_device = str(get_device_id(mac))
#     transport_layer = unpack('B', packet[8:9])[0]
#     protocol = unpack('B', packet[9:10])[0]
#
#     packet_length = unpack('H', packet[10:12])[0]
#
#     header = {
#         "id_device": id_device,
#         "mac": mac,
#         "transport_layer": transport_layer,
#         "protocol": protocol,
#         "packet_length": packet_length
#     }
#     return header


# 1 2 3 4 5
def parse_battery(data: bytes) -> int:
    battery_level = unpack('B', data[0:1])[0]
    return battery_level


# 1 2 3 4 5
def parse_timestamp(data: bytes) -> datetime.datetime:
    timestamp = unpack('i', data[1:5])[0]
    return timestamp


# 2 3 4 5
def parse_thpc(data: bytes) -> dict:
    temperature = unpack('B', data[5:6])[0]
    pressure = unpack('i', data[6:10])[0]
    humidity = unpack('B', data[10:11])[0]
    co = unpack('f', data[11:15])[0]

    thpc = {
        "temp": temperature,
        "hum": humidity,
        "press": pressure,
        "co": co
    }
    return thpc


# TODO: Verificar el rms para el protocolo 3
# 3
def parse_rms(data: bytes) -> dict:
    rms = unpack('f', data[15:19])

    rms = {
        "rms": rms[0]
    }

    return rms


# 4
def parse_imu(data: bytes) -> dict:
    imu = unpack('6f', data[19:43])

    imu = {
        "amp_x": imu[0],
        "freq_x": imu[1],
        "amp_y": imu[2],
        "freq_y": imu[3],
        "amp_z": imu[4],
        "freq_z": imu[5]
    }

    return imu


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
def parse_kpi(packet: dict, data: bytes, i: int) -> dict:
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

    # Parse the header data
    # packet.update(parse_header(data))

    config = get_last_config()
    protocol = int(config["id_protocol"])

    # Get battery level (protocol 1, 2, 3, 4, 5)
    packet["batt_level"] = parse_battery(data)

    # Get Timestamp
    if protocol > 0:
        packet["timestamp"] = parse_timestamp(data)

    # Get THPC data
    if protocol > 1:
        packet.update(parse_thpc(data))

    # Get RMS data
    if protocol == 3:
        packet.update(parse_rms(data))

    # Get IMU data
    if protocol == 4:
        packet.update(parse_imu(data))

    return packet
