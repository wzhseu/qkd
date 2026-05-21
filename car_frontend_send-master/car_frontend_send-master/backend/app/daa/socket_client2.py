# -*- coding:utf-8 -*-
# 导入socket库
import socket


def socket_client(addr, port, mes):
    # 定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 定义IP地址与端口号
    ip_port = (addr, port)
    # 进行连接服务器
    client.connect(ip_port)
    while True:
        # message=input('You can say:')
        message = mes
        client.send(message.encode('utf-8'))  # 将发送的数据进行编码
        a = client.recv(1024)  # 接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))
        # break
        if a.decode('utf-8')=='bye':
            break
    client.close()


if __name__ == '__main__':
    socket_client(addr='127.0.0.1', port=8081, mes="hello")
