# 导入socket模块和struct模块
import socket
import struct
import os

filepath = ''

# 创建一个socket对象
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到云服务器的IP和端口
client.connect(('106.13.160.91', 8080))

print("recv start...")

# 根据需要发送字符消息或文件
while True:    
    fileinfo_size = struct.calcsize('128sl')
    buf = client.recv(1024)
    print("buf:", buf)
    if buf:
        filename, filesize = struct.unpack('128sl', buf)
        filename = str(filename, 'utf-8')
        print(filename)
        print(filesize)
        fn = (str(filename)).strip('\00')
        #new_filename = os.path.join('./', 'new_' + fn)
        new_filename = os.path.join('', 'new_' + fn)
        print('file new name is {0}, filesize if {1}'.format(new_filename,
                                                                filesize))

        recvd_size = 0  # 定义已接收文件的大小
        fp = open(filepath + new_filename, 'wb')
        print('start receiving...')

        while not recvd_size == filesize:
            if filesize - recvd_size > 1024:
                data = client.recv(1024)
                recvd_size += len(data)
            else:
                data = client.recv(filesize - recvd_size)
                recvd_size = filesize
            fp.write(data)
        fp.close()
        print('end receive...')
        break