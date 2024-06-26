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
