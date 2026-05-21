import os
from SecretKeyUtil import SecretKeyUtil
import base64
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
#import struct

def decrypt_oralce(filelocator,mode):#解密方法
    # filelocator:文件的位置，这里是解密，所以就是待解密文件的位置
    # mode:选择加密的模式，'ECB'选择的是ECB模式加密，'CBC'选择的是CBC模式加密
    # text = str(open('sm3.sm4', 'r').read())# 密文文件
    # open('sm3.sm4', 'r').close()
    #
    # crypt_sm4 = CryptSM4()
    # key = SecretKeyUtil(os.popen('pwd').read().replace('\n', '') + '/SecretKey.txt')
    # crypt_sm4.set_key(key, SM4_DECRYPT)
    # base64_decrypted = base64.decodebytes(bytes(text.encode('cp936')))#优先逆向解密base64成bytes
    # decrypted_text = str(crypt_sm4.crypt_ecb(base64_decrypted),encoding='gbk').replace('\0','')#执行解密密并转码返回str
    # decrypted_text2 = eval(decrypted_text)
    #
    # logbat = open('recover.png', 'wb')
    # logbat.write(decrypted_text2)
    # logbat.close()
    ###### SM4对象的调用以及参数设置等
    iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'  # CBC模式的初始向量
    # key是SM4的密钥，以字节的形式送入；因为SecretKey.txt中的密钥是01比特，所以需要调用SecretKeyUtil将密钥从比特转换为字节
    key = SecretKeyUtil(os.popen('pwd').read().replace('\n', '') + '/SecretKey.txt')
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(key, SM4_DECRYPT)

    ###### 读取密文
    fp = open(filelocator, 'rb+')
    ciphertext = fp.read()
    fp.close()

    ###### SM4解密 ECB模式
    if mode == 'ECB':
        decrypted_data = crypt_sm4.crypt_ecb(ciphertext)
    else :
        decrypted_data = crypt_sm4.crypt_cbc(iv,ciphertext)
    #decrypted_text = str(crypt_sm4.crypt_ecb(ciphertext),encoding='gbk').replace('\0','')#执行解密密并转码返回str
    #decrypted_text2 = eval(decrypted_text)
    ###### 将解密结果写入到文件中
    filepath, filename = os.path.split(filelocator)  # filepath是源文件所在路径,filename是源文件的名称（包含后缀）
    if filepath == "":
        fp = open(filename.replace('.sm4',''), 'wb')
        fp.write(decrypted_data)
        fp.close()
    else:
        fp = open(filepath + '/' + filename.replace('.sm4', ''), 'wb')
        fp.write(decrypted_data)
        fp.close()

if __name__ == '__main__':
    decrypt_oralce('./quantum01.txt.sm4','CBC')