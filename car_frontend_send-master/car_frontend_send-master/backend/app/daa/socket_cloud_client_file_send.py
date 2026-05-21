# 导入socket模块和struct模块
import socket
import struct
import os

filepath = 'test.txt'

# 创建一个socket对象
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到云服务器的IP和端口
client.connect(('106.13.160.91', 8080))

# 根据需要发送字符消息或文件
while True:

    # filepath = input('please input file path: ')
    if os.path.isfile(filepath):
        # 定义定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小
        fileinfo_size = struct.calcsize('128sl')
        # 定义文件头信息，包含文件名和文件大小
        fhead = struct.pack('128sl', bytes(os.path.basename(filepath),'utf-8'),
                            os.stat(filepath).st_size)
        client.send(fhead)
        print ('client filepath: {0}'.format(filepath))

        fp = open(filepath, 'rb')
        while 1:
            data = fp.read(1024)
            if not data:
                print ('{0} file send over...'.format(filepath))
                break
            client.send(data)
        break
    client.close()