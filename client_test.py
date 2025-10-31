#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP Socket客户端测试程序
用于测试报警器和灯光控制功能
"""

import socket
import json
import xml.etree.ElementTree as ET
import struct
import time
import logging
from datetime import datetime
from typing import Dict, Any
from config import COMMAND_CODES, DATA_FORMATS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProtocolClient:
    """协议客户端"""
    
    # 协议头部常量
    SYNC_BYTES = [0xeb, 0x91, 0xeb, 0x90]
    HEADER_LENGTH = 16
    
    def __init__(self):
        self.message_id = 0
    
    def build_header(self, asdu_length: int, asdu_format: int = 0x01) -> bytes:
        """构建协议头部"""
        header = bytearray(self.HEADER_LENGTH)
        
        # 同步字符
        for i, sync_byte in enumerate(self.SYNC_BYTES):
            header[i] = sync_byte
        
        # ASDU长度 (小端字节序)
        header[4:6] = struct.pack('<H', asdu_length)
        
        # 报文ID (小端字节序)
        header[6:8] = struct.pack('<H', self.message_id)
        
        # ASDU格式
        header[8] = asdu_format
        
        # 预留字节
        header[9:16] = b'\x00' * 7
        
        self.message_id = (self.message_id + 1) % 65536
        return bytes(header)
    
    def parse_header(self, header: bytes) -> Dict[str, Any]:
        """解析协议头部"""
        if len(header) != self.HEADER_LENGTH:
            raise ValueError(f"协议头部长度错误: {len(header)} != {self.HEADER_LENGTH}")
        
        # 检查同步字符
        sync_bytes = list(header[:4])
        if sync_bytes != self.SYNC_BYTES:
            raise ValueError(f"同步字符错误: {sync_bytes}")
        
        # 解析长度和报文ID
        asdu_length = struct.unpack('<H', header[4:6])[0]
        message_id = struct.unpack('<H', header[6:8])[0]
        asdu_format = header[8]
        
        return {
            'asdu_length': asdu_length,
            'message_id': message_id,
            'asdu_format': asdu_format
        }
    
    def parse_response(self, response_data: bytes) -> Dict[str, Any]:
        """解析响应数据"""
        # 解析头部
        header_info = self.parse_header(response_data[:self.HEADER_LENGTH])
        
        # 解析ASDU
        asdu_data = response_data[self.HEADER_LENGTH:]
        if header_info['asdu_format'] == DATA_FORMATS['JSON']:  # JSON格式
            return json.loads(asdu_data.decode('utf-8'))
        elif header_info['asdu_format'] == DATA_FORMATS['XML']:  # XML格式
            return self._parse_xml_response(asdu_data)
        else:
            raise ValueError(f"不支持的格式类型: {header_info['asdu_format']}")
    
    def build_request(self, msg_type: int, command: int, items: Dict[str, Any] = None, format_type: int = DATA_FORMATS['JSON']) -> bytes:
        """构建请求数据"""
        if items is None:
            items = {}
        
        request_data = {
            "Type": msg_type,
            "Command": command,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Items": items
        }
        
        if format_type == DATA_FORMATS['JSON']:  # JSON格式
            asdu_data = json.dumps(request_data, ensure_ascii=False).encode('utf-8')
        elif format_type == DATA_FORMATS['XML']:  # XML格式
            asdu_data = self._build_xml_request(request_data)
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")
        
        header = self.build_header(len(asdu_data), format_type)
        return header + asdu_data
    
    def _build_xml_request(self, data: Dict[str, Any]) -> bytes:
        """构建XML请求数据"""
        root = ET.Element('PatrolDevice')
        
        # 添加基本字段
        type_elem = ET.SubElement(root, 'Type')
        type_elem.text = str(data['Type'])
        
        command_elem = ET.SubElement(root, 'Command')
        command_elem.text = str(data['Command'])
        
        time_elem = ET.SubElement(root, 'Time')
        time_elem.text = data['Time']
        
        # 添加Items
        items_elem = ET.SubElement(root, 'Items')
        for key, value in data['Items'].items():
            item_elem = ET.SubElement(items_elem, key)
            item_elem.text = str(value)
        
        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_str
    
    def _parse_xml_response(self, asdu_data: bytes) -> Dict[str, Any]:
        """解析XML响应数据"""
        try:
            data_str = asdu_data.decode('utf-8')
            root = ET.fromstring(data_str)
            
            result = {}
            for child in root:
                if child.tag == 'Items' and len(child) > 0:
                    # 解析Items子元素
                    items = {}
                    for item in child:
                        items[item.tag] = item.text
                    result[child.tag] = items
                else:
                    result[child.tag] = child.text
            
            return result
        except Exception as e:
            logger.error(f"XML解析错误: {e}")
            raise


class DeviceClient:
    """设备控制客户端"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self.protocol_client = ProtocolClient()
        self.socket = None
    
    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"已连接到服务器 {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            logger.info("已断开连接")
    
    def send_request(self, msg_type: int, command: int, items: Dict[str, Any] = None, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """发送请求并接收响应"""
        try:
            # 构建请求
            request_data = self.protocol_client.build_request(msg_type, command, items, format_type)
            
            # 发送请求
            self.socket.send(request_data)
            format_name = "XML" if format_type == DATA_FORMATS['XML'] else "JSON"
            logger.info(f"发送请求 - Type: {msg_type}, Command: {command}, Format: {format_name}")
            
            # 接收响应头部
            header_data = self.recv_exact(self.protocol_client.HEADER_LENGTH)
            header_info = self.protocol_client.parse_header(header_data)
            
            # 接收响应ASDU
            asdu_data = self.recv_exact(header_info['asdu_length'])
            
            # 解析响应
            response = self.protocol_client.parse_response(header_data + asdu_data)
            logger.info(f"收到响应: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"请求处理错误: {e}")
            return {"status": "error", "message": str(e)}
    
    def recv_exact(self, length: int) -> bytes:
        """精确接收指定长度的数据"""
        data = b''
        while len(data) < length:
            chunk = self.socket.recv(length - len(data))
            if not chunk:
                raise ConnectionError("连接已断开")
            data += chunk
        return data
    
    def control_alarm(self, command: int, items: Dict[str, Any] = None, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """控制报警器"""
        return self.send_request(1001, command, items, format_type)
    
    def control_radiation_sensor(self, command: int, items: Dict[str, Any] = None, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """控制辐射传感器"""
        return self.send_request(1002, command, items, format_type)
    
    def get_status(self, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """获取设备状态"""
        return self.send_request(1003, 0, format_type=format_type)
    
    def start_dose_rate_stream(self, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """开始1Hz推送剂量率"""
        return self.control_radiation_sensor(COMMAND_CODES['START_STREAM'], format_type=format_type)
    
    def stop_dose_rate_stream(self, format_type: int = DATA_FORMATS['JSON']) -> Dict[str, Any]:
        """停止推送剂量率"""
        return self.control_radiation_sensor(COMMAND_CODES['STOP_STREAM'], format_type=format_type)
    
    def receive_stream_data(self, timeout: float = None):
        """接收推送的剂量率数据"""
        if timeout:
            self.socket.settimeout(timeout)
        try:
            # 接收响应头部
            header_data = self.recv_exact(self.protocol_client.HEADER_LENGTH)
            if not header_data:
                return None
            
            header_info = self.protocol_client.parse_header(header_data)
            
            # 接收响应ASDU
            asdu_data = self.recv_exact(header_info['asdu_length'])
            if not asdu_data:
                return None
            
            # 解析响应
            response = self.protocol_client.parse_response(header_data + asdu_data)
            return response
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"接收推送数据错误: {e}")
            return None


def test_alarm_control():
    """测试报警器控制"""
    print("\n=== 测试报警器控制 ===")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
                # 设置警灯
        print("设置警灯...")
        response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], {"color": 5, "freq": 3})
        print(f"响应: {response}")

        time.sleep(3)

        # 播放指定音乐
        print("播放音乐 红灯爆闪...")
        response = client.control_alarm(COMMAND_CODES['PLAY_MUSIC'], {"folder": 0x31, "file": 2})
        print(f"响应: {response}")
        
        time.sleep(3)
        
        # 设置音量
        print("设置音量...")
        response = client.control_alarm(COMMAND_CODES['SET_VOLUME'], {"volume": 1})
        print(f"响应: {response}")
        
        time.sleep(1)
        
        # 暂停播放
        print("暂停播放-...")
        response = client.control_alarm(COMMAND_CODES['PAUSE'])
        print(f"响应: {response}")
        
        time.sleep(3)

        # 下一曲
        print("下一曲-...")
        response = client.control_alarm(COMMAND_CODES['NEXT_TRACK'])
        print(f"响应: {response}")
        
        # time.sleep(3)
        
        # 设置警灯
        print("设置警灯...")
        response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], {"color": 5, "freq": 3})
        print(f"响应: {response}")
        
    finally:
        client.disconnect()


def test_radiation_sensor():
    """测试辐射传感器"""
    print("\n=== 测试辐射传感器 ===")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
        # 获取单次剂量率
        print("获取剂量率（单次）...")
        response = client.control_radiation_sensor(COMMAND_CODES['GET_DOSE_RATE'])
        print(f"响应: {response}")
        
    finally:
        client.disconnect()


def test_dose_rate_stream():
    """测试1Hz推送剂量率"""
    print("\n=== 测试1Hz推送剂量率 ===")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
        # 开始推送
        print("开始1Hz推送...")
        response = client.start_dose_rate_stream()
        print(f"响应: {response}")
        
        # 接收推送数据（10秒）
        print("\n接收推送数据（10秒）...")
        count = 0
        start_time = time.time()
        while time.time() - start_time < 10:
            data = client.receive_stream_data(timeout=2.0)
            if data:
                if data.get('status') == 'stream':
                    count += 1
                    print(f"[{count}] 剂量率: {data.get('dose_rate')} {data.get('unit')} - {data.get('timestamp')}")
                else:
                    print(f"收到数据: {data}")
            else:
                print("等待数据...")
        
        # 停止推送
        print("\n停止推送...")
        response = client.stop_dose_rate_stream()
        print(f"响应: {response}")
        
    finally:
        client.disconnect()


def test_status_query():
    """测试状态查询"""
    print("\n=== 测试状态查询 ===")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
        response = client.get_status()
        print(f"设备状态: {response}")
        
    finally:
        client.disconnect()


def test_xml_format():
    """测试XML格式通信"""
    print("\n=== 测试XML格式通信 ===")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
        # 测试XML格式的报警器控制
        print("测试XML格式报警器控制...")
        response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], 
                                      {"color": 5, "freq": 3}, 
                                      DATA_FORMATS['XML'])
        print(f"XML响应: {response}")
        
        time.sleep(2)
        
        # 测试XML格式的辐射传感器
        print("测试XML格式辐射传感器...")
        response = client.control_radiation_sensor(COMMAND_CODES['GET_DOSE_RATE'], 
                                                   format_type=DATA_FORMATS['XML'])
        print(f"XML响应: {response}")
        
        time.sleep(2)
        
        # 测试XML格式的状态查询
        print("测试XML格式状态查询...")
        response = client.get_status(DATA_FORMATS['XML'])
        print(f"XML响应: {response}")
        
    finally:
        client.disconnect()


def interactive_mode():
    """交互模式"""
    print("\n=== 交互模式 ===")
    print("输入命令进行控制:")
    print("辐射传感器:")
    print("  get_dose_rate - 获取剂量率（单次）")
    print("  start_stream - 开始1Hz推送")
    print("  stop_stream - 停止推送")
    print("报警器控制:")
    print("  play_music [folder] [file] - 播放音乐")
    print("  volume_up - 音量+")
    print("  volume_down - 音量-")
    print("  set_volume [vol] - 设置音量")
    print("  pause - 暂停")
    print("  resume - 继续")
    print("  stop - 停止")
    print("  alarm_light [color] [freq] - 设置警灯")
    print("其他:")
    print("  status - 查询状态")
    print("  quit - 退出")
    
    client = DeviceClient()
    if not client.connect():
        return
    
    try:
        while True:
            command = input("\n请输入命令: ").strip().lower()
            
            if command == "quit":
                break
            elif command == "get_dose_rate":
                response = client.control_radiation_sensor(COMMAND_CODES['GET_DOSE_RATE'])
                print(f"响应: {response}")
            elif command == "start_stream":
                response = client.start_dose_rate_stream()
                print(f"响应: {response}")
                print("开始接收推送数据...")
                # 在后台接收数据
                import threading
                def receive_loop():
                    while True:
                        data = client.receive_stream_data(timeout=2.0)
                        if data and data.get('status') == 'stream':
                            print(f"剂量率: {data.get('dose_rate')} {data.get('unit')} - {data.get('timestamp')}")
                stream_thread = threading.Thread(target=receive_loop, daemon=True)
                stream_thread.start()
            elif command == "stop_stream":
                response = client.stop_dose_rate_stream()
                print(f"响应: {response}")
            elif command.startswith("play_music"):
                parts = command.split()
                folder = int(parts[1]) if len(parts) > 1 else 1
                file_num = int(parts[2]) if len(parts) > 2 else 1
                response = client.control_alarm(COMMAND_CODES['PLAY_MUSIC'], {"folder": folder, "file": file_num})
                print(f"响应: {response}")
            elif command == "volume_up":
                response = client.control_alarm(COMMAND_CODES['VOLUME_UP'])
                print(f"响应: {response}")
            elif command == "volume_down":
                response = client.control_alarm(COMMAND_CODES['VOLUME_DOWN'])
                print(f"响应: {response}")
            elif command.startswith("set_volume"):
                parts = command.split()
                vol = int(parts[1]) if len(parts) > 1 else 30
                response = client.control_alarm(COMMAND_CODES['SET_VOLUME'], {"volume": vol})
                print(f"响应: {response}")
            elif command == "pause":
                response = client.control_alarm(COMMAND_CODES['PAUSE'])
                print(f"响应: {response}")
            elif command == "resume":
                response = client.control_alarm(COMMAND_CODES['RESUME'])
                print(f"响应: {response}")
            elif command == "stop":
                response = client.control_alarm(COMMAND_CODES['STOP'])
                print(f"响应: {response}")
            elif command.startswith("alarm_light"):
                parts = command.split()
                color = int(parts[1]) if len(parts) > 1 else 1
                freq = int(parts[2]) if len(parts) > 2 else 1
                response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], {"color": color, "freq": freq})
                print(f"响应: {response}")
            elif command == "status":
                response = client.get_status()
                print(f"设备状态: {response}")
            else:
                print("无效命令")
                
    finally:
        client.disconnect()


def main():
    """主函数"""
    print("TCP Socket客户端测试程序")
    print("1. 测试报警器控制")
    print("2. 测试辐射传感器（单次）")
    print("3. 测试1Hz推送剂量率")
    print("4. 测试状态查询")
    print("5. 测试XML格式通信")
    print("6. 交互模式")
    print("7. 运行所有测试")
    
    choice = input("请选择测试项目 (1-7): ").strip()
    
    if choice == "1":
        test_alarm_control()
    elif choice == "2":
        test_radiation_sensor()
    elif choice == "3":
        test_dose_rate_stream()
    elif choice == "4":
        test_status_query()
    elif choice == "5":
        test_xml_format()
    elif choice == "6":
        interactive_mode()
    elif choice == "7":
        test_alarm_control()
        test_radiation_sensor()
        test_dose_rate_stream()
        test_status_query()
        test_xml_format()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
