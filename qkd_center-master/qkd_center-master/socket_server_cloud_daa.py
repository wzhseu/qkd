import socket
import struct
import select

print("listening...")

# 创建一个TCP/IP套接字
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定套接字到指定的地址和端口
server.bind(('10.38.174.164', 8080))

# 监听传入连接，参数指定最大连接数
server.listen(2) # number of device

# 接受第一个客户端连接
client1, addr1 = server.accept()

print("device 1:", addr1)

# 接受第二个客户端连接
client2, addr2 = server.accept()
print("device 2:", addr2)

# 客户端列表
inputs = [client1, client2]

# 主循环，用于接收和转发数据
while True:
 data1 = client1.recv(1024)
 if data1:
  print('data from device1: ', data1.decode('utf-8'))
  client2.send(data1)
 else:
  print('device1 connection shutdown')
  break
 
 data2 = client2.recv(1024)
 if data2:  # 这里应该是 if data2:
  print('data from device2: ', data2.decode('utf-8'))
  client1.send(data2)
 else:
  print('device2 connection shutdown')
  break
  

# 关闭服务器套接字
server.close()
