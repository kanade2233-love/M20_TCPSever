# TCP Socket服务器 - 报警器和灯光控制

基于自定义TCP协议的Socket服务器，用于远程控制机器狗的报警器和灯光开关。

## 功能特性

- 支持自定义TCP协议格式（协议头部 + ASDU）
- 支持JSON和XML数据格式
- 多客户端并发连接
- 完整的日志记录
- **Modbus TCP通信**（灯光控制）
- **Modbus RTU通信**（报警器控制）
- **CRC16-MODBUS校验**自动计算
- **丰富的灯光控制**（日行灯、远光灯、全部灯光）
- **完整的报警器控制**（音乐播放、音量控制、警灯设置）
- 设备状态查询

## 协议规范

### 协议头部结构（16字节）

| 序号 | 内容 | 长度 | 值 | 备注 |
|------|------|------|-----|------|
| 1-4 | 同步字符 | 4 | 0xeb, 0x91, 0xeb, 0x90 | 固定 |
| 5-6 | 长度 | 2 | - | ASDU长度，小端字节序 |
| 7-8 | 报文ID | 2 | - | 唯一标识，小端字节序 |
| 9 | ASDU格式 | 1 | 0x00(XML) 或 0x01(JSON) | 数据格式 |
| 10-16 | 预留 | 7 | 0x00 | 预留字节 |

### ASDU结构

```json
{
    "Type": 1001,
    "Command": 1,
    "Time": "2023-01-01 00:00:00",
    "Items": {
        "light_type": "all"
    }
}
```

### 消息类型

- `1001`: 灯光控制
- `1002`: 报警器控制
- `1003`: 状态查询

### 灯光控制命令码

- `1`: 开日行灯
- `2`: 关日行灯
- `3`: 开远光灯（自动关日行灯）
- `4`: 关远光灯
- `5`: 全开
- `6`: 全关

### 报警器控制命令码

- `1`: 播放指定音乐
- `2`: 上一曲
- `3`: 下一曲
- `4`: 音量+
- `5`: 音量-
- `6`: 设置音量
- `7`: 暂停
- `8`: 继续播放
- `9`: 停止
- `10`: 设置警灯
- `11`: 查询状态

## 安装和使用

### 1. 安装依赖

```bash
# 安装Python依赖包
python3 install_deps.py
```

### 2. 配置参数

编辑 `config.py` 文件，修改以下配置：

```python
# Modbus配置
MODBUS_CONFIG = {
    'tcp_ip': '192.168.0.7',    # Modbus TCP服务器IP
    'tcp_port': 8234,           # Modbus TCP端口
    'serial_port': '/dev/ttyUSB0',  # 串口设备
    'baudrate': 9600,           # 串口波特率
}
```

### 3. 启动服务器

```bash
# 方法1: 使用启动脚本
chmod +x start.sh
./start.sh

# 方法2: 直接运行
python3 socket_server.py
```

### 4. 运行客户端测试

```bash
python3 client_test.py
```

### 5. 查看日志

```bash
tail -f server.log
```

## 使用示例

### 控制灯光

```python
from client_test import DeviceClient
from config import COMMAND_CODES

client = DeviceClient('localhost', 8888)
client.connect()

# 开启日行灯
response = client.control_lights(COMMAND_CODES['DAYLIGHT_ON'])
print(response)

# 开启远光灯
response = client.control_lights(COMMAND_CODES['HIGHBEAM_ON'])
print(response)

# 开启所有灯光
response = client.control_lights(COMMAND_CODES['ALL_LIGHTS_ON'])
print(response)

client.disconnect()
```

### 控制报警器

```python
# 播放指定音乐
response = client.control_alarm(COMMAND_CODES['PLAY_MUSIC'], {"folder": 1, "file": 2})
print(response)

# 设置音量
response = client.control_alarm(COMMAND_CODES['SET_VOLUME'], {"volume": 50})
print(response)

# 设置警灯
response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], {"color": 2, "freq": 3})
print(response)
```

### 查询状态

```python
status = client.get_status()
print(status)
```

## 配置文件

编辑 `config.py` 文件可以修改：

- 服务器监听地址和端口
- 协议参数
- 设备引脚配置
- 日志设置

## 网络通信

服务器默认监听 `0.0.0.0:8888`，支持多客户端同时连接。

客户端可以通过TCP连接到服务器进行设备控制。

### Modbus通信

- **灯光控制**: 使用Modbus TCP协议与IP `192.168.0.7:8234` 通信
- **报警器控制**: 使用Modbus RTU协议通过串口 `/dev/ttyUSB0` 通信
- **CRC校验**: 自动计算CRC16-MODBUS校验码

## 日志

服务器运行日志保存在 `server.log` 文件中，包含：

- 连接和断开信息
- 命令处理记录
- 错误信息
- 设备状态变化

## 错误处理

- 协议格式错误
- 网络连接异常
- 设备控制失败
- 数据解析错误

所有错误都会记录到日志文件中。

## 扩展功能

可以基于现有框架扩展：

- 添加更多设备类型
- 支持更多命令
- 添加设备状态监控
- 实现设备组控制
- 添加用户认证

## 注意事项

1. 确保Python3环境已安装
2. 检查端口8888是否被占用
3. 确保有足够的文件权限
4. 建议在生产环境中添加用户认证机制
