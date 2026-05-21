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
    client.send('AT+PCstart'.encode("utf-8"))
    print("等待TX2连接中...")

connect_server()
data = client.recv(1024).strip()  # 设置收多少字节
if data.decode("utf-8")=='TX2ready':
    print("开始接收...")
    while True:
        receved_string= client.recv(1024).decode("utf-8")                          #设置收多少字节
        print("recv:",receved_string)
        if receved_string == 'AT+disconnect':
            client.send('AT+PCstart'.encode("utf-8"))
            print("等待TX2连接中...")
            data = client.recv(1024).strip()  # 设置收多少字节
            if data.decode("utf-8") == 'TX2ready':
                print("开始接收...")

        # f = open("test.txt", 'a', encoding="utf-8")
        # f.write(receved_string)
        # f.write("\n")
        # f.close()
client.close()