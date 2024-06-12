from packet_parser_BLE import parse_packet
import conexion_SQL as sql


# Esta función es asincrona, va a enviar la configuración y
# recibir paquetes desde el dispositivo BLE.
async def start_communication(client, CHARACTERISTIC_UUID):
    print("***********************************************")
    print("Iniciando comunicación")
    config = sql.get_last_config()
    id_protocol = config["id_protocol"]
    status = config["status"]
    print(f"ID_protocol: {id_protocol}, Status: {status}")

    # Convertimos la configuración a bytes
    config_bytes = str(config).encode('utf-8')

    # Enviar la configuración al dispositivo BLE
    await client.write_gatt_char(CHARACTERISTIC_UUID, config_bytes)

    # Recibir paquetes del dispositivo BLE
    while True:
        data = await client.read_gatt_char(CHARACTERISTIC_UUID)
        parse_packet(data)
