from packet_parser_BLE import parse_packet
from db import get_config


# Esta función es asincrona, va a enviar la configuración y
# recibir paquetes desde el dispositivo BLE.
async def start_communication(client, CHARACTERISTIC_UUID):
    print("***********************************************")
    print("Iniciando comunicacion")
    config = get_config()
    id_protocol = config["id_protocol"]
    status = config["status"]
    print(f"ID_protocol: {id_protocol}, Status: {status}")

    # Convertimos la configuracion a bytes
    config_bytes = str(config).encode('utf-8')

    # Enviar la configuracion al dispositivo BLE
    await client.write_gatt_char(CHARACTERISTIC_UUID, config_bytes)

    # Recibir paquetes del dispositivo BLE
    while True:
        data = await client.read_gatt_char(CHARACTERISTIC_UUID)
        parse_packet(data)
