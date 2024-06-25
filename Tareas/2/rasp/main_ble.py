import asyncio
from parser import parse_packet, encode_config
from struct import unpack
from bleak import BleakClient, BleakScanner
ADDRESS = "C0:49:EF:08:D3:AE"
CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"

async def connect(device_mac):
    # Con esto nos conectamos a un dispositivo
    client = BleakClient(device_mac)
    print("Client:   ", client)
    i = 0
    while True:
        i+=1
        try:
            connected = await client.connect()
            break
        except:
            continue
    print(f"Connected (after {i} tries)")
    return client, connected

# print("Running discover()")
# asyncio.run(discover())

# print(f"Running connect({ADDRESS})")


# print(client)


async def main():
    client = BleakClient(ADDRESS)
    print("Trying to connect:   ", client)
    i = 0
    while True:
        i+=1
        try:
            connected = await client.connect()
            break
        except:
            continue
    print(f"Connected (after {i} tries)")
    # async with client:
    print("Here we are at the async with, with client", client)

    print("Escribiendo...")
    config = encode_config()
    print(config)
    await client.write_gatt_char(CHARACTERISTIC_UUID, config)
    print("Listo!")
    
    data = await client.read_gatt_char(CHARACTERISTIC_UUID)
    print("Characterisic A:", data)
    print("Received len:", len(data))
    packet = parse_packet(data)
    print(packet)
    

asyncio.run(main())

quit()

def convert_to_128bit_uuid(short_uuid):
    # Usada para convertir un UUID de 16 bits a 128 bits
    # Los bits fijos son utilizados para BLE ya que todos los UUID de BLE son de 128 bits
    # y tiene este formato: 0000XXXX-0000-1000-8000-00805F9B34FB
    base_uuid = "0000ff01-0000-1000-8000-00805F9B34FB"
    short_uuid_hex = "{:04X}".format(short_uuid)
    return base_uuid[:4] + short_uuid_hex + base_uuid[8:]


# CHARACTERISTIC_UUID = convert_to_128bit_uuid(0xFF01) # Busquen este valor en el codigo de ejemplo de esp-idf

async def main(ADDRESS):
    async with BleakClient(ADDRESS) as client:
        data = await client.read_gatt_char(CHARACTERISTIC_UUID)
        print("Characterisic A {0}".format("".join(map(chr, data))))
        # Luego podemos escribir en la caracteristica
        data = 'Hello World!'.encode()
        await client.write_gatt_char(CHARACTERISTIC_UUID, b"\x01\x00")
