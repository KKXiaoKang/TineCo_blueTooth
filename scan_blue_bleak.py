import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Device {device.name}: {device.address}")

asyncio.run(scan_ble_devices())
