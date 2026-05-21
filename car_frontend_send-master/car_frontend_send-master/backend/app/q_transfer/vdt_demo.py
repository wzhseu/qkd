import socket
import os
import hashlib
import sys
import struct
from Crypto.Cipher import AES
import operator                     # 导入 operator，用于比较原始数据与加解密后的数据
from app.q_transfer.video_send import socket_client, PadKey, EnCrypt, PadTest

video_file_name = 'q_transfer/video.mp4'



def VDT():


    AES_BLOCK_SIZE = AES.block_size     # AES 加密数据块大小, 只能是16
    AES_KEY_SIZE = 32                   # AES 密钥长度（单位字节），可选 16、24、32，对应 128、192、256 位密钥
    with open("catch_q_key.txt","rb") as fd:                   # 打开二进制文件
        key=fd.read() 
               # AES 加解密密钥

    print("开始视频传输")
    with open(video_file_name, 'rb') as f:          # 以二进制模式打开文件
        bytes = f.read()                                # 将文件内容读取出来到字节列表中
        print('源文件长度：{}'.format(len(bytes)))
    key = PadKey(key)                          # 将密钥转换位字节列表并补齐密钥
    print("Padkey:",key)
    bytes = PadTest(bytes)                              # 补齐原始数据
    print('补齐后的源文件长度：{}'.format(len(bytes)))

    encryptTest = EnCrypt(key, bytes)   
    with open('q_transfer/en-result.mp4', 'wb') as f:          # 以二进制模式打开文件
      f.write(encryptTest) 
    en_filepath = 'q_transfer/en-result.mp4'
    res = socket_client(en_filepath)
    
    if (res):
        return True
    
