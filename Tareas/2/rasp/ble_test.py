import asyncio
from bleak import BleakClient, BleakScanner
from parser import parse_packet

CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"
ADDRESS = "C0:49:EF:08:D3:AE"

async def get_client():
    client = BleakClient(ADDRESS)
    print("Trying to connect:", client)
    i = 0
    while True:
        try:
            connected = await client.connect()
            break
        except:
            i+=1
    print(f"Connected (after {i} tries)")
    data = await client.read_gatt_char(CHARACTERISTIC_UUID)
    print(parse_packet(data))
    return client

client = asyncio.run(get_client())

# async def get_data(client):
    
# print("now getting data")

# asyncio.run(get_data(client))