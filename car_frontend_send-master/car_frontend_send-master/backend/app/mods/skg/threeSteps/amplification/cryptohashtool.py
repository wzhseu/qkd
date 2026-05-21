import sha3  #实现SHA-3系列的哈希函数
from .SM3 import sm3_hash  #实现SM3哈希函数
from hashlib import blake2b,shake_128,sha256

def StructByteStream(bitstrs):
#该函数是将保存在txt文档中协调好的密钥转换成字节流的函数
#例如，Input：协商好的密钥为"1000111101110000"
#Output：那么经过StructByteStream函数处理后的结果为b"\x8f\x70"
#该函数的作用是将保存在txt文档中的密钥转换成对应的字节流，然后作为各个哈希函数的输入，去做哈希
    if len(bitstrs)%8 !=0:
        paddings = '0'*(8-(len(bitstrs)%8))
        bitstrs +=paddings
    ByteChunks = int(len(bitstrs)/8)
    ByteStream = b''
    for i in range(0,ByteChunks):
        ByteChunkValue = 0
        ByteChunkValue = int(bitstrs[i*8])*128+int(bitstrs[i*8+1])*64+int(bitstrs[i*8+2])*32+int(bitstrs[i*8+3])*16 \
            +int(bitstrs[i*8+4])*8+int(bitstrs[i*8+5])*4+int(bitstrs[i*8+6])*2+int(bitstrs[i*8+7])
        ByteStream +=(ByteChunkValue).to_bytes(1, byteorder='big')
    return ByteStream

def Hex2Bin(hexstring):
    #哈希函数得到的摘要值是以十六进制的形式出现的
    #该函数将十六进制的摘要值转换为比特bit的形式，以供后续将比特流写入到文本中
    #bitstring = bin(int(hexstring,16))[2:]
    num_of_bits = len(hexstring)*4
    bitstring = bin(int(hexstring, 16))[2:].zfill(num_of_bits)
    return bitstring

#哈希函数族的第一个函数采用SHA3算法
def SecureHashAlgorithm3(reconciled_key):
    Byte_key = StructByteStream(reconciled_key)
    digest = sha3.sha3_224(Byte_key).hexdigest()
    #sha3_224产生的摘要长度为224比特
    #在现在的构想中，256比特的密钥在协商后应该抛弃128比特，也就是隐私放大产生的密钥长度为128比特
    #所以取摘要值的前32*4=128个比特作为结果
    final_key = digest[:32]
    return final_key

#哈希函数族的第二个函数采用SM3算法
def SMthree(reconciled_key):
    Byte_key = StructByteStream(reconciled_key)
    digest = sm3_hash(Byte_key)
    final_key = digest[:32]
    return final_key

#哈希函数族的第三个函数采用BLAKE2b算法,可以参考https://docs.python.org/3/library/hashlib.html
def BLAKE2b(reconciled_key):
#NSA于2007年正式宣布在全球范围内征集新新一代(SHA-3)算法设计，2012年公布评选结果，
#Keccak算法最终获胜成为唯一官方标准SHA-3算法，但还有四种算法同时进入了第三轮评选，
#分别是：BLAKE, GrøSTL, JH和SKEIN，这些算法其实也非常安全，而且经受审查，被各种竞争币频繁使用。
#SHA3并不是NIST在2006年发起的那场竞赛中唯一的突破。虽然SHA3最终获胜，一个叫做BLAKE的算法紧随其后位居第二。

#BLAKE2系列比常见的MD5，SHA-1，SHA-2，SHA-3 更快，同时提供不低于 SHA-3 的安全性。
#BLAKE2b算法为64位 CPU(包括 ARM Neon)优化，可以生成最长64字节的摘要
#所以BLAKE2b算法可以指定生成摘要的位数
    Byte_key = StructByteStream(reconciled_key)
    final_key = blake2b(Byte_key,digest_size=16).hexdigest() #指定生成摘要的位数，隐私增强需要128比特，所以指定为16字节
    return final_key

####下面的哈希函数是备选哈希函数，目前在隐私增强算法中没有使用到以下的哈希函数！
#目前的隐私增强算法只使用了SHA3-224、SM3与BLAKE2b三个哈希函数
##第四个哈希函数，shake_128，shake_128应该是属于SHA-3系列的子函数
def SHAKE128(reconciled_key):
    Byte_key = StructByteStream(reconciled_key)
    final_key = shake_128(Byte_key).hexdigest(16)
    return  final_key

#第五个哈希函数，SHA-2系列里面的SHA-256
def SHA256(reconciled_key):
    Byte_key = StructByteStream(reconciled_key)
    hash_256= sha256()
    hash_256.update(Byte_key)
    final_key = hash_256.hexdigest()[:32]
    return final_key
###############################################################



