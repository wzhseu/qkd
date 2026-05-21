def SecretKeyUtil(SecretKeyFile):
    with open(SecretKeyFile, 'r') as f:
        BitsStream = f.read()[0:128]  # SM4算法的密钥长度为128比特
    ######接收方通过USRP接收到比特，开始进行恢复
    tmp = hex(int(BitsStream, 2))[2:]  # 二进制比特流转十六进制
    DataBytes = bytes.fromhex(tmp)  # 十六进制数据转字节流
    return DataBytes