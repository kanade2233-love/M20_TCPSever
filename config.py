#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

# 服务器配置
SERVER_CONFIG = {
    'host': '0.0.0.0',  # 监听所有网络接口
    'port': 8888,       # 监听端口
    'max_connections': 5,  # 最大连接数
    'timeout': 30,      # 连接超时时间(秒)
}

# Modbus配置
MODBUS_CONFIG = {
    'serial_port': '/dev/ttyUSB0',  # 串口设备（与报警器和辐射传感器共用）
    'baudrate': 9600,           # 串口波特率
    'timeout': 1,               # 串口超时时间
}

# 协议配置
PROTOCOL_CONFIG = {
    'sync_bytes': [0xeb, 0x91, 0xeb, 0x90],  # 同步字符
    'header_length': 16,  # 协议头部长度
    'max_asdu_length': 65535,  # ASDU最大长度
    'default_format': 0x00,  # 默认格式 (JSON)
}

# 数据格式定义
DATA_FORMATS = {
    'XML': 0x00,    # XML格式
    'JSON': 0x01,   # JSON格式
}

# 设备配置
DEVICE_CONFIG = {
    'alarm_pin': 18,      # 报警器控制引脚 (GPIO)
}

# 消息类型定义
MESSAGE_TYPES = {
    'ALARM_CONTROL': 1001,    # 报警器控制
    'RADIATION_SENSOR': 1002, # 辐射传感器
    'STATUS_QUERY': 1003,     # 状态查询
    'SYSTEM_INFO': 1004,      # 系统信息
}

# 命令码定义
COMMAND_CODES = {
    # 报警器控制命令
    'PLAY_MUSIC': 1,        # 播放指定音乐
    'PREV_TRACK': 2,        # 上一曲
    'NEXT_TRACK': 3,        # 下一曲
    'VOLUME_UP': 4,         # 音量+
    'VOLUME_DOWN': 5,       # 音量-
    'SET_VOLUME': 6,        # 设置音量
    'PAUSE': 7,             # 暂停
    'RESUME': 8,            # 继续播放
    'STOP': 9,              # 停止
    'SET_ALARM_LIGHT': 10,  # 设置警灯
    'QUERY_STATUS': 11,     # 查询状态
    
    # 辐射传感器命令
    'GET_DOSE_RATE': 1,     # 获取剂量率
    'START_STREAM': 2,      # 开始1Hz推送
    'STOP_STREAM': 3,       # 停止推送
}

# 辐射传感器配置
RADIATION_SENSOR_CONFIG = {
    'modbus_address': 2,    # Modbus设备地址
    'register_address': 0x0001,  # 寄存器地址
    'register_count': 2,    # 读取寄存器数量
    'stream_interval': 1.0, # 推送间隔（秒）- 1Hz
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': '/home/wheeltec/controltest/server.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}
