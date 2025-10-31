#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus通信模块
支持Modbus TCP和Modbus RTU通信
"""

import socket
import serial
import time
import logging
from typing import Optional
from config import MODBUS_CONFIG
from crc_module import add_crc_to_modbus_command

logger = logging.getLogger(__name__)

class ModbusCommunicator:
    """Modbus通信器"""
    
    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self._init_serial()
    
    def _init_serial(self):
        """初始化串口连接"""
        try:
            self.serial_conn = serial.Serial(
                port=MODBUS_CONFIG['serial_port'],
                baudrate=MODBUS_CONFIG['baudrate'],
                timeout=MODBUS_CONFIG['timeout']
            )
            logger.info(f"串口 {MODBUS_CONFIG['serial_port']} 初始化成功")
        except Exception as e:
            logger.error(f"串口初始化失败: {e}")
            self.serial_conn = None
    
    def send_modbus_rtu_with_response(self, command_hex: str, timeout: float = 1.0) -> Optional[bytes]:
        """
        发送Modbus RTU命令并读取响应
        Args:
            command_hex: 十六进制命令字符串（不包含CRC）
            timeout: 读取超时时间（秒）
        Returns:
            响应字节数据（不包含CRC），失败返回None
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("串口未连接")
            return None
        
        try:
            # 清空输入缓冲区
            self.serial_conn.reset_input_buffer()
            
            # 添加CRC校验码
            full_command = add_crc_to_modbus_command(command_hex)
            command_bytes = bytes.fromhex(full_command.replace(' ', ''))
            
            # 发送命令
            self.serial_conn.write(command_bytes)
            logger.info(f"发送Modbus RTU命令: {full_command}")
            
            # 等待一小段时间让设备处理命令（Modbus RTU需要字符间隔）
            time.sleep(0.05)  # 50ms延迟
            
            # 读取响应
            # 响应格式：地址(1) + 功能码(1) + 数据长度(1) + 数据(N) + CRC(2)
            original_timeout = self.serial_conn.timeout
            self.serial_conn.timeout = timeout
            
            try:
                # 方法1: 先尝试读取前3字节确定数据长度
                header = b''
                start_time = time.time()
                
                # 循环读取直到收到至少3字节头部
                while len(header) < 3:
                    if time.time() - start_time > timeout:
                        logger.error(f"读取响应头部超时: 只读到{len(header)}字节")
                        return None
                    chunk = self.serial_conn.read(3 - len(header))
                    if chunk:
                        header += chunk
                
                if len(header) < 3:
                    logger.error(f"读取响应头部失败: 只读到{len(header)}字节")
                    return None
                
                # 检查功能码是否正确
                if header[1] != 3:
                    logger.error(f"响应功能码错误: 期望0x03, 收到0x{header[1]:02X}")
                    return None
                
                data_length = header[2]
                expected_total_length = 3 + data_length + 2  # 头部(3) + 数据(N) + CRC(2)
                
                # 读取剩余数据
                remaining = b''
                start_time = time.time()
                while len(remaining) < data_length + 2:
                    if time.time() - start_time > timeout:
                        logger.error(f"读取响应数据超时: 期望{data_length + 2}字节，只读到{len(remaining)}字节")
                        return None
                    chunk = self.serial_conn.read(expected_total_length - len(header) - len(remaining))
                    if chunk:
                        remaining += chunk
                
                if len(remaining) < data_length + 2:
                    logger.error(f"读取响应数据失败: 期望{data_length + 2}字节，只读到{len(remaining)}字节")
                    return None
                
                # 组合完整响应
                response = header + remaining
                logger.info(f"Modbus RTU响应: {response.hex().upper()}")
                
                # 验证CRC
                response_without_crc = response[:-2]
                received_crc = int.from_bytes(response[-2:], byteorder='little')
                calculated_crc = self._calc_crc16_modbus(response_without_crc)
                
                if received_crc != calculated_crc:
                    logger.error(f"CRC校验失败: 收到0x{received_crc:04X}, 计算0x{calculated_crc:04X}")
                    logger.error(f"响应数据: {response.hex().upper()}")
                    logger.error(f"响应数据(无CRC): {response_without_crc.hex().upper()}")
                    return None
                
                # 返回不带CRC的响应数据
                return response_without_crc
                
            finally:
                self.serial_conn.timeout = original_timeout
                
        except Exception as e:
            logger.error(f"Modbus RTU通信失败: {e}", exc_info=True)
            return None
    
    def _calc_crc16_modbus(self, data: bytes) -> int:
        """计算CRC16-MODBUS校验码"""
        from crc_module import calc_crc16_modbus
        return calc_crc16_modbus(data)
    
    def send_modbus_rtu(self, command_hex: str) -> bool:
        """
        发送Modbus RTU命令
        Args:
            command_hex: 十六进制命令字符串（不包含CRC）
        Returns:
            发送是否成功
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("串口未连接")
            return False
        
        try:
            # 添加CRC校验码
            full_command = add_crc_to_modbus_command(command_hex)
            command_bytes = bytes.fromhex(full_command.replace(' ', ''))
            
            # 发送命令
            self.serial_conn.write(command_bytes)
            logger.info(f"发送Modbus RTU命令: {full_command}")
            
            # 可选：读取响应
            # response = self.serial_conn.read(1024)
            # logger.info(f"Modbus RTU响应: {response.hex()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Modbus RTU通信失败: {e}")
            return False
    
    def parse_dose_rate(self, response_data: bytes) -> Optional[float]:
        """
        解析辐射传感器剂量率数据
        Args:
            response_data: Modbus响应数据（不含CRC，格式：02 03 04 AA 00 00 00）
        Returns:
            剂量率值（单位：μSv/h），失败返回None
        """
        try:
            if len(response_data) < 7:
                logger.error(f"响应数据长度不足: {len(response_data)} < 7")
                return None
            
            # 响应格式：地址(1) + 功能码(1) + 数据长度(1) + 数据(4字节)
            from config import RADIATION_SENSOR_CONFIG
            expected_address = RADIATION_SENSOR_CONFIG['modbus_address']
            
            if response_data[0] != expected_address:
                logger.error(f"响应地址错误: 期望{expected_address}, 收到{response_data[0]}")
                return None
            
            if response_data[1] != 3:
                logger.error(f"响应功能码错误: 期望0x03, 收到0x{response_data[1]:02X}")
                return None
            
            data_length = response_data[2]
            if data_length != 4:
                logger.error(f"数据长度错误: {data_length} != 4")
                return None
            
            # 提取4字节数据：FF 00 00 00
            data_bytes = response_data[3:7]
            
            # 解析：FF+(00×0x100)+(00×0x10000)+(00×0x1000000)
            dose_rate_nsv = (data_bytes[0] + 
                           (data_bytes[1] * 0x100) + 
                           (data_bytes[2] * 0x10000) + 
                           (data_bytes[3] * 0x1000000))
            
            # 转换为μSv/h (1μSv/h = 1000nSv/h)
            dose_rate_usv = dose_rate_nsv / 1000.0
            
            logger.debug(f"剂量率解析: {data_bytes.hex().upper()} -> {dose_rate_nsv}nSv/h = {dose_rate_usv}μSv/h")
            return dose_rate_usv
            
        except Exception as e:
            logger.error(f"剂量率解析错误: {e}")
            return None
    
    def get_dose_rate(self) -> Optional[float]:
        """
        获取辐射传感器剂量率
        Returns:
            剂量率值（单位：μSv/h），失败返回None
        """
        from config import RADIATION_SENSOR_CONFIG
        
        # 构建读取命令：01 03 00 01 00 02
        cmd = f"{RADIATION_SENSOR_CONFIG['modbus_address']:02X} 03 00 01 00 02"
        
        response = self.send_modbus_rtu_with_response(cmd)
        if response is None:
            return None
        
        return self.parse_dose_rate(response)
    
    def close(self):
        """关闭连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("串口连接已关闭")




