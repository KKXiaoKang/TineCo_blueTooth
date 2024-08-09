import asyncio
import json
import struct
from bleak import BleakClient

async def get_characteristics_uuids(address):
    async with BleakClient(address) as client:
        print(f"Connected to {address}")
        for service in client.services:
            print(f"Service UUID: {service.uuid}")
            for characteristic in service.characteristics:
                print(f"  Characteristic UUID: {characteristic.uuid}")

# address = "00:00:00:00:05:F5"
address = "18:00:00:D8:F6:7F"

asyncio.run(get_characteristics_uuids(address))

# 定义UUIDs
SERVICE_UUID = '0000e0ff-3c17-d293-8e48-14fe2e4da212'  # 替换为你的服务UUID
WRITE_CHARACTERISTIC_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'  # 替换为你的特征UUID
NOTICE_CHARACTERISTIC_UUID = '0000ffe2-0000-1000-8000-00805f9b34fb'
READ_CHARACTERISTIC_UUID='0000ffe3-0000-1000-8000-00805f9b34fb'

def calculate_checksum(data):
    return sum(data) & 0xFF

async def send_data(client, data):
    '''
    本地发送数据到料理机
    '''
    # 将数据转换为JSON字符串
    json_str = json.dumps(data)
    # 将JSON字符串转换为字节
    json_bytes = json_str.encode('utf-8')
    print(json_bytes)

    # 构造协议数据
    payload = bytearray([0xF1, 0xCC, 0x00])
    # payload.extend(len(json_str).to_bytes(2, 'little'))
    payload.extend(struct.pack('>H', len(json_bytes)))
    payload.extend(json_bytes)
    payload.append(calculate_checksum(payload))

    # 发送数据
    await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, payload, response=False)
    print(f"发送数据给料理机: {payload}")

async def receive_data(client):
    '''
    接受从料理机发送来的消息
    '''
    # 接收数据
    data = await client.read_gatt_char(READ_CHARACTERISTIC_UUID)

    print(f"Recieve data: {data}")


# 回调函数，当特性发生变化时会调用这个函数
def callback(characteristic_uuid, data):
    print(f"Received data: {data}")


"""
    Device T_KA210802A4672: 18:00:00:D8:F6:7F   # 添可
    Device 3F-C4-3F-80-D6-CF: 3F:C4:3F:80:D6:CF
    Device Nordic_Blinky: E9:07:C2:98:66:DF
    Device ZKTeco: 5C:C3:36:81:AC:6B
    Device L3250 Series: A6:D7:3C:4B:A6:5A
    Device 37-F5-30-43-DC-67: 37:F5:30:43:DC:67
    Device 33-35-86-FD-43-B1: 33:35:86:FD:43:B1
    Device 4D-41-2B-EA-EC-4D: 4D:41:2B:EA:EC:4D
    Device 7F-36-B3-5A-AE-6A: 7F:36:B3:5A:AE:6A
    Device 7D-90-32-BE-AD-47: 7D:90:32:BE:AD:47
    Device 35-43-F9-D6-75-8D: 35:43:F9:D6:75:8D
    Device 48-E9-E0-52-15-31: 48:E9:E0:52:15:31
    Device 67-5C-A7-CA-06-5F: 67:5C:A7:CA:06:5F
    Device 0E-7C-6B-06-16-69: 0E:7C:6B:06:16:69
    Device 71-9A-7D-B5-72-DF: 71:9A:7D:B5:72:DF
    Device 63-9D-5D-B6-3F-AA: 63:9D:5D:B6:3F:AA
    Device 17-E8-1A-5B-AC-52: 17:E8:1A:5B:AC:52
    Device HONOR Band 5-9D5: F0:C4:2F:49:E9:D5
    Device Pencil: CC:A2:00:00:39:19
    Device 4C-21-F9-67-E4-6F: 4C:21:F9:67:E4:6F
    Device 00-39-02-DF-2E-D1: 00:39:02:DF:2E:D1
    Device 23-58-70-1B-E7-F1: 23:58:70:1B:E7:F1
    Device F7-A2-75-F5-EB-0D: F7:A2:75:F5:EB:0D
    Device 29-0B-36-A0-C8-C0: 29:0B:36:A0:C8:C0
    Device 69-D2-12-93-03-49: 69:D2:12:93:03:49
    Device D6-E6-53-ED-09-DC: D6:E6:53:ED:09:DC
    Device ED-1E-42-A4-96-EA: ED:1E:42:A4:96:EA
    Device 5C-41-13-26-18-AE: 5C:41:13:26:18:AE
    Device D3-45-CE-FD-B5-55: D3:45:CE:FD:B5:55
    Device 4D-D8-F7-B0-84-9B: 4D:D8:F7:B0:84:9B
    Device 客厅的小米电视: 68:39:43:6C:A1:35
    Device 5E-06-0F-F0-DE-11: 5E:06:0F:F0:DE:11
    Device 5F-79-B3-35-58-96: 5F:79:B3:35:58:96
    Device 75-BD-92-3A-A1-97: 75:BD:92:3A:A1:97
    Device D7-52-29-C7-02-84: D7:52:29:C7:02:84
"""
async def main():
    # 连接到BLE设备
    # 料理机的蓝牙地址
    # device_address = '00:00:00:00:05:F5'  # 替换为你的设备地址
    device_address = '18:00:00:D8:F6:7F'
    client = BleakClient(device_address)
    await client.connect()

    await client.start_notify(NOTICE_CHARACTERISTIC_UUID, callback)

    try:
        # 发送烹饪指令到食万
        input_data = {"actionType":"startCook", "menuId":"20230904130922_60dff78391b6fa08e386d84b958f2d14"}
        finsh_data = {"actionType":"addFoodComplete"}

        await send_data(client, input_data)  # 西兰花炒虾仁
        print(" --- success to send_data --- ")
        # 从食万接收数据
        # while (True):
        received_data = await receive_data(client)
        print("received_data : ", received_data)
    except Exception as e:
        await client.disconnect()
        print(e)
    finally:
        # 断开连接
        await client.disconnect()
        # 结束连接
        print(" end to connect ")

# 运行主函数
asyncio.run(main())
