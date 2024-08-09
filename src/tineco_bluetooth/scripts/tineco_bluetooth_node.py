#!/usr/bin/env python
import rospy
from tineco_bluetooth.srv import send_tineco_data, send_tineco_dataResponse
import asyncio
import json
import struct
from bleak import BleakClient

import yaml
import rospkg
import os

# 加载配置文件
rospack = rospkg.RosPack()
config_path = os.path.join(rospack.get_path('tineco_bluetooth'), 'config/instructions.yaml')
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)
print("config : ", config)

SERVICE_UUID = '0000e0ff-3c17-d293-8e48-14fe2e4da212'
WRITE_CHARACTERISTIC_UUID = '0000ffe1-0000-1000-8000-00805f9b34fb'
NOTICE_CHARACTERISTIC_UUID = '0000ffe2-0000-1000-8000-00805f9b34fb'
READ_CHARACTERISTIC_UUID = '0000ffe3-0000-1000-8000-00805f9b34fb'
device_address = '18:00:00:D8:F6:7F'

client = None

def calculate_checksum(data):
    return sum(data) & 0xFF

async def send_data(client, data):
    json_str = json.dumps(data)
    json_bytes = json_str.encode('utf-8')
    payload = bytearray([0xF1, 0xCC, 0x00])
    payload.extend(struct.pack('>H', len(json_bytes)))
    payload.extend(json_bytes)
    payload.append(calculate_checksum(payload))
    await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, payload, response=False)
    rospy.loginfo(f"Sent data: {payload}")

def callback(sender, data):
    rospy.loginfo(f"Received data: {data}")

async def connect_to_device():
    global client
    try:
        client = BleakClient(device_address)
        await client.connect()
        await client.start_notify(NOTICE_CHARACTERISTIC_UUID, callback)
        rospy.loginfo("Connected to Tineco device and started notifications.")
    except Exception as e:
        rospy.logerr(f"Failed to connect to device: {e}")

async def disconnect_from_device():
    global client
    try:
        if client and client.is_connected:
            await client.stop_notify(NOTICE_CHARACTERISTIC_UUID)
            await client.disconnect()
            rospy.loginfo("Disconnected from Tineco device.")
    except Exception as e:
        rospy.logerr(f"Failed to disconnect from device: {e}")

async def handle_action(actionType):
    try:
        if not client or not client.is_connected:
            await connect_to_device()

        input_data = {}

        # 遍历 config 查找匹配的 key_value
        for key, value in config.items():
            if value['key_value'] == actionType:
                if value['actionType'] == 'addFoodComplete':
                    # 直接设置 actionType
                    input_data = {"actionType": value['actionType']}
                else:
                    # 设置 actionType 和 menuId
                    input_data = {"actionType": value['actionType'], "menuId": value.get('menuId')}
                break  # 找到匹配的条目后退出循环

        # 对于 'add_food_complete'，直接设置 actionType
        if actionType == 'add_food_complete':
            input_data = {"actionType": "addFoodComplete"}
        
        # input_data
        print(" input_data : ", input_data)
        await send_data(client, input_data)

        # 保持一段时间以接收可能的响应数据
        await asyncio.sleep(5)

        return True
    except Exception as e:
        rospy.logerr(f"Failed to handle action: {e}")
        return False

def handle_send_data(req):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(handle_action(req.actionType))
    loop.close()
    return send_tineco_dataResponse(result)

def tineco_bluetooth_server():
    rospy.init_node('tineco_bluetooth_server')
    s = rospy.Service('/tineco_bluetooth_send_data', send_tineco_data, handle_send_data)
    rospy.loginfo("Ready to send data to Tineco device.")
    
    try:
        rospy.spin()
    finally:
        # 确保节点关闭时断开设备连接
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(disconnect_from_device())
        loop.close()

if __name__ == "__main__":
    tineco_bluetooth_server()
