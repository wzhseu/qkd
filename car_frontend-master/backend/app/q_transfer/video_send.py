#发送端
import socket
import os
import hashlib
import sys
import struct
from Crypto.Cipher import AES
import operator                     # 导入 operator，用于比较原始数据与加解密后的数据
myfname="key.enc"
AES_BLOCK_SIZE = AES.block_size     # AES 加密数据块大小, 只能是16
AES_KEY_SIZE = 16                   # AES 密钥长度（单位字节），可选 16、24、32，对应 128、192、256 位密钥
with open(myfname,"rb") as fd:                   # 打开二进制文件
    key=fd.read() 
               # AES 加解密密钥

# 待加密文本补齐到 block size 的整数倍
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
    return key                                  # 返回补齐后的密钥

# AES 加密
def EnCrypt(key, bytes):
    myCipher = AES.new(key, AES.MODE_ECB)       # 新建一个 AES 算法实例，使用 ECB（电子密码本）模式
    encryptData = myCipher.encrypt(bytes)       # 调用加密方法，得到加密后的数据
    return encryptData                          # 返回加密数据




ip_port =("192.168.201.131", 8008)#指定要发送的服务器地址和端口




def socket_client():
    try:
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#生成socket连接对象
        s.connect(ip_port)#连接
    except socket.error as msg:
        print(msg)#输出错误信息
        sys.exit(1)
    print("服务器已连接...\n")
    LEN = 0
    while 1:
        # filepath = input("please input the file path:")#输入要发送的文件的路径
        # filepath = '/home/quantum-test/code/car_frontend/backend/app/q_transfer/video.mp4'
        filepath = 'video.mp4'
        print(os.path.isfile(filepath))
        if os.path.isfile(filepath):#如果文件存在
            #定义文件信息，128sq（其中sq是在不同机器上的衡量单位）表示文件命长128byte
            fileinfo_size = struct.calcsize('128sq')
            #定义文件名和文件大小
            fhead =struct.pack('128sq',os.path.basename(filepath).encode('utf-8'),
                               os.stat(filepath).st_size)
            print(fhead)
            s.send(fhead)#发送文件名、文件大小等信息
            print('即将发送的文件的路径为：{0}\n'.format(filepath))
            LENS = os.stat(filepath).st_size#获取文件的大小
            m =hashlib.md5()
            fp =open(filepath,'rb')#读取文件
            while 1:
                data = fp.read(1024)
                m.update(data)
                data_len = len(data)
                LEN += data_len
                if not data:
                    print ('{0} 文件发送完毕...'.format(filepath))
                    break
                s.send(data)#发送文件
                # print('已发送：',int(LEN/LENS*100),'%')
            fp.close()#关闭
            md5 = m.hexdigest()#获取MD５
            s.send(md5.encode('utf-8'))#发送ｍｄ５
            print('MD5:',md5)
        s.close()
        break

if __name__=='__main__':
    with open('video.mp4', 'rb') as f:          # 以二进制模式打开文件
        bytes = f.read()                                # 将文件内容读取出来到字节列表中
        print('源文件长度：{}'.format(len(bytes)))
    key = PadKey(key)                          # 将密钥转换位字节列表并补齐密钥
    bytes = PadTest(bytes)                              # 补齐原始数据
    print('补齐后的源文件长度：{}'.format(len(bytes)))

    encryptTest = EnCrypt(key, bytes)   
    with open('en-result.mp4', 'wb') as f:          # 以二进制模式打开文件
      f.write(encryptTest) 
    socket_client()
