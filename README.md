# 启用顺序与操作（云服务器 → 网关 → 接收端 → 发射端）
## 0.配置ip地址
- 在config.ini中修改ip，注意发射端、接收端、云服务器ip

## 1. 先启动云服务器（qkd_center-master）
- 在云服务器主机上启动云端服务（示例命令，按你实际项目调整）：
```bash
# 进入云服务器工程目录
cd .../项目代码原版/qkd_center-master
# 启动多设备通信中心（设备接入端口 8080，管理界面 8088）
python3 run_communication_center.py

# 以下日志服务按需继续分别启动
python3 qkd_server_device.py
python3 qkd_server_catchkey1.py
```
- 打开管理界面 `http://云服务器IP:8088` 可查看所有接入设备，并选择任意两台在线设备建立通信。
- 保证云端端口开放并监听（设备通信 8080、管理界面 8088、日志端口例如 800x/801x，视你实际脚本而定）。

## 2. 再启动边缘网关（my_quantum-master）
- 在发射端和接收端网关主机上分别启动网关服务：
```bash
cd .../项目代码原版/my_quantum-master
# 建议使用虚拟环境（如有）后再启动
python3 run_gateway.py
```
- 确认网关与云端互通，能获取/管理密钥，内含密钥数据库。

## 3. 启动接收端（car_frontend-master）
- 在接收端主机上运行视频接收脚本（建议先启动接收端让其监听端口 8081）：
```bash
cd .../项目代码原版/car_frontend-master
#先构建前端
cd /fronted
npm run build
#再运行后端
cd /backend/app
flask run
```


## 4. 最后启动发射端（car_frontend-send-master）
- 在发射端主机上运行视频发送脚本，连接到接收端 IP 的 8081：
```bash
操作同上
```
-  成功打开网页后，也需要接收端先进行操作

## 5. C/D 普通 IoT 通信演示（不含量子密钥）
- 先保持云端多设备通信中心运行：
```bash
cd .../项目代码原版/qkd_center-master
python3 run_communication_center.py
```
- 启动 C 端：
```bash
cd .../项目代码原版/iot_device_c_demo
python3 app.py
```
浏览器打开 `http://localhost:5202`。
- 启动 D 端：
```bash
cd .../项目代码原版/iot_device_d_demo
python3 app.py
```
浏览器打开 `http://localhost:5203`。
- 在 C、D 页面分别点击“接入”。此时两端都能在云端管理界面看到，但未配对时发送消息会被服务器丢弃。
- 打开云端管理界面 `http://云服务器IP:8088`，选择 `car-c` 与 `car-d` 建立通信。配对后 C、D 两端即可互发普通文本消息。

## 重要提示
- 启动顺序务必遵循：云服务器 → 网关 → 接收端 → 发射端。
- 端口/IP 要一致：接收端监听 8081；发射端连接接收端的 8081。
- 两端密钥文件 `catch_q_key.txt` 的第一行必须是同一串 64 位十六进制字符串（32字节），且一致。
- 摄像头：内置通常是 `/dev/video0`，外接是 `/dev/video1`/`/dev/video2`；必要时在发送端调整摄像头索引或使用自动探测。
- 常用排查：
  - 无响应：检查端口一致并确保接收端已先启动；用 `ping`/`nc` 验证网络与端口。
  - 解密失败：检查两端密钥文件是否相同且格式正确。
  - 摄像头读取失败：检查权限（video 组）、设备占用与 USB 带宽。
