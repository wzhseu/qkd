# 导入socket模块和struct模块
import socket


# 创建一个socket对象
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到云服务器的IP和端口
client.connect(('106.13.160.91', 8080))

# 根据需要发送字符消息或文件
while True:
    
    # 接收数据，并获取数据类型和数据内容（假设最多接收1024字节）
    data = client.recv(1024)
    if data: # 如果不为空，表示有数据
        content = data # 解包得到类型和内容
        msg = content.decode('utf-8') # 将内容解码成字符串
        print('接收到来自%s的字符消息：%s' % (client.getpeername(), msg)) # 打印消息
    
    # 输入要发送的类型，0表示字符消息，1表示文件
    # 发送字符消息
    msg = 'hello 222'
    # 将类型和消息打包成一个字节串
    data = msg.encode('utf-8')
    # 发送打包后的字节串
    client.send(data)
    client.close()
    break
 