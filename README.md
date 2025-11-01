# TCP Socket服务器 - 报警器和辐射传感器控制

基于自定义TCP协议的Socket服务器，用于远程控制声光报警器和辐射传感器设备。

## 功能特性

- 支持自定义TCP协议格式（协议头部 + ASDU）
- 支持JSON和XML数据格式
- 多客户端并发连接
- 完整的日志记录
- **Modbus RTU通信**（报警器和辐射传感器共用串口）
- **CRC16-MODBUS校验**自动计算
- **完整的报警器控制**（音乐播放、音量控制、警灯设置）
- **辐射传感器剂量率监测**（单次查询和1Hz实时推送）
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

**JSON格式示例：**
```json
{
    "Type": 1002,
    "Command": 1,
    "Time": "2023-01-01 00:00:00",
    "Items": {}
}
```

**XML格式示例：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1002</Type>
	<Command>1</Command>
	<Time>2023-01-01 00:00:00</Time>
	<Items/>
</PatrolDevice>
```

### 消息类型

| Type值 | 说明 | 备注 |
|--------|------|------|
| 1001 | 报警器控制 | 控制声光报警器 |
| 1002 | 辐射传感器控制 | 获取剂量率、启动/停止推送 |
| 1003 | 状态查询 | 查询设备状态 |

### 报警器控制命令码（Type=1001）

| Command值 | 说明 | Items参数 | Modbus RTU命令 |
|-----------|------|-----------|----------------|
| 1 | 播放指定音乐 | folder, file | `FF 06 {folder:02X} 03 00 {file:02X}` |
| 2 | 上一曲 | 无 | `FF 06 00 02 00 00` |
| 3 | 下一曲 | 无 | `FF 06 00 01 00 00` |
| 4 | 音量+ | 无 | `FF 06 00 04 00 00` |
| 5 | 音量- | 无 | `FF 06 00 05 00 00` |
| 6 | 设置音量 | volume | `FF 06 00 06 00 {volume:02X}` |
| 7 | 暂停 | 无 | `FF 06 00 0E 00 00` |
| 8 | 继续播放 | 无 | `FF 06 00 0D 00 00` |
| 9 | 停止 | 无 | `FF 06 00 16 00 01` |
| 10 | 设置警灯 | color, freq | `FF 06 00 C2 00 {color}{freq}` |
| 11 | 查询状态 | 无 | - |

### 辐射传感器命令码（Type=1002）

| Command值 | 说明 | Items参数 | 功能 |
|-----------|------|-----------|------|
| 1 | 获取剂量率 | 无 | 单次读取剂量率值 |
| 2 | 开始1Hz推送 | 无 | 启动每秒推送剂量率数据 |
| 3 | 停止推送 | 无 | 停止推送 |

## 辐射传感器RTU命令详解

### 命令组成和发送流程

#### 1. 命令构建

在 `modbus_comm.py` 的 `get_dose_rate()` 方法中，命令构建如下：

```python
from config import RADIATION_SENSOR_CONFIG

# 构建读取命令：{地址} 03 {寄存器地址高} {寄存器地址低} {寄存器数量高} {寄存器数量低}
cmd = f"{RADIATION_SENSOR_CONFIG['modbus_address']:02X} 03 00 01 00 02"
```

**示例**（地址为1，寄存器地址0x0001，读取2个寄存器）：
- 地址：`01` (从 `RADIATION_SENSOR_CONFIG['modbus_address']` 获取，默认为1)
- 功能码：`03` (读保持寄存器)
- 寄存器地址：`00 01` (高字节在前，大端序)
- 寄存器数量：`00 02` (读取2个寄存器 = 4字节数据)

**命令（不含CRC）：** `01 03 00 01 00 02`

#### 2. CRC校验码计算

使用CRC16-MODBUS算法计算校验码：

```python
from crc_module import add_crc_to_modbus_command

# 命令（不含CRC）
command_hex = "01 03 00 01 00 02"

# 添加CRC校验码
full_command = add_crc_to_modbus_command(command_hex)
# 结果：01 03 00 01 00 02 95 CB
```

**CRC计算过程：**
1. 将命令转换为字节：`[0x01, 0x03, 0x00, 0x01, 0x00, 0x02]`
2. 使用CRC16-MODBUS算法计算：结果为 `0xCB95`
3. 转换为小端字节序：`95 CB`

**完整命令：** `01 03 00 01 00 02 95 CB`

#### 3. 发送命令

通过串口发送完整命令：

```python
command_bytes = bytes.fromhex(full_command.replace(' ', ''))
serial_conn.write(command_bytes)
```

#### 4. 接收响应

设备响应格式：`01 03 04 FF 00 00 00 CA 27`

- `01`：设备地址
- `03`：功能码（读保持寄存器）
- `04`：数据长度（4字节）
- `FF 00 00 00`：剂量率数据（4字节）
- `CA 27`：CRC校验码（小端字节序）

#### 5. 解析剂量率

剂量率数据解析公式：
```
剂量率(nSv/h) = 字节0 + (字节1 × 0x100) + (字节2 × 0x10000) + (字节3 × 0x1000000)
剂量率(μSv/h) = 剂量率(nSv/h) / 1000.0
```

**示例解析 `FF 00 00 00`：**
- `0xFF + (0x00 × 0x100) + (0x00 × 0x10000) + (0x00 × 0x1000000)`
- `= 255 + 0 + 0 + 0`
- `= 255 nSv/h`
- `= 0.255 μSv/h`

### 完整流程图

```
客户端请求（Type=1002, Command=1）
    ↓
服务器调用 get_dose_rate()
    ↓
构建RTU命令：01 03 00 01 00 02
    ↓
计算CRC：添加 95 CB
    ↓
完整命令：01 03 00 01 00 02 95 CB
    ↓
通过串口 /dev/ttyUSB0 发送
    ↓
等待50ms（Modbus RTU字符间隔）
    ↓
读取响应：01 03 04 FF 00 00 00 CA 27
    ↓
验证CRC校验码
    ↓
解析剂量率数据：FF 00 00 00 → 255 nSv/h → 0.255 μSv/h
    ↓
返回响应给客户端
```

## 安装和使用

### 1. 安装依赖

```bash
# 安装Python依赖包
python3 install_deps.py
```

### 2. 配置参数

编辑 `config.py` 文件，修改以下配置：

```python
# 服务器配置
SERVER_CONFIG = {
    'host': '0.0.0.0',  # 监听地址
    'port': 8888,       # 监听端口
}

# Modbus配置
MODBUS_CONFIG = {
    'serial_port': '/dev/ttyUSB0',  # 串口设备（与报警器和辐射传感器共用）
    'baudrate': 9600,           # 串口波特率
    'timeout': 1,               # 串口超时时间
}

# 辐射传感器配置
RADIATION_SENSOR_CONFIG = {
    'modbus_address': 1,         # Modbus设备地址（示例中使用1）
    'register_address': 0x0001,  # 寄存器地址
    'register_count': 2,        # 读取寄存器数量（2个寄存器=4字节数据）
    'stream_interval': 1.0,     # 推送间隔（秒）- 1Hz
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

测试菜单选项：
- 1. 测试报警器控制
- 2. 测试辐射传感器（单次）
- 3. 测试1Hz推送剂量率
- 4. 测试状态查询
- 5. 测试XML格式通信
- 6. 交互模式
- 7. 运行所有测试

### 5. 查看日志

```bash
tail -f server.log
```

## 使用示例

### 控制报警器

```python
from client_test import DeviceClient
from config import COMMAND_CODES

client = DeviceClient('localhost', 8888)
client.connect()

# 播放指定音乐
response = client.control_alarm(COMMAND_CODES['PLAY_MUSIC'], {"folder": 49, "file": 2})
print(response)

# 设置音量
response = client.control_alarm(COMMAND_CODES['SET_VOLUME'], {"volume": 50})
print(response)

# 设置警灯
response = client.control_alarm(COMMAND_CODES['SET_ALARM_LIGHT'], {"color": 2, "freq": 3})
print(response)

# 停止播放
response = client.control_alarm(COMMAND_CODES['STOP'])
print(response)

client.disconnect()
```

### 辐射传感器操作

```python
from client_test import DeviceClient
from config import COMMAND_CODES

client = DeviceClient('localhost', 8888)
client.connect()

# 获取单次剂量率
response = client.control_radiation_sensor(COMMAND_CODES['GET_DOSE_RATE'])
print(response)
# 输出: {'status': 'success', 'dose_rate': 0.17, 'unit': 'μSv/h', ...}

# 开始1Hz推送
response = client.start_dose_rate_stream()
print(response)

# 接收推送数据（持续10秒）
import time
start_time = time.time()
while time.time() - start_time < 10:
    data = client.receive_stream_data(timeout=2.0)
    if data and data.get('status') == 'stream':
        print(f"剂量率: {data.get('dose_rate')} {data.get('unit')}")

# 停止推送
response = client.stop_dose_rate_stream()
print(response)

client.disconnect()
```

### 查询状态

```python
status = client.get_status()
print(status)
```

## 网络通信

服务器默认监听 `0.0.0.0:8888`，支持多客户端同时连接。

客户端可以通过TCP连接到服务器进行设备控制。

### Modbus RTU通信

- **串口设备**: `/dev/ttyUSB0`
- **波特率**: 9600
- **数据格式**: 8位数据位，无奇偶校验，1位停止位（8N1）
- **协议**: Modbus RTU
- **设备共享**: 报警器和辐射传感器共用同一串口，通过不同的Modbus地址区分
  - 报警器：地址 `FF` (0xFF)
  - 辐射传感器：地址 `01` (从配置读取，默认1)

### CRC校验

所有Modbus RTU命令自动添加CRC16-MODBUS校验码，响应数据也会进行CRC校验。

## 1Hz推送功能

当客户端发送 `Type=1002, Command=2`（开始推送）命令后：

1. 服务器为该客户端创建独立的推送线程
2. 每1秒（可配置）读取一次辐射传感器剂量率
3. 自动将剂量率数据推送给客户端
4. 推送格式与请求格式一致（XML或JSON）
5. 客户端发送 `Command=3`（停止推送）可停止推送

**推送数据格式：**
```json
{
    "status": "stream",
    "dose_rate": 0.17,
    "unit": "μSv/h",
    "timestamp": "2023-12-15 14:30:25"
}
```

## 日志

服务器运行日志保存在 `server.log` 文件中，包含：

- 连接和断开信息
- 命令处理记录
- Modbus RTU命令和响应
- 错误信息
- 设备状态变化
- 剂量率数据记录

## 错误处理

- 协议格式错误
- 网络连接异常
- Modbus RTU通信失败
- CRC校验失败
- 设备控制失败
- 数据解析错误

所有错误都会记录到日志文件中，并返回相应的错误响应。

## 注意事项

1. 确保Python3环境已安装
2. 检查端口8888是否被占用
3. 确保串口设备 `/dev/ttyUSB0` 存在且有权限访问
4. 确保辐射传感器Modbus地址配置正确（默认1）
5. 串口设备与报警器和辐射传感器共用，注意地址区分
6. 建议在生产环境中添加用户认证机制
7. 1Hz推送会持续占用串口，注意避免与其他操作冲突

## 文件结构

```
tcpcontrol/
├── socket_server.py      # TCP服务器主程序
├── client_test.py        # 客户端测试程序
├── modbus_comm.py       # Modbus RTU通信模块
├── crc_module.py        # CRC16-MODBUS校验模块
├── config.py            # 配置文件
├── README.md            # 本文档
├── ASDU_EXAMPLES.md     # ASDU格式示例文档
├── start.sh             # 启动脚本
├── install_deps.py      # 依赖安装脚本
└── server.log           # 日志文件
```

## 扩展功能

可以基于现有框架扩展：

- 添加更多设备类型
- 支持更多命令
- 添加设备状态监控
- 实现设备组控制
- 添加用户认证
- 支持多串口设备
- 添加数据历史记录