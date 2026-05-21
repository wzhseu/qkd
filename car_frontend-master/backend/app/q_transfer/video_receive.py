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
# 导入上面封装好的日志输出
from app.logging_demo import logging_
import operator                     # 导入 operator，用于比较原始数据与加解密后的数据
import configparser

cfg = configparser.ConfigParser()
cfg.read('config.ini')
cloud_ip = cfg.get('constants', 'cloud_ip')
to_ip = cfg.get('constants', 'to_ip')
local_ip = cfg.get('constants', 'local_ip')
local127_ip = cfg.get('constants', 'local127_ip')

#### ip data ####
# local_ip = '121.248.54.244'
# to_ip = '121.248.49.100'
# cloud_ip = '121.248.55.231'
port_num = 8083
# msg_port = 8082

_path = os.path.dirname(__file__) # 获取当前文件路径
print(_path)
lg = logging_(_path).logger # 实例化类

# myfname="q_transfer/key.enc"
target_filepath = 'q_transfer/result.mp4'
AES_BLOCK_SIZE = AES.block_size     # AES 加密数据块大小, 只能是16
AES_KEY_SIZE = 32                   # AES 密钥长度（单位字节），可选 16、24、32，对应 128、192、256 位密钥





# with open("video_conn/q_key.txt","r") as f:
#     rec = f.readline().strip()
#     # key = int(rec,16).to_bytes(32,'big')
   

ip_port =('0.0.0.0', port_num) ######################## 定义监听地址和端口

# 读取日志并返回
def red_logs():
    log_path = f'{_path}/log.log' # 获取日志文件路径
    # print("log_path:",log_path)
    with open(log_path,'rb') as f:
        log_size = os.path.getsize(log_path) # 获取日志大小
        # print("log_size:",log_size)
        offset = -100
        # 如果文件大小为0时返回空
        if log_size == 0:
            return ''
        while True:
            # 判断offset是否大于文件字节数,是则读取所有行,并返回
            if (abs(offset) >= log_size):
                f.seek(-log_size, 2)
                data = f.readlines()
                return data
            # 游标移动倒数的字节数位置
            data = f.readlines()
            # 判断读取到的行数，如果大于1则返回最后一行，否则扩大offset
            if (len(data) > 1):
                return data
            else:
                offset *= 2

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
    return key   
def socket_service():
    try:
        # #定义socket连接对象
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # #解决端口重用问题
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind(ip_port)#绑定地址
        print("video file transfer ip_port:", ip_port)
        s.listen(5)#等待最大客户数
 
    except socket.error as msg:
        print(msg)#输出错误信息
        exit(1)
    
    

    conn, addr = s.accept() #等待连接
    res = deal_data(conn, addr )
    if (res):
        s.close()
        return True


# AES 解密
def DeCrypt(key, encryptData):
    myCipher = AES.new(key, AES.MODE_ECB)       # 新建一个 AES 算法实例，使用 ECB（电子密码本）模式
    bytes = myCipher.decrypt(encryptData)       # 调用解密方法，得到解密后的数据
    return bytes                                # 返回解密数据

def deal_data(conn,addr):
    print('接收的文件来自{0}'.format(addr))
    
    #conn.send('欢迎连接服务器'.encode('utf-8'))

    last_time = time.time()
    while True:
        fileinfo_size =struct.calcsize('128sq')
        print(fileinfo_size)
        #接收文件
        buf =conn.recv(fileinfo_size)
        print(buf)
        if buf:
            filename, filesize = struct.unpack('128sq',buf)
            fn = filename.strip('\00'.encode('utf-8'))
            new_filename = os.path.join('./q_transfer/'.encode('utf-8'),'new_'.encode('utf-8')+fn)
            print('文件的新名字是{0}，文件的大小为{1}'.format(new_filename,filesize))
      


            recvd_size = 0
            m = hashlib.md5()

            fp = open(new_filename,'wb')
            print('开始接收文件...')
            lg.info("车A开始接收文件...")

            transfer_start_time = time.time() # record the video file transfer time and rate

            while recvd_size < filesize:
                if filesize - recvd_size > 1024:
                     data = conn.recv(1024)
                     recvd_size += len(data)
                else:
                     data = conn.recv(filesize-recvd_size)#最后一次接收
                     recvd_size += len(data)
                
                if time.time() - last_time >=2:
                    msg = str(int(recvd_size/filesize*100))
                    print('已接收：',msg,'%')
                    lg.info("已接收：%s"%(msg))
                    last_time = time.time()
                m.update(data)

                fp.write(data)#写入文件
            fp.close()

            transfer_end_time = time.time()

            transfer_time = transfer_end_time - transfer_start_time
            transfer_rate = round((filesize/ 10**3 / transfer_time), 2) 

            msg = "视频文件发送速率：" + str(transfer_rate) + "kb/s"

            # # 创建一个socket对象
            # video_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # # 连接到云服务器的IP和端口
            # video_receive_socket.connect((cloud_ip, msg_port))

            print("车A发送：", msg)
            lg.info("%s"%(msg))
            # video_receive_socket.send(msg.encode('utf-8'))#将发送的数据进行编码
            # a=video_receive_socket.recv(1024)#接受服务端的信息，最大数据为1k
            # print(a.decode('utf-8'))

            md5_client = conn.recv(1024).decode('utf-8')
            md5_server = m.hexdigest()
            print("服务器发来的md5:", md5_server)
            print("接收文件的md5:", md5_client)
            #md5进行校验
            if md5_client == md5_server:
                print('接收完毕，MD5校验成功...')
                lg.info("接收完毕，MD5校验成功...")
            else:
                print('MD5验证失败')
                lg.info("MD5验证失败")
        with open(new_filename,"rb") as fd:                   # 打开二进制文件
            encryptTest=fd.read()
        encryptTest = PadTest(encryptTest)
        with open("catch_q_key.txt","rb") as fd:                   # 打开二进制文件
            key=fd.read()    # AES 加解密密钥
        key = PadKey(key)
        print("padkey:",key)
        decryptTest = DeCrypt(key, encryptTest)
        with open(target_filepath, 'wb') as f:          # 以二进制模式打开文件
            f.write(decryptTest) 
        print('视频文件接收并解密成功！')
        lg.info("视频文件接收并解密成功！")

        conn.send("file transfer over.".encode())
        conn.close()
        return True
        break

if __name__=='__main__':
    socket_service()
