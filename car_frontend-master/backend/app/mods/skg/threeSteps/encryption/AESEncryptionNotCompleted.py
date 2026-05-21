import os
import time
import psutil
import base64
from Crypto.Cipher import AES
#import struct
def add_to_16(value):# str不是16的倍数那就补足为16的倍数
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回bytes
def encrypt_oracle():#加密方法
    key = input('\n请设置一个秘钥用于加密文件：')
    print('\n当被加密文件与本程序不同目录时\n请输入要加密文件完整路径包括文件名以及后缀')
    print('\n\n当被加密文件与本程序同一目录时只需输入文件名以及后缀：')
    file_path = input('\n\n请输入：')
    filepath,tempfilename = os.path.split(file_path)#filepath源文件所在路径,tempfilename源文件名称包含后缀
    filename,extension = os.path.splitext(tempfilename)#filename源文件名称不包含后缀,extension源文件后缀
    savefile = filename+'_encryption'+extension#加密后文件名称
    try:
        try:
            virtualmem = psutil.virtual_memory()#获取本机内存信息
            availablemem = round(virtualmem.available / 3)
            filesize = os.path.getsize(file_path)
            if filesize > availablemem:
                print("\n\n\n加密文件大于系统可用内存可能影响加密效率或出现内存崩溃\n\n\n")
                print('\n\n\n是否继续运行 继续操作请按"y"返回请按"n"\n\n\n')
                temp = input('\n请按键选择')
                if temp == "n" or temp == "N" :
                    encrypt_oracle()
        except:
            print('\n输入有误，请重新输入')
            encrypt_oracle()
        text = open(file_path, 'rb').read()# 待加密文本
        open(file_path, 'rb').close()
    except:
        print('\n输入有误，请重新输入')
        encrypt_oracle()
    text = str(text)
    aes = AES.new(add_to_16(key), AES.MODE_ECB)# 初始化加密器
    encrypt_aes = aes.encrypt(add_to_16(text))#先进行aes加密
    encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='cp936') #用base64转成字符串形式 # 执行加密并转码返回bytes
    if filepath == "":
        logbat = open(savefile, 'w')
        logbat.write(encrypted_text)
        logbat.close()
        print('\n文件加密成功 文件以保存为 ',savefile)
    else:
        logbat = open(filepath+'\\'+savefile, 'w')
        logbat.write(encrypted_text)
        logbat.close()
        print('\n文件加密成功 文件保存在 ',filepath,'中 \n\n文件名为 ',savefile)

if __name__ == '__main__':
    encrypt_oracle()