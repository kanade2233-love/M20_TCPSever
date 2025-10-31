#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRC16-MODBUS计算模块
"""

def calc_crc16_modbus(data):
    """
    计算CRC16-MODBUS校验码
    Args:
        data: 字节数据
    Returns:
        CRC16校验码 (2字节)
    """
    crc = 0xFFFF
    
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    
    return crc & 0xFFFF

def bytes_to_hex_string(data):
    """
    将字节数据转换为十六进制字符串
    Args:
        data: 字节数据
    Returns:
        十六进制字符串
    """
    return ' '.join(f'{b:02X}' for b in data)

def hex_string_to_bytes(hex_str):
    """
    将十六进制字符串转换为字节数据
    Args:
        hex_str: 十六进制字符串
    Returns:
        字节数据
    """
    return bytes.fromhex(hex_str.replace(' ', ''))

def add_crc_to_modbus_command(command_hex):
    """
    为Modbus命令添加CRC校验码
    Args:
        command_hex: 不带CRC的命令十六进制字符串
    Returns:
        带CRC的完整命令十六进制字符串
    """
    # 移除空格并转换为字节
    command_bytes = hex_string_to_bytes(command_hex)
    
    # 计算CRC
    crc = calc_crc16_modbus(command_bytes)
    
    # 添加CRC到命令末尾（小端字节序）
    crc_bytes = crc.to_bytes(2, byteorder='little')
    
    # 组合完整命令
    full_command = command_bytes + crc_bytes
    
    return bytes_to_hex_string(full_command)




