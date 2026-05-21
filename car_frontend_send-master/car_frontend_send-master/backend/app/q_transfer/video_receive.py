#接收端
import socket
import threading
import time
import sys
import os
import struct
import hashlib
# from Cryptodome.Cipher import AES  # Cryptodome is not useful in Ubuntu, change into Crypto
from Crypto.Cipher import AES
import operator                     # 导入 operator，用于比较原始数据与加解密后的数据
myfname="q_transfer/key.enc"
AES_BLOCK_SIZE = AES.block_size     # AES 加密数据块大小, 只能是16
AES_KEY_SIZE = 16                   # AES 密钥长度（单位字节），可选 16、24、32，对应 128、192、256 位密钥
with open(myfname,"rb") as fd:                   # 打开二进制文件
    key=fd.read() 
               # AES 加解密密钥
ip_port =("192.168.201.131", 8008)#定义监听地址和端口

def PadTest(bytes):
    while len(bytes) % AES_BLOCK_SIZE != 0:     # 循环直到补齐 AES_BLOCK_SIZE 的倍数
        bytes += ' '.encode()                   # 通过补空格（不影响源文件的可读）来补齐
    return bytes                                # 返回补齐后的字节列表

# 待加密的密钥补齐到对应的位数
def PadKey(key):
    if len(key) > AES_KEY_SIZE:                 # 如果密钥长度超过 AES_KEY_SIZE
        return key[:AES_KEY_SIZE]               # 截取前面部分作为密钥并返回
    while len(key) % AES_KEY_SIZE != 0:         # 不到 AES_KEY_SIZE 长度则补齐
        key += ' '.encode()                     # 补齐的字符可用任意字符代替

def socket_service():
    try:
        #定义socket连接对象
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #解决端口重用问题
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind(ip_port)#绑定地址
        s.listen(5)#等待最大客户数
    except socket.error as msg:
        print(msg)#输出错误信息
        exit(1)
    print('监听开始...')

    # Previously XZY used thread, but it seems not necessary... 2021.3.28

    # while 1:
    #     conn, addr = s.accept()#等待连接
    #     #多线程开启
    #     t = threading.Thread(target=deal_data, args=(conn, addr))
    #     t.start()

    conn, addr = s.accept() #等待连接
    res = deal_data(conn,addr)
    if (res):
        return True


# AES 解密
def DeCrypt(key, encryptData):
    myCipher = AES.new(key, AES.MODE_ECB)       # 新建一个 AES 算法实例，使用 ECB（电子密码本）模式
    bytes = myCipher.decrypt(encryptData)       # 调用解密方法，得到解密后的数据
    return bytes                                # 返回解密数据

def deal_data(conn,addr):
    print('接收的文件来自{0}'.format(addr))
    #conn.send('欢迎连接服务器'.encode('utf-8'))

    while True:
        fileinfo_size =struct.calcsize('128sq')
        print(fileinfo_size)
        #接收文件
        buf =conn.recv(fileinfo_size)
        print(buf)
        if buf:
            filename, filesize = struct.unpack('128sq',buf)
            fn = filename.strip('\00'.encode('utf-8'))
            new_filename = os.path.join('./'.encode('utf-8'),'new_'.encode('utf-8')+fn)
            print('文件的新名字是{0}，文件的大小为{1}'.format(new_filename,filesize))


            recvd_size = 0
            m = hashlib.md5()

            fp = open(new_filename,'wb')
            print('开始接收文件...')

            while recvd_size < filesize:
                if filesize - recvd_size > 1024:
                     data = conn.recv(1024)
                     recvd_size += len(data)
                else:
                     data = conn.recv(filesize-recvd_size)#最后一次接收
                     recvd_size += len(data)
                print('已接收：',int(recvd_size/filesize*100),'%')
                m.update(data)

                fp.write(data)#写入文件
            fp.close()

            md5_client = conn.recv(1024).decode('utf-8')
            md5_server = m.hexdigest()
          #  print("服务器发来的md5:", md5_server)
          #  print("接收文件的md5:", md5_client)
            #md5进行校验
            if md5_client == md5_server:
                print('接收完毕，MD5校验成功...')
            else:
                print('MD5验证失败')
        with open(new_filename,"rb") as fd:                   # 打开二进制文件
            encryptTest=fd.read()
        encryptTest = PadTest(encryptTest)
        key = PadKey(key)
        decryptTest = DeCrypt(key, encryptTest)
        with open('result.mp4', 'wb') as f:          # 以二进制模式打开文件
            f.write(decryptTest) 
        print('Done!')
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
        return True
        break

if __name__=='__main__':
    socket_service()
