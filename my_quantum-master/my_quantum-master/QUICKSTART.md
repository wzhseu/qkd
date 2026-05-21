# QKD边缘网关数据库系统 - 快速开始

## 5分钟快速部署

### 步骤1: 安装依赖（1分钟）

```bash
cd /media/john/Data1/中国移动紫金创新研究院/项目代码\ \(原始代码\)/my_quantum-master
pip3 install -r requirements.txt
```

### 步骤2: 启动网关服务（1分钟）

```bash
python3 run_gateway.py
```

看到以下输出表示启动成功：
```
============================================================
  QKD边缘网关数据库系统启动
============================================================
  访问地址: http://localhost:5002
  API文档: http://localhost:5002/health
============================================================
```

### 步骤3: 访问Web界面（1分钟）

打开浏览器访问：`http://localhost:5002`

你将看到：
- 📊 实时密钥统计
- 📝 密钥列表管理
- 📈 每日趋势图表
- 📋 运行日志

### 步骤4: 启动密钥分发服务（2分钟）

**新开一个终端**，运行：

```bash
# 启动Device1密钥分发服务
python3 quantum_to_device_1_with_db.py
```

如果你有Device2，再开一个终端：

```bash
# 启动Device2密钥分发服务
python3 quantum_to_device_2_with_db.py
```

## 验证系统工作

### 1. 检查自动导入

系统会自动从 `../qkd_app_8013-master/` 目录导入密钥文件。

在Web界面的 "导入记录" 标签页查看已导入的文件。

### 2. 测试密钥获取API

```bash
# 获取统计信息
curl http://localhost:5002/api/keys/stats

# 获取最新密钥
curl -X POST http://localhost:5002/api/keys/consume/latest \
  -H "Content-Type: application/json" \
  -d '{"device": "device1"}'
```

### 3. 小车请求密钥

小车端代码不需要修改，继续使用原来的socket方式：

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("10.243.195.202", 9000))
s.send(b"get_key")
key = s.recv(1024)
print(f"Received key: {key}")
s.close()
```

边缘网关会自动从数据库获取密钥返回给小车。

## 配置说明

### 修改监控目录

编辑 `gateway_app/config.ini`：

```ini
[auto_import]
enabled = true
path = /your/custom/path    # 修改为你的密钥目录
device = device1
per_line = false
interval_sec = 5
```

重启服务生效。

### 修改Web端口

编辑 `gateway_app/config.ini`：

```ini
[server]
port = 5002    # 修改为你想要的端口
```

### 修改密钥分发服务IP和端口

编辑 `quantum_to_device_1_with_db.py`：

```python
local_ip = "10.243.195.202"   # 修改为你的边缘网关IP
port_num = 9000                # 修改为你的端口
GATEWAY_API = "http://localhost:5002"  # 修改为网关API地址
```

## 常见问题

### Q1: 端口被占用怎么办？

修改 `gateway_app/config.ini` 中的端口号，然后重启服务。

### Q2: 自动导入不工作？

1. 检查配置文件中的路径是否正确
2. 检查目录中是否有匹配的文件（outkey*.txt等）
3. 查看Web界面的"运行日志"标签页

### Q3: 小车获取不到密钥？

1. 确认网关服务正常运行：`curl http://localhost:5002/health`
2. 确认数据库中有未使用的密钥：访问Web界面查看统计
3. 确认密钥分发服务正常运行
4. 检查网络连接

### Q4: 如何查看数据库内容？

```bash
# 使用sqlite3命令行工具
cd gateway_data
sqlite3 quantum_gateway.db

# 查看密钥数量
SELECT COUNT(*) FROM keys;

# 查看未使用密钥
SELECT * FROM keys WHERE status='unused' LIMIT 10;

# 查看每日统计
SELECT * FROM key_usage_stats ORDER BY date DESC;
```

或者直接访问Web界面查看。

## 下一步

- 📖 阅读完整文档：`README_GATEWAY.md`
- 🔧 查看示例代码（参考 qkd_center-master/examples/）
- 🛠️ 创建工具脚本（参考 qkd_center-master/tools/）
- 📊 自定义前端界面

## 系统架构

```
┌─────────────────┐
│   QKD设备       │
│   生成密钥      │
└────────┬────────┘
         │
         ├─→ outkey.txt
         │
┌────────▼────────────────────────────────┐
│  边缘网关数据库系统                      │
│  ├─ 自动导入器（监控目录）               │
│  ├─ SQLite数据库（4张表）               │
│  ├─ Flask API（15+接口）                │
│  └─ Vue前端（实时监控）                 │
└────────┬────────────────────────────────┘
         │
         ├─→ HTTP API (5002端口)
         ├─→ Socket服务 (9000端口 - Device1)
         └─→ Socket服务 (9001端口 - Device2)
         │
┌────────▼────────┐
│   小车设备      │
│   请求密钥      │
└─────────────────┘
```

## 支持

如有问题，请查看：
1. Web界面的"运行日志"标签页
2. 控制台输出信息
3. 完整文档 `README_GATEWAY.md`

祝使用愉快！🎉
