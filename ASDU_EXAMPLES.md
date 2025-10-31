# ASDU格式示例文档

## TCP服务端口号

**TCP服务端口：8888**

服务器监听地址：`0.0.0.0:8888`（监听所有网络接口）

## 协议头部结构

每个报文包含16字节的协议头部 + ASDU数据：

```
[同步字符 4字节] [ASDU长度 2字节] [报文ID 2字节] [格式类型 1字节] [预留 7字节]
```

- 同步字符：`0xeb 0x91 0xeb 0x90`（固定值）
- ASDU长度：小端字节序，表示ASDU数据的字节数
- 报文ID：小端字节序，唯一标识每个报文
- 格式类型：`0x00`表示XML，`0x01`表示JSON
- 预留字节：7字节，全部填`0x00`

## XML格式ASDU示例

### 示例1：设置警灯（报警器控制）

**完整APDU（协议头部+ASDU）：**
```
协议头部（16字节）:
EB 91 EB 90 [ASDU长度] [报文ID] 00 [预留7字节]

ASDU（XML格式，0x00）:
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1002</Type>
	<Command>10</Command>
	<Time>2023-01-01 00:00:00</Time>
	<Items>
		<color>5</color>
		<freq>3</freq>
	</Items>
</PatrolDevice>
```

**说明：**
- Type: 1002（报警器控制）
- Command: 10（设置警灯）
- Items.color: 5（颜色值）
- Items.freq: 3（频率值）

---

### 示例2：播放音乐（报警器控制）

**ASDU（XML格式）：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1002</Type>
	<Command>1</Command>
	<Time>2023-12-15 14:30:25</Time>
	<Items>
		<folder>17</folder>
		<file>1</file>
	</Items>
</PatrolDevice>
```

**说明：**
- Type: 1002（报警器控制）
- Command: 1（播放指定音乐）
- Items.folder: 17（文件夹编号，十六进制0x11）
- Items.file: 1（文件编号）

---

### 示例3：设置音量（报警器控制）

**ASDU（XML格式）：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1002</Type>
	<Command>6</Command>
	<Time>2023-12-15 14:30:25</Time>
	<Items>
		<volume>30</volume>
	</Items>
</PatrolDevice>
```

**说明：**
- Type: 1002（报警器控制）
- Command: 6（设置音量）
- Items.volume: 30（音量值，0-100）

---

### 示例4：下一曲（报警器控制）

**ASDU（XML格式）：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1002</Type>
	<Command>3</Command>
	<Time>2023-12-15 14:30:25</Time>
	<Items/>
</PatrolDevice>
```

**说明：**
- Type: 1002（报警器控制）
- Command: 3（下一曲）
- Items为空（不需要额外参数）

---

### 示例5：开启日行灯（灯光控制）

**ASDU（XML格式）：**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<PatrolDevice>
	<Type>1001</Type>
	<Command>1</Command>
	<Time>2023-12-15 14:30:25</Time>
	<Items/>
</PatrolDevice>
```

**说明：**
- Type: 1001（灯光控制）
- Command: 1（开启日行灯）
- Items为空（不需要额外参数）

---

## JSON格式ASDU示例

### 示例1：设置警灯（报警器控制）

**完整APDU（协议头部+ASDU）：**
```
协议头部（16字节）:
EB 91 EB 90 [ASDU长度] [报文ID] 01 [预留7字节]

ASDU（JSON格式，0x01）:
{"Type":1002,"Command":10,"Time":"2023-01-01 00:00:00","Items":{"color":5,"freq":3}}
```

**说明：**
- Type: 1002（报警器控制）
- Command: 10（设置警灯）
- Items.color: 5（颜色值）
- Items.freq: 3（频率值）

---

### 示例2：播放音乐（报警器控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1002,
    "Command": 1,
    "Time": "2023-12-15 14:30:25",
    "Items": {
        "folder": 17,
        "file": 1
    }
}
```

**紧凑格式：**
```json
{"Type":1002,"Command":1,"Time":"2023-12-15 14:30:25","Items":{"folder":17,"file":1}}
```

**说明：**
- Type: 1002（报警器控制）
- Command: 1（播放指定音乐）
- Items.folder: 17（文件夹编号）
- Items.file: 1（文件编号）

---

### 示例3：设置音量（报警器控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1002,
    "Command": 6,
    "Time": "2023-12-15 14:30:25",
    "Items": {
        "volume": 30
    }
}
```

**紧凑格式：**
```json
{"Type":1002,"Command":6,"Time":"2023-12-15 14:30:25","Items":{"volume":30}}
```

---

### 示例4：下一曲（报警器控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1002,
    "Command": 3,
    "Time": "2023-12-15 14:30:25",
    "Items": {}
}
```

**紧凑格式：**
```json
{"Type":1002,"Command":3,"Time":"2023-12-15 14:30:25","Items":{}}
```

---

### 示例5：暂停播放（报警器控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1002,
    "Command": 7,
    "Time": "2023-12-15 14:30:25",
    "Items": {}
}
```

**紧凑格式：**
```json
{"Type":1002,"Command":7,"Time":"2023-12-15 14:30:25","Items":{}}
```

---

### 示例6：开启日行灯（灯光控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1001,
    "Command": 1,
    "Time": "2023-12-15 14:30:25",
    "Items": {}
}
```

**紧凑格式：**
```json
{"Type":1001,"Command":1,"Time":"2023-12-15 14:30:25","Items":{}}
```

---

### 示例7：开启远光灯（灯光控制）

**ASDU（JSON格式）：**
```json
{
    "Type": 1001,
    "Command": 3,
    "Time": "2023-12-15 14:30:25",
    "Items": {}
}
```

**紧凑格式：**
```json
{"Type":1001,"Command":3,"Time":"2023-12-15 14:30:25","Items":{}}
```

---

### 示例8：状态查询

**ASDU（JSON格式）：**
```json
{
    "Type": 1003,
    "Command": 0,
    "Time": "2023-12-15 14:30:25",
    "Items": {}
}
```

**紧凑格式：**
```json
{"Type":1003,"Command":0,"Time":"2023-12-15 14:30:25","Items":{}}
```

---

## 消息类型说明

| Type值 | 说明 |
|--------|------|
| 1001 | 灯光控制 |
| 1002 | 报警器控制 |
| 1003 | 状态查询 |

## 报警器控制命令码（Command）

| Command值 | 说明 | 需要的Items参数 |
|-----------|------|----------------|
| 1 | 播放指定音乐 | folder, file |
| 2 | 上一曲 | 无 |
| 3 | 下一曲 | 无 |
| 4 | 音量+ | 无 |
| 5 | 音量- | 无 |
| 6 | 设置音量 | volume |
| 7 | 暂停 | 无 |
| 8 | 继续播放 | 无 |
| 9 | 停止 | 无 |
| 10 | 设置警灯 | color, freq |
| 11 | 查询状态 | 无 |

## 灯光控制命令码（Command）

| Command值 | 说明 |
|-----------|------|
| 1 | 开启日行灯 |
| 2 | 关闭日行灯 |
| 3 | 开启远光灯（自动关闭日行灯） |
| 4 | 关闭远光灯 |
| 5 | 开启所有灯光 |
| 6 | 关闭所有灯光 |

## 发送示例（Python代码）

### XML格式发送示例

```python
import socket
import struct
from datetime import datetime

def build_xml_request(msg_type, command, items=None):
    """构建XML格式请求"""
    if items is None:
        items = {}
    
    xml_body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_body += '<PatrolDevice>\n'
    xml_body += f'\t<Type>{msg_type}</Type>\n'
    xml_body += f'\t<Command>{command}</Command>\n'
    xml_body += f'\t<Time>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</Time>\n'
    xml_body += '\t<Items>\n'
    for key, value in items.items():
        xml_body += f'\t\t<{key}>{value}</{key}>\n'
    xml_body += '\t</Items>\n'
    xml_body += '</PatrolDevice>'
    
    return xml_body.encode('utf-8')

def send_xml_request(host, port, msg_type, command, items=None):
    """发送XML格式请求"""
    # 构建ASDU
    asdu_data = build_xml_request(msg_type, command, items)
    asdu_length = len(asdu_data)
    
    # 构建协议头部
    header = bytearray(16)
    header[0:4] = bytes([0xeb, 0x91, 0xeb, 0x90])  # 同步字符
    header[4:6] = struct.pack('<H', asdu_length)   # ASDU长度
    header[6:8] = struct.pack('<H', 1)             # 报文ID
    header[8] = 0x00                               # XML格式
    header[9:16] = b'\x00' * 7                     # 预留
    
    # 发送完整请求
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(bytes(header) + asdu_data)
    
    # 接收响应头部
    response_header = sock.recv(16)
    asdu_len = struct.unpack('<H', response_header[4:6])[0]
    
    # 接收响应ASDU
    response_asdu = sock.recv(asdu_len)
    sock.close()
    
    return response_asdu.decode('utf-8')

# 使用示例：设置警灯
response = send_xml_request('192.168.1.100', 8888, 1002, 10, {'color': 5, 'freq': 3})
print(response)
```

### JSON格式发送示例

```python
import socket
import json
import struct
from datetime import datetime

def build_json_request(msg_type, command, items=None):
    """构建JSON格式请求"""
    if items is None:
        items = {}
    
    request_data = {
        "Type": msg_type,
        "Command": command,
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Items": items
    }
    
    return json.dumps(request_data, ensure_ascii=False).encode('utf-8')

def send_json_request(host, port, msg_type, command, items=None):
    """发送JSON格式请求"""
    # 构建ASDU
    asdu_data = build_json_request(msg_type, command, items)
    asdu_length = len(asdu_data)
    
    # 构建协议头部
    header = bytearray(16)
    header[0:4] = bytes([0xeb, 0x91, 0xeb, 0x90])  # 同步字符
    header[4:6] = struct.pack('<H', asdu_length)   # ASDU长度
    header[6:8] = struct.pack('<H', 1)             # 报文ID
    header[8] = 0x01                               # JSON格式
    header[9:16] = b'\x00' * 7                     # 预留
    
    # 发送完整请求
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(bytes(header) + asdu_data)
    
    # 接收响应头部
    response_header = sock.recv(16)
    asdu_len = struct.unpack('<H', response_header[4:6])[0]
    
    # 接收响应ASDU
    response_asdu = sock.recv(asdu_len)
    sock.close()
    
    return json.loads(response_asdu.decode('utf-8'))

# 使用示例：设置警灯
response = send_json_request('192.168.1.100', 8888, 1002, 10, {'color': 5, 'freq': 3})
print(response)
```

## 注意事项

1. **字节序**：ASDU长度和报文ID使用小端字节序（Little Endian）
2. **编码格式**：XML和JSON都使用UTF-8编码
3. **时间格式**：时间字段格式为 `YYYY-MM-DD HH:MM:SS`
4. **Items为空**：当不需要参数时，XML使用`<Items/>`，JSON使用`{}`或`{"Items":{}}`
5. **报文ID**：每次发送应使用递增的报文ID（可以循环使用0-65535）
6. **连接方式**：TCP连接，端口8888，连接后发送请求，接收响应后可以保持连接继续发送，或关闭连接
