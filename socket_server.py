#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP Socket服务器 - 控制报警器和灯光开关
支持自定义协议格式：协议头部 + ASDU(JSON/XML)
"""

import socket
import threading
import json
import xml.etree.ElementTree as ET
import struct
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from config import SERVER_CONFIG, MODBUS_CONFIG, COMMAND_CODES, RADIATION_SENSOR_CONFIG
from modbus_comm import ModbusCommunicator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/user/tcpcontrol/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProtocolHandler:
    """协议处理器"""
    
    # 协议头部常量
    SYNC_BYTES = [0xeb, 0x91, 0xeb, 0x90]
    HEADER_LENGTH = 16
    
    def __init__(self):
        self.message_id = 0
    
    def build_header(self, asdu_length: int, asdu_format: int = 0x01) -> bytes:
        """
        构建协议头部
        Args:
            asdu_length: ASDU长度
            asdu_format: ASDU格式 (0x00=XML, 0x01=JSON)
        Returns:
            协议头部字节
        """
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
        
        # 预留字节 (7字节，填0)
        header[9:16] = b'\x00' * 7
        
        self.message_id = (self.message_id + 1) % 65536
        return bytes(header)
    
    def parse_header(self, header: bytes) -> Dict[str, Any]:
        """
        解析协议头部
        Args:
            header: 协议头部字节
        Returns:
            解析后的头部信息
        """
        if len(header) != self.HEADER_LENGTH:
            raise ValueError(f"协议头部长度错误: {len(header)} != {self.HEADER_LENGTH}")
        
        # 检查同步字符
        sync_bytes = list(header[:4])
        if sync_bytes != self.SYNC_BYTES:
            raise ValueError(f"同步字符错误: {sync_bytes}")
        
        # 解析长度 (小端字节序)
        asdu_length = struct.unpack('<H', header[4:6])[0]
        
        # 解析报文ID (小端字节序)
        message_id = struct.unpack('<H', header[6:8])[0]
        
        # 解析ASDU格式
        asdu_format = header[8]
        
        return {
            'asdu_length': asdu_length,
            'message_id': message_id,
            'asdu_format': asdu_format
        }
    
    def parse_asdu(self, asdu_data: bytes, format_type: int) -> Dict[str, Any]:
        """
        解析ASDU数据
        Args:
            asdu_data: ASDU字节数据
            format_type: 格式类型 (0x00=XML, 0x01=JSON)
        Returns:
            解析后的ASDU数据
        """
        try:
            data_str = asdu_data.decode('utf-8')
            
            if format_type == 0x00:  # XML格式
                root = ET.fromstring(data_str)
                return {
                    'Type': int(root.find('Type').text),
                    'Command': int(root.find('Command').text),
                    'Time': root.find('Time').text,
                    'Items': self._parse_xml_items(root.find('Items'))
                }
            elif format_type == 0x01:  # JSON格式
                return json.loads(data_str)
            else:
                raise ValueError(f"不支持的ASDU格式: {format_type}")
        except Exception as e:
            logger.error(f"ASDU解析错误: {e}")
            raise
    
    def _parse_xml_items(self, items_element) -> Dict[str, Any]:
        """解析XML Items元素"""
        if items_element is None:
            return {}
        
        items = {}
        for child in items_element:
            items[child.tag] = child.text
        return items
    
    def build_response(self, response_data: Dict[str, Any], format_type: int = 0x01) -> bytes:
        """
        构建响应数据
        Args:
            response_data: 响应数据
            format_type: 格式类型 (0x00=XML, 0x01=JSON)
        Returns:
            完整的APDU字节数据
        """
        if format_type == 0x00:  # XML格式
            asdu_data = self._build_xml_response(response_data)
        elif format_type == 0x01:  # JSON格式
            asdu_data = json.dumps(response_data, ensure_ascii=False).encode('utf-8')
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")
        
        header = self.build_header(len(asdu_data), format_type)
        return header + asdu_data
    
    def _build_xml_response(self, data: Dict[str, Any]) -> bytes:
        """构建XML响应"""
        root = ET.Element('Response')
        
        for key, value in data.items():
            elem = ET.SubElement(root, key)
            elem.text = str(value)
        
        xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_str


class DeviceController:
    """设备控制器"""
    
    def __init__(self):
        self.modbus_comm = ModbusCommunicator()
        self.alarm_state = False
        self.current_volume = 30
        self.current_track = 1
        self.is_playing = False
    
    def control_radiation_sensor(self, command: int, items: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        控制辐射传感器（使用Modbus RTU）
        Args:
            command: 命令码
            items: 附加参数
        Returns:
            控制结果或剂量率数据
        """
        try:
            if command == COMMAND_CODES['GET_DOSE_RATE']:  # 获取剂量率（单次）
                dose_rate = self.modbus_comm.get_dose_rate()
                if dose_rate is not None:
                    return {
                        "status": "success",
                        "message": "获取剂量率成功",
                        "dose_rate": dose_rate,
                        "unit": "μSv/h",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                else:
                    return {"status": "error", "message": "获取剂量率失败"}
            else:
                return {"status": "error", "message": f"无效的辐射传感器命令: {command}"}
                
        except Exception as e:
            logger.error(f"辐射传感器控制错误: {e}")
            return {"status": "error", "message": str(e)}
    
    def control_alarm(self, command: int, items: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        控制报警器（使用Modbus RTU）
        Args:
            command: 命令码
            items: 附加参数
        Returns:
            控制结果
        """
        try:
            if items is None:
                items = {}
            
            result = False
            message = ""
            
            if command == COMMAND_CODES['PLAY_MUSIC']:  # 播放指定音乐
                folder = items.get('folder', 1)
                file_num = items.get('file', 1)
                cmd_hex = f"01 06 {folder:02X} 0F 01 {file_num:02X}"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = f"播放音乐: 文件夹01, 文件{file_num}"
                
            elif command == COMMAND_CODES['CIRCLE_MUSIC']:  # 循环
                file_num = items.get('file', 1)
                cmd_hex = f"01 06 00 10 01 {file_num:02X}"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = f"循环播放音乐: 文件夹01, 文件{file_num}"

            elif command == COMMAND_CODES['PREV_TRACK']:  # 上一曲
                cmd_hex = "01 06 00 02 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = "上一曲"
                
            elif command == COMMAND_CODES['NEXT_TRACK']:  # 下一曲
                cmd_hex = "01 06 00 01 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = "下一曲"
                
            elif command == COMMAND_CODES['VOLUME_UP']:  # 音量+
                cmd_hex = "01 06 00 04 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = "音量+"
                
            elif command == COMMAND_CODES['VOLUME_DOWN']:  # 音量-
                cmd_hex = "01 06 00 05 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = "音量-"
                
            elif command == COMMAND_CODES['SET_VOLUME']:  # 设置音量
                vol = items.get('volume', 30)
                vol_hex = f"{vol:02X}"
                cmd_hex = f"01 06 00 06 00 {vol_hex}"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                self.current_volume = vol
                message = f"设置音量为: {vol}"
                
            elif command == COMMAND_CODES['PAUSE']:  # 暂停
                cmd_hex = "01 06 00 0E 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                self.is_playing = False
                message = "暂停播放"
                
            elif command == COMMAND_CODES['RESUME']:  # 继续播放
                cmd_hex = "01 06 00 0D 00 00"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                self.is_playing = True
                message = "继续播放"
                
            elif command == COMMAND_CODES['STOP']:  # 停止
                cmd_hex = "01 06 00 19 00 01"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                self.is_playing = False
                message = "停止播放"
                
            elif command == COMMAND_CODES['SET_ALARM_LIGHT']:  # 设置警灯
                color = items.get('color', 1)
                freq = items.get('freq', 1)
                xy_val = f"{color}{freq}"
                cmd_hex = f"01 06 00 C2 00 {xy_val}"
                result = self.modbus_comm.send_modbus_rtu(cmd_hex)
                message = f"设置警灯: 颜色{color}, 频率{freq}"
                
            elif command == COMMAND_CODES['QUERY_STATUS']:  # 查询状态
                status_data = {
                    "status": "playing" if self.is_playing else "stopped",
                    "volume": self.current_volume,
                    "current_track": self.current_track,
                    "light": {"color": "red", "mode": "steady"}
                }
                return {"status": "success", "message": "状态查询成功", "data": status_data}
                
            else:
                return {"status": "error", "message": f"无效的报警器命令: {command}"}
            
            if result:
                logger.info(message)
                return {"status": "success", "message": message, "result": True}
            else:
                return {"status": "error", "message": "报警器控制失败", "result": False}
                
        except Exception as e:
            logger.error(f"报警器控制错误: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        return {
            "alarm_state": self.alarm_state,
            "current_volume": self.current_volume,
            "current_track": self.current_track,
            "is_playing": self.is_playing,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def close(self):
        """关闭连接"""
        self.modbus_comm.close()


class SocketServer:
    """TCP Socket服务器"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or SERVER_CONFIG['host']
        self.port = port or SERVER_CONFIG['port']
        self.protocol_handler = ProtocolHandler()
        self.device_controller = DeviceController()
        self.running = False
        self.server_socket = None
        # 客户端推送状态管理 {client_address: {'streaming': bool, 'thread': thread, 'format': int}}
        self.client_streams = {}
    
    def start(self):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"TCP服务器启动成功，监听地址: {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"客户端连接: {client_address}")
                    
                    # 为每个客户端创建新线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"接受连接错误: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"服务器启动错误: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("服务器已停止")
    
    def handle_client(self, client_socket: socket.socket, client_address):
        """处理客户端连接"""
        client_key = str(client_address)
        try:
            while self.running:
                # 接收协议头部
                header_data = self.recv_exact(client_socket, self.protocol_handler.HEADER_LENGTH)
                if not header_data:
                    break
                
                # 解析协议头部
                header_info = self.protocol_handler.parse_header(header_data)
                logger.info(f"收到消息 - ID: {header_info['message_id']}, ASDU长度: {header_info['asdu_length']}")
                
                # 接收ASDU数据
                asdu_data = self.recv_exact(client_socket, header_info['asdu_length'])
                if not asdu_data:
                    break
                
                # 解析ASDU
                parsed_data = self.protocol_handler.parse_asdu(asdu_data, header_info['asdu_format'])
                logger.info(f"解析ASDU: {parsed_data}")
                
                # 处理命令（特殊处理流式推送命令）
                msg_type = parsed_data.get('Type', 0)
                command = parsed_data.get('Command', 0)
                
                if msg_type == 1002 and command == COMMAND_CODES['START_STREAM']:
                    # 开始1Hz推送
                    self._start_stream(client_socket, client_address, header_info['asdu_format'])
                    response = {"status": "success", "message": "开始1Hz推送剂量率数据"}
                elif msg_type == 1002 and command == COMMAND_CODES['STOP_STREAM']:
                    # 停止推送
                    self._stop_stream(client_address)
                    response = {"status": "success", "message": "停止推送"}
                else:
                    # 处理其他命令
                    response = self.process_command(parsed_data)
                
                # 发送响应
                response_data = self.protocol_handler.build_response(response, header_info['asdu_format'])
                client_socket.send(response_data)
                logger.info(f"发送响应: {response}")
                
        except Exception as e:
            logger.error(f"处理客户端 {client_address} 错误: {e}")
        finally:
            # 停止推送并清理
            self._stop_stream(client_address)
            if client_key in self.client_streams:
                del self.client_streams[client_key]
            client_socket.close()
            logger.info(f"客户端 {client_address} 断开连接")
    
    def _start_stream(self, client_socket: socket.socket, client_address, format_type: int):
        """启动1Hz推送线程"""
        client_key = str(client_address)
        
        # 如果已经在推送，先停止
        if client_key in self.client_streams:
            self._stop_stream(client_address)
        
        # 创建推送线程
        stream_thread = threading.Thread(
            target=self._stream_dose_rate,
            args=(client_socket, client_address, format_type),
            daemon=True
        )
        
        self.client_streams[client_key] = {
            'streaming': True,
            'thread': stream_thread,
            'format': format_type
        }
        
        stream_thread.start()
        logger.info(f"客户端 {client_address} 开始1Hz推送")
    
    def _stop_stream(self, client_address):
        """停止推送"""
        client_key = str(client_address)
        if client_key in self.client_streams:
            self.client_streams[client_key]['streaming'] = False
            logger.info(f"客户端 {client_address} 停止推送")
    
    def _stream_dose_rate(self, client_socket: socket.socket, client_address, format_type: int):
        """1Hz推送剂量率数据"""
        client_key = str(client_address)
        interval = RADIATION_SENSOR_CONFIG['stream_interval']
        
        try:
            while self.running:
                if client_key not in self.client_streams:
                    break
                
                if not self.client_streams[client_key]['streaming']:
                    break
                
                # 获取剂量率
                dose_rate = self.device_controller.modbus_comm.get_dose_rate()
                if dose_rate is not None:
                    # 构建推送数据
                    stream_data = {
                        "status": "stream",
                        "dose_rate": dose_rate,
                        "unit": "μSv/h",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 发送数据
                    response_data = self.protocol_handler.build_response(stream_data, format_type)
                    client_socket.send(response_data)
                    logger.debug(f"推送剂量率到 {client_address}: {dose_rate} μSv/h")
                else:
                    logger.warning(f"获取剂量率失败，跳过本次推送")
                
                # 等待1秒
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"推送线程 {client_address} 错误: {e}")
        finally:
            if client_key in self.client_streams:
                self.client_streams[client_key]['streaming'] = False
    
    def recv_exact(self, sock: socket.socket, length: int) -> bytes:
        """精确接收指定长度的数据"""
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return b''
            data += chunk
        return data
    
    def process_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理命令"""
        try:
            msg_type = data.get('Type', 0)
            command = data.get('Command', 0)
            items = data.get('Items', {})
            
            # 根据消息类型处理不同命令
            if msg_type == 1001:  # 报警器控制
                return self.device_controller.control_alarm(command, items)
            elif msg_type == 1002:  # 辐射传感器控制
                return self.device_controller.control_radiation_sensor(command, items)
            elif msg_type == 1003:  # 状态查询
                return self.device_controller.get_status()
            else:
                return {"status": "error", "message": f"不支持的消息类型: {msg_type}"}
                
        except Exception as e:
            logger.error(f"命令处理错误: {e}")
            return {"status": "error", "message": str(e)}


def main():
    """主函数"""
    server = SocketServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
        server.stop()


if __name__ == "__main__":
    main()
