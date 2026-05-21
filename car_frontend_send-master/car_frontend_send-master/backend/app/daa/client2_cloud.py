import socket
import time

client = socket.socket()
def connect_server():
    while True:
        try:
            client.connect(('106.13.160.91', 8080))  # 106.13.47.79   localhost
            break
        except Exception  as e:
            time.sleep(1)
            print("服务器没开", e)
    client.send('AT+TX2start'.encode("utf-8"))
    print("等待PC连接中...")
connect_server()
data = client.recv(1024).strip()  # 设置收多少字节
if data.decode("utf-8")=='PCready':
    print("开始发送...")
    send_num=0
    while True:
        try:
            send_str='TX2test: %s'%(str(send_num))
            client.send(send_str.encode("utf-8"))      #转二进制并发送
            print("send:",send_str)
            receved_string = client.recv(1024).decode("utf-8")     #设置收多少字节  接收带数据会收到  ok
            #print("recv:",receved_string)

            if receved_string == 'AT+disconnect':
                while  True:
                    client.send('AT+TX2start'.encode("utf-8"))
                    print("等待PC连接中...")
                    data = client.recv(1024).strip()  # 设置收多少字节
                    if data.decode("utf-8") == 'PCready':
                        print("开始发送...")
                        send_num = 0
                        break

            time.sleep(1)
            send_num=send_num+1
        except Exception  as e:
            print("出错:", e)
            client.send('AT+TX2start'.encode("utf-8"))
            print("等待PC连接中...")
            data = client.recv(1024).strip()  # 设置收多少字节
            print("error:",data)
            if data.decode("utf-8") == 'PCready':
                while  True:
                    client.send('AT+TX2start'.encode("utf-8"))
                    print("等待PC连接中...")
                    data = client.recv(1024).strip()  # 设置收多少字节
                    if data.decode("utf-8") == 'PCready':
                        print("开始发送...")
                        send_num = 0
                        break