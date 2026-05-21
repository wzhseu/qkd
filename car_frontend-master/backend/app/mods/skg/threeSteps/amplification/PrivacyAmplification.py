from .cryptohashtool import SecureHashAlgorithm3,SMthree,BLAKE2b

def determine_which_hash_to_use(reconciled_key):
    #Alice和Bob在信息协商得到一致的密钥后，进行隐私增强阶段；
    #隐私增强采用密码学哈希函数进行增强隐私，本方案目前采用了
    #3个哈希函数进行隐私增强，分别是SHA-3、SM3与BLAKE2b哈希函数
    #本函数实现的功能即Alice和Bob根据协商好的密钥，决定使用
    #哪一个哈希函数来进行隐私增强
    if len(reconciled_key)%2 !=0:
        reconciled_key += '0' #接下来的操作需要协商密钥长度为偶数，所以如果长度是奇数的话，需要补上一位
    half_length = len(reconciled_key)//2
    sum = 0
    for i in range(0,half_length//2):
        Q1 = int(reconciled_key[2*i])*2+int(reconciled_key[2*i+1])
        Q2 = int(reconciled_key[half_length+(2*i)]) * 2 + int(reconciled_key[half_length+(2 * i + 1)])
        sum += (Q1 * Q2)
    hash_function_order = sum%3
    return hash_function_order

def privacy_amplification(reconciled_key):
    hash_function_dict = {
        0:SecureHashAlgorithm3,
        1:SMthree,
        2:BLAKE2b
    }
    hash_function_order = determine_which_hash_to_use(reconciled_key)
    privacy_amplified_key = hash_function_dict[hash_function_order](reconciled_key)
    return privacy_amplified_key

