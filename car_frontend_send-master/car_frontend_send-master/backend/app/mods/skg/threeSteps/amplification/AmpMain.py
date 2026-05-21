from PrivacyAmplification import privacy_amplification
from cryptohashtool import Hex2Bin

if __name__ == '__main__':
    with open("Originalkey.txt", "r") as f:
        reconciled_key = f.read()  # 读取信息协调好之后的密钥
    privacy_amplified_key = privacy_amplification(reconciled_key) #使用哈希函数进行隐私增强
    bin_privacy_amplified_key= Hex2Bin(privacy_amplified_key) #将十六进制表示的哈希值转换为二进制表示
    with open("Generatedkey.txt", "w") as f:
        f.write(bin_privacy_amplified_key) #将隐私增强后的密钥写入文本中


