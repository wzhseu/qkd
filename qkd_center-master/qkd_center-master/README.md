# README

## 多设备通信中心

使用 `run_communication_center.py` 启动服务器端多设备通信中心：

```bash
python3 run_communication_center.py
```

启动后：

- 设备/DAA 转发端口：`8080`
- Web 管理界面：`http://localhost:8088`
- API：`/api/devices`、`/api/sessions`、`/api/logs`

A/B 小车连接 `8080` 后会注册为 `car-a`、`car-b`，服务器默认在两车都在线时自动配对，以兼容原 A/B 演示流程。

## 一键启动三个日志监听端口

使用 `run_log_listeners.py` 同时监听原有三个日志端口：

```bash
python3 run_log_listeners.py
```

启动后：

- `8000`：终端运行日志，写入 `log.txt`
- `8001`：量子密钥提取日志 1，写入 `log2.txt`
- `8002`：量子密钥提取日志 2，写入 `log3.txt`

如果需要绑定指定 IP，可以使用：

```bash
python3 run_log_listeners.py --host 10.38.174.164
```

## C/D 普通通信演示

启动 C 端：

```bash
cd ../../iot_device_c_demo
python3 app.py
```

启动 D 端：

```bash
cd ../../iot_device_d_demo
python3 app.py
```

C 端页面默认 `http://localhost:5202`，D 端页面默认 `http://localhost:5203`。两端接入后，先在管理界面中选择 `car-c` 与 `car-d` 建立会话，再进行文本通信。


### 鍘熸湁鏃ュ織鎺ユ敹鏈嶅姟

1. 杩愯`qkd_server_catchkey.py` 鐢熸垚鏃ュ織鍦╨og2.txt涓細鐢ㄤ簬鎺ユ敹閲忓瓙瀵嗛挜鎻愬彇閫熺巼

2. 杩愯`qkd_server_device.py` 鐢熸垚鏃ュ織鍦╨og.txt涓細鐢ㄤ簬鎺ユ敹缁堢杩愯鏃ュ織

3. 杩愯`socket_server_cloud.py` 锛氱敤浜庢帴鏀朵袱缁堢涔嬮棿浜ゆ崲鐨勮韩浠藉嚟璇?

涓婅堪涓変釜绋嬪簭蹇呴』閮藉湪缁堢鎵撳紑杩愯鎵嶈兘鎺ユ敹鎴愬姛

闇€淇敼锛?

鍦╭kd_server_catchkey.py鍜宷kd_server_device.py涓慨鏀?

```
server = ThreadingTCPServer(('172锛?6锛?2锛?', 8000), Handler)
```

淇敼涓洪噺瀛愬瘑閽ョ鐞嗕腑蹇冧富鏈虹殑鍏綉ip鍦板潃锛堝凡閰嶇疆濂斤級
