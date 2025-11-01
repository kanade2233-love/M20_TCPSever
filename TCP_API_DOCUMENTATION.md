# TCP接口开发文档

## 版本信息

- **文档版本**: v1.0
- **接口版本**: v1.0
- **更新日期**: 2025-10-31

## 目录

- [1. 概述](#1-概述)
- [2. 连接信息](#2-连接信息)
- [3. 协议规范](#3-协议规范)
- [4. 数据格式](#4-数据格式)
- [5. 消息类型与命令码](#5-消息类型与命令码)
- [6. 接口详细说明](#6-接口详细说明)
- [7. 错误处理](#7-错误处理)
- [8. 开发示例](#8-开发示例)
- [9. 注意事项](#9-注意事项)

---

## 1. 概述

本文档描述TCP Socket接口的通信协议，用于远程控制声光报警器和辐射传感器设备。
git@github.com:kanade2233-love/M20_TCPSever.git

### 1.1 功能特性

- 支持自定义TCP协议格式（协议头部 + ASDU）
- 支持JSON和XML两种数据格式
- 支持多客户端并发连接
- 支持1Hz实时数据推送
- 完整的错误处理和日志记录

### 1.2 通信方式

- **协议**: TCP Socket
- **数据编码**: UTF-8
- **字节序**: 小端字节序（Little Endian）

---

## 2. 连接信息

### 2.1 服务器地址

- **IP地址**: `10.21.31.104`（可配置）
- **端口**: `8888`（可配置）
- **协议**: TCP

### 2.2 连接方式

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('10.21.31.104', 8888))
```

### 2.3 连接超时

建议设置连接超时时间：
- **连接超时**: 5秒
- **读取超时**: 30秒

---

## 3. 协议规范

### 3.1 报文结构

每个完整的报文（APDU）由两部分组成：
1. **协议头部**（固定16字节）
2. **ASDU数据**（可变长度，由头部中的长度字段指定）

```
[协议头部 16字节] [ASDU数据 N字节]
```

### 3.2 协议头部结构

协议头部固定为16字节，结构如下：

| 偏移 | 字段名 | 长度 | 字节序 | 说明 | 示例值 |
|------|--------|------|--------|------|--------|
| 0-3 | 同步字符 | 4 | - | 固定值：`0xEB 0x91 0xEB 0x90` | `EB 91 EB 90` |
| 4-5 | ASDU长度 | 2 | 小端 | ASDU数据字节数（不含头部） | `00 48` (72字节) |
| 6-7 | 报文ID | 2 | 小端 | 唯一标识报文，建议递增使用 | `00 01` |
| 8 | 格式类型 | 1 | - | `0x00`=XML, `0x01`=JSON | `00` 或 `01` |
| 9-15 | 预留 | 7 | - | 全部填`0x00` | `00 00 00 00 00 00 00` |

#### 3.2.1 同步字符

固定4字节：`0xEB 0x91 0xEB 0x90`

用于标识报文的开始，服务器会校验此字段。

#### 3.2.2 ASDU长度

2字节，小端字节序，表示ASDU数据的字节数。

**示例**：
- ASDU长度为72字节：`48 00`（小端表示）
- ASDU长度为256字节：`00 01`（小端表示）

#### 3.2.3 报文ID

2字节，小端字节序，用于唯一标识每个报文。

建议客户端从0开始递增使用，可以循环使用（0-65535）。

#### 3.2.4 格式类型

1字节，标识ASDU数据的格式：
- `0x00`: XML格式
- `0x01`: JSON格式

响应格式将与请求格式保持一致。

#### 3.2.5 协议头部示例

```
EB 91 EB 90    // 同步字符
48 00          // ASDU长度：72字节（小端）
01 00          // 报文ID：1（小端）
01             // 格式类型：JSON (0x01)
00 00 00 00 00 00 00  // 预留字节
```

---

## 4. 数据格式

### 4.1 ASDU结构

ASDU（应用服务数据单元）包含以下字段：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Type | int | 是 | 消息类型（1001=报警器，1002=辐射传感器，1003=状态查询） |
| Command | int | 是 | 命令码（具体命令见下文） |
| Time | string | 是 | 时间戳，格式：`YYYY-MM-DD HH:MM:SS` |
| Items | object | 是 | 附加参数对象（可为空） |

### 4.2 JSON格式

**请求示例**：
```json
{
    "Type": 1001,
    "Command": 1,
    "Time": "2025-10-31 18:48:33",
    "Items": {
        "folder": 49,
        "file": 2
    }
}
```

**响应示例**：
```json
{
    "status": "success",
    "message": "播放音乐: 文件夹49, 文件2",
    "result": true
}
```

### 4.3 XML格式

**请求示例**：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
    <Type>1001</Type>
    <Command>1</Command>
    <Time>2025-10-31 18:48:33</Time>
    <Items>
        <folder>49</folder>
        <file>2</file>
    </Items>
</PatrolDevice>
```

**响应示例**：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <status>success</status>
    <message>播放音乐: 文件夹49, 文件2</message>
    <result>True</result>
</Response>
```

---

## 5. 消息类型与命令码

### 5.1 消息类型（Type）

| Type值 | 名称 | 说明 |
|--------|------|------|
| 1001 | ALARM_CONTROL | 报警器控制 |
| 1002 | RADIATION_SENSOR | 辐射传感器控制 |
| 1003 | STATUS_QUERY | 状态查询 |

### 5.2 报警器控制命令（Type=1001）

| Command值 | 名称 | Items参数 | 说明 |
|-----------|------|-----------|------|
| 1 | PLAY_MUSIC | folder, file | 播放指定音乐 |
| 2 | PREV_TRACK | - | 上一曲 |
| 3 | NEXT_TRACK | - | 下一曲 |
| 4 | VOLUME_UP | - | 音量+ |
| 5 | VOLUME_DOWN | - | 音量- |
| 6 | SET_VOLUME | volume | 设置音量（0-100） |
| 7 | PAUSE | - | 暂停播放 |
| 8 | RESUME | - | 继续播放 |
| 9 | STOP | - | 停止播放 |
| 10 | SET_ALARM_LIGHT | color, freq | 设置警灯（颜色、频率） |
| 11 | QUERY_STATUS | - | 查询报警器状态 |
| 12 | CIRCLE_MUSIC | - | 循环播放音乐 |

### 5.3 辐射传感器命令（Type=1002）

| Command值 | 名称 | Items参数 | 说明 |
|-----------|------|-----------|------|
| 1 | GET_DOSE_RATE | - | 获取剂量率（单次） |
| 2 | START_STREAM | - | 开始1Hz推送剂量率 |
| 3 | STOP_STREAM | - | 停止推送 |

### 5.4 状态查询（Type=1003）

| Command值 | 说明 |
|-----------|------|
| 0 | 查询所有设备状态 |

---

## 6. 接口详细说明

### 6.1 报警器控制接口

#### 6.1.1 播放指定音乐

**请求**：
```json
{
    "Type": 1001,
    "Command": 1,
    "Time": "2025-10-31 18:48:33",
    "Items": {
        "folder": 49,
        "file": 2
    }
}
```

**响应**：
```json
{
    "status": "success",
    "message": "播放音乐: 文件夹49, 文件2",
    "result": true
}
```

#### 6.1.2 设置音量

**请求**：
```json
{
    "Type": 1001,
    "Command": 6,
    "Time": "2025-10-31 18:48:33",
    "Items": {
        "volume": 50
    }
}
```

**响应**：
```json
{
    "status": "success",
    "message": "设置音量为: 50",
    "result": true
}
```

#### 6.1.3 设置警灯

**请求**：
```json
{
    "Type": 1001,
    "Command": 10,
    "Time": "2025-10-31 18:48:33",
    "Items": {
        "color": 5,
        "freq": 3
    }
}
```

**响应**：
```json
{
    "status": "success",
    "message": "设置警灯: 颜色5, 频率3",
    "result": true
}
```

### 6.2 辐射传感器接口

#### 6.2.1 获取剂量率（单次）

**请求**：
```json
{
    "Type": 1002,
    "Command": 1,
    "Time": "2025-10-31 18:48:33",
    "Items": {}
}
```

**响应**：
```json
{
    "status": "success",
    "message": "获取剂量率成功",
    "dose_rate": 0.17,
    "unit": "μSv/h",
    "timestamp": "2025-10-31 18:48:38"
}
```

#### 6.2.2 开始1Hz推送

**请求**：
```json
{
    "Type": 1002,
    "Command": 2,
    "Time": "2025-10-31 18:48:33",
    "Items": {}
}
```

**响应**：
```json
{
    "status": "success",
    "message": "开始1Hz推送剂量率数据"
}
```

**推送数据**（每秒一次）：
```json
{
    "status": "stream",
    "dose_rate": 0.17,
    "unit": "μSv/h",
    "timestamp": "2025-10-31 18:48:34"
}
```

#### 6.2.3 停止推送

**请求**：
```json
{
    "Type": 1002,
    "Command": 3,
    "Time": "2025-10-31 18:48:33",
    "Items": {}
}
```

**响应**：
```json
{
    "status": "success",
    "message": "停止推送"
}
```

### 6.3 状态查询接口

**请求**：
```json
{
    "Type": 1003,
    "Command": 0,
    "Time": "2025-10-31 18:48:33",
    "Items": {}
}
```

**响应**：
```json
{
    "alarm_state": false,
    "current_volume": 30,
    "current_track": 1,
    "is_playing": false,
    "timestamp": "2025-10-31 18:48:33"
}
```

---

## 7. 错误处理

### 7.1 错误响应格式

所有错误响应遵循以下格式：

```json
{
    "status": "error",
    "message": "错误描述信息"
}
```

### 7.2 常见错误码

| 错误情况 | 响应消息 |
|---------|---------|
| 协议头部错误 | `"协议头部长度错误"` 或 `"同步字符错误"` |
| ASDU格式错误 | `"ASDU解析错误"` |
| 不支持的消息类型 | `"不支持的消息类型: {type}"` |
| 无效的命令码 | `"无效的报警器命令: {command}"` 或 `"无效的辐射传感器命令: {command}"` |
| 设备控制失败 | `"报警器控制失败"` 或 `"获取剂量率失败"` |
| 网络错误 | `"连接已断开"` 或 `"请求处理错误: {error}"` |

### 7.3 错误处理示例

**请求格式错误**：
```json
{
    "status": "error",
    "message": "ASDU解析错误: Invalid JSON"
}
```

**命令执行失败**：
```json
{
    "status": "error",
    "message": "获取剂量率失败"
}
```

---

## 8. 开发示例

### 8.1 Python示例（JSON格式）

```python
import socket
import struct
import json
from datetime import datetime

class TCPClient:
    def __init__(self, host='10.21.31.104', port=8888):
        self.host = host
        self.port = port
        self.sock = None
        self.message_id = 0
        self.sync_bytes = bytes([0xEB, 0x91, 0xEB, 0x90])
    
    def connect(self):
        """连接服务器"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"已连接到 {self.host}:{self.port}")
    
    def disconnect(self):
        """断开连接"""
        if self.sock:
            self.sock.close()
            print("已断开连接")
    
    def build_header(self, asdu_length, format_type=0x01):
        """构建协议头部"""
        header = bytearray(16)
        
        # 同步字符
        header[0:4] = self.sync_bytes
        
        # ASDU长度（小端）
        header[4:6] = struct.pack('<H', asdu_length)
        
        # 报文ID（小端）
        header[6:8] = struct.pack('<H', self.message_id)
        
        # 格式类型
        header[8] = format_type
        
        # 预留字节
        header[9:16] = b'\x00' * 7
        
        self.message_id = (self.message_id + 1) % 65536
        return bytes(header)
    
    def send_request(self, msg_type, command, items=None, format_type=0x01):
        """发送请求并接收响应"""
        if items is None:
            items = {}
        
        # 构建ASDU
        asdu_data = {
            "Type": msg_type,
            "Command": command,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Items": items
        }
        
        if format_type == 0x01:  # JSON
            asdu_bytes = json.dumps(asdu_data, ensure_ascii=False).encode('utf-8')
        else:  # XML（需要实现XML构建）
            raise ValueError("XML格式暂未实现")
        
        # 构建完整请求
        header = self.build_header(len(asdu_bytes), format_type)
        request = header + asdu_bytes
        
        # 发送请求
        self.sock.send(request)
        print(f"发送请求: Type={msg_type}, Command={command}")
        
        # 接收响应头部
        response_header = self.recv_exact(16)
        header_info = self.parse_header(response_header)
        
        # 接收响应ASDU
        response_asdu = self.recv_exact(header_info['asdu_length'])
        
        # 解析响应
        if header_info['format_type'] == 0x01:
            response = json.loads(response_asdu.decode('utf-8'))
        else:
            # XML解析（需要实现）
            raise ValueError("XML格式暂未实现")
        
        return response
    
    def recv_exact(self, length):
        """精确接收指定长度的数据"""
        data = b''
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("连接已断开")
            data += chunk
        return data
    
    def parse_header(self, header):
        """解析协议头部"""
        if len(header) != 16:
            raise ValueError("协议头部长度错误")
        
        sync = header[0:4]
        if sync != self.sync_bytes:
            raise ValueError("同步字符错误")
        
        asdu_length = struct.unpack('<H', header[4:6])[0]
        message_id = struct.unpack('<H', header[6:8])[0]
        format_type = header[8]
        
        return {
            'asdu_length': asdu_length,
            'message_id': message_id,
            'format_type': format_type
        }

# 使用示例
if __name__ == '__main__':
    client = TCPClient()
    client.connect()
    
    try:
        # 播放音乐
        response = client.send_request(1001, 1, {"folder": 49, "file": 2})
        print(f"响应: {response}")
        
        # 获取剂量率
        response = client.send_request(1002, 1)
        print(f"剂量率: {response}")
        
        # 查询状态
        response = client.send_request(1003, 0)
        print(f"状态: {response}")
        
    finally:
        client.disconnect()
```

### 8.2 1Hz推送接收示例

```python
import socket
import struct
import json
import threading

class StreamReceiver:
    def __init__(self, client):
        self.client = client
        self.streaming = False
        self.thread = None
    
    def start_stream(self):
        """开始接收推送"""
        # 发送开始推送命令
        response = self.client.send_request(1002, 2)
        if response.get('status') == 'success':
            self.streaming = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            print("开始接收推送数据")
    
    def stop_stream(self):
        """停止接收推送"""
        self.streaming = False
        response = self.client.send_request(1002, 3)
        print("停止推送")
    
    def _receive_loop(self):
        """接收循环"""
        while self.streaming:
            try:
                # 接收响应头部
                header = self.client.recv_exact(16)
                header_info = self.client.parse_header(header)
                
                # 接收响应ASDU
                asdu = self.client.recv_exact(header_info['asdu_length'])
                
                # 解析数据
                data = json.loads(asdu.decode('utf-8'))
                
                if data.get('status') == 'stream':
                    print(f"剂量率: {data.get('dose_rate')} {data.get('unit')} - {data.get('timestamp')}")
            except Exception as e:
                print(f"接收错误: {e}")
                break

# 使用示例
client = TCPClient()
client.connect()

receiver = StreamReceiver(client)
receiver.start_stream()

import time
time.sleep(10)  # 接收10秒

receiver.stop_stream()
client.disconnect()
```

### 8.3 C++示例（JSON格式）

```cpp
#include <iostream>
#include <string>
#include <sstream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <json/json.h>

class TCPClient {
private:
    int sock;
    uint16_t message_id;
    const uint8_t sync_bytes[4] = {0xEB, 0x91, 0xEB, 0x90};
    
    std::vector<uint8_t> build_header(uint16_t asdu_length, uint8_t format_type) {
        std::vector<uint8_t> header(16, 0);
        
        // 同步字符
        memcpy(&header[0], sync_bytes, 4);
        
        // ASDU长度（小端）
        header[4] = asdu_length & 0xFF;
        header[5] = (asdu_length >> 8) & 0xFF;
        
        // 报文ID（小端）
        header[6] = message_id & 0xFF;
        header[7] = (message_id >> 8) & 0xFF;
        
        // 格式类型
        header[8] = format_type;
        
        message_id = (message_id + 1) % 65536;
        return header;
    }
    
    std::vector<uint8_t> recv_exact(size_t length) {
        std::vector<uint8_t> data(length);
        size_t received = 0;
        while (received < length) {
            ssize_t n = recv(sock, &data[received], length - received, 0);
            if (n <= 0) {
                throw std::runtime_error("接收数据失败");
            }
            received += n;
        }
        return data;
    }

public:
    TCPClient() : message_id(0), sock(-1) {}
    
    void connect(const std::string& host, int port) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            throw std::runtime_error("创建socket失败");
        }
        
        sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(port);
        inet_pton(AF_INET, host.c_str(), &server_addr.sin_addr);
        
        if (::connect(sock, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            throw std::runtime_error("连接失败");
        }
    }
    
    Json::Value send_request(int type, int command, Json::Value items = Json::Value()) {
        // 构建ASDU
        Json::Value asdu;
        asdu["Type"] = type;
        asdu["Command"] = command;
        
        // 时间戳（简化示例）
        asdu["Time"] = "2025-10-31 18:48:33";
        asdu["Items"] = items;
        
        // 转换为JSON字符串
        Json::StreamWriterBuilder builder;
        std::string json_str = Json::writeString(builder, asdu);
        
        // 构建请求
        std::vector<uint8_t> header = build_header(json_str.length(), 0x01);
        std::vector<uint8_t> request(header.begin(), header.end());
        request.insert(request.end(), json_str.begin(), json_str.end());
        
        // 发送请求
        send(sock, request.data(), request.size(), 0);
        
        // 接收响应
        std::vector<uint8_t> resp_header = recv_exact(16);
        uint16_t asdu_length = resp_header[4] | (resp_header[5] << 8);
        std::vector<uint8_t> resp_asdu = recv_exact(asdu_length);
        
        // 解析响应
        std::string resp_str(resp_asdu.begin(), resp_asdu.end());
        Json::Value response;
        Json::Reader reader;
        reader.parse(resp_str, response);
        
        return response;
    }
    
    ~TCPClient() {
        if (sock >= 0) {
            close(sock);
        }
    }
};

// 使用示例
int main() {
    TCPClient client;
    client.connect("10.21.31.104", 8888);
    
    // 播放音乐
    Json::Value items;
    items["folder"] = 49;
    items["file"] = 2;
    Json::Value response = client.send_request(1001, 1, items);
    std::cout << "响应: " << response << std::endl;
    
    return 0;
}
```

---

## 9. 注意事项

### 9.1 字节序

所有多字节数值字段使用**小端字节序**（Little Endian）：
- ASDU长度（2字节）
- 报文ID（2字节）

### 9.2 字符编码

所有字符串数据使用**UTF-8编码**。

### 9.3 连接管理

- 建议为每个请求维护独立的连接，或使用连接池
- 1Hz推送功能会占用连接，推送期间请保持连接
- 连接断开后推送会自动停止

### 9.4 超时设置

- **连接超时**: 建议5秒
- **读取超时**: 建议30秒（推送模式除外）
- **写入超时**: 建议5秒

### 9.5 错误重试

- 网络错误建议重试3次，间隔1秒
- 协议错误不建议重试，应检查代码
- 设备控制失败可以重试1-2次

### 9.6 性能建议

- 避免频繁建立连接，使用连接池
- 批量操作时使用多个连接并发
- 1Hz推送期间避免发送其他命令

### 9.7 安全建议

- 生产环境建议添加身份认证
- 建议使用TLS加密传输
- 限制连接频率防止DOS攻击

---

## 附录

### A. 完整请求示例

**播放音乐（JSON格式）**：

```
协议头部（16字节）:
EB 91 EB 90 48 00 01 00 01 00 00 00 00 00 00 00

ASDU（JSON格式，72字节）:
{"Type":1001,"Command":1,"Time":"2025-10-31 18:48:33","Items":{"folder":49,"file":2}}
```

### B. 完整响应示例

**播放音乐响应（JSON格式）**：

```
协议头部（16字节）:
EB 91 EB 90 3C 00 01 00 01 00 00 00 00 00 00 00

ASDU（JSON格式，60字节）:
{"status":"success","message":"播放音乐: 文件夹49, 文件2","result":true}
```

### C. 联系信息

如有问题或需要技术支持，请联系开发团队。

---

**文档结束**
