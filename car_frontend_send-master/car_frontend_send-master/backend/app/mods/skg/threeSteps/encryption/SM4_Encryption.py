import os
# import psutil
import base64
from .SecretKeyUtil import SecretKeyUtil
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT

def encrypt_oracle(filelocator,mode):#加密方法
    #filelocator:文件的位置，这里是加密，所以就是待加密文件的位置
    #mode:选择加密的模式，'ECB'选择的是ECB模式加密，'CBC'选择的是CBC模式加密
    ###### SM4对象的调用以及参数设置等
    iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'  # CBC模式的初始向量
    # key是SM4的密钥，以字节的形式送入；因为SecretKey.txt中的密钥是01比特，所以需要调用SecretKeyUtil将密钥从比特转换为字节
    # key = SecretKeyUtil(os.popen('pwd').read().replace('\n', '') + '/SecretKey.txt')
    key = SecretKeyUtil("mods/skg/threeSteps/encryption/SecretKey.txt")
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(key, SM4_ENCRYPT)

    ###### 待加密文件预处理
    fp = open(filelocator, 'rb')
    waiting_encrypted_files = fp.read()
    fp.close()
    #以二进制格式打开一个文件用于只读。文件指针将会放在文件的开头。这是默认模式。一般用于非文本文件如图片等。
    #plaintext = str(waiting_encrypted_files)

    ###### 加密
    # encrypt_sm4 = crypt_sm4.crypt_ecb(plaintext.encode('cp936'))
    if mode == 'ECB':
        encrypt_sm4 = crypt_sm4.crypt_ecb(waiting_encrypted_files)
    else:
        encrypt_sm4 = crypt_sm4.crypt_cbc(iv,waiting_encrypted_files)

    #encode函数以指定的编码格式编码字符串

    ###### 将加密结果写入到文件中
    # encrypted_text = str(base64.encodebytes(encrypt_sm4), encoding='cp936') #用base64转成字符串形式 # 执行加密并转码返回bytes
    # logbat = open('sm3.sm4', 'w')
    # logbat.write(encrypted_text)
    # logbat.close()
    filepath, filename = os.path.split(filelocator)#filepath是源文件所在路径,filename是源文件的名称（包含后缀）
    #filename, extension = os.path.splitext(filename)
    if filepath == "":
        fp = open(filename + '.sm4', 'wb+')
        fp.write(encrypt_sm4)
        fp.close()
    else:
        fp = open(filepath + '/' + filename + '.sm4', 'wb+')
        fp.write(encrypt_sm4)
        fp.close()

if __name__ == '__main__':
    encrypt_oracle('./Alice_QR.png','CBC')