import asyncio
from bleak import BleakClient, BleakScanner

CHARACTERISTIC_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"

async def scan():
    # Con esto podemos ver los dispositivos que estan disponibles
    scanner = BleakScanner()
    devices = await scanner.discover()
    print("Devices:")
    # c0:49:ef:08:d3:ae 
    print(devices)
    print("+-------MAC-------+--------------------------+")
    esps = []
    for device in devices:
        if "ESP" in device.name:
            esps.append(device.address)
    return esps

esps = asyncio.run(scan())
print("ESPS:", esps)