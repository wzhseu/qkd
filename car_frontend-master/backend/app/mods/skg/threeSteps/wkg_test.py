import matlab.engine
import os

## kill the usrp
# pid = os.system("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'")

# pid = os.popen("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'").read()
# print('--pid--\n')
# print(pid)
# print(type(pid))
# pid=pid.split('\n')
# print(pid)
#
# for index in range(len(pid)-1):
#     os.system('sudo -S kill -9 %s' % pid[index])
# pid2 = os.popen("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'").read()
# print('--pid2--\n')
# print(pid2)
# print('------------------------')

id='server'
# id='client'  # the computer is server or client?

### Step1
## usrp-server
cmd1 = 'cd ~/code/usrp-server/build; sudo -S ./usrp_server --bind "tcp://*:5555" --device-args "addr=192.168.10.3"'
os.system(cmd1)

# textlist = os.popen(cmd1).readlines()
# for line in textlist:   # 输出命令执行后的返回信息
# 	print(line)

## skg-client
# cmd2 = 'cd ~/code/skg-client; source venv/bin/activate;FLASK_APP=main.py flask run --host=0.0.0.0 --port=5000'
# os.system(cmd2)


## kill the usrp
# pid = os.system("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'")

pid = os.popen("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'").read()
print('--pid--\n')
print(pid)
print(type(pid))
pid=pid.split('\n')
print(pid)

for index in range(len(pid)-1):
    os.system('sudo -S kill -9 %s' % pid[index])
pid2 = os.popen("ps -ef|grep usrp_server|grep -v grep|awk '{print $2}'").read()
print('--pid2--\n')
print(pid2)
print('------------------------')


### Step2 quantization

eng_quantization = matlab.engine.start_matlab()
path_quantization = eng_quantization.genpath('quantization')
eng_quantization.addpath(path_quantization, nargout=0)
eng_quantization.QuanMain(nargout=0)

eng_quantization.quit()

### Step3 reconciliation
## Server

if id=='server':
    eng_reconc_server = matlab.engine.start_matlab()
    path_reconc_server = eng_reconc_server.genpath('conciliation/Server')
    eng_reconc_server.addpath(path_reconc_server, nargout=0)
    eng_reconc_server.ReconcMain(nargout=0)
    eng_reconc_server.quit()

    # socket


## Client
elif id=='client':
    # socket

    eng_reconc_client = matlab.engine.start_matlab()
    path_reconc_client = eng_reconc_client.genpath('conciliation/Client')
    eng_reconc_client.addpath(path_reconc_client, nargout=0)
    eng_reconc_client.ReconcMain(nargout=0)
    eng_reconc_client.quit()


### step4
from amplification.cryptohashtool import Hex2Bin
from amplification.PrivacyAmplification import privacy_amplification


with open("/home/wkg/code/skg-client/mods/skg/threeSteps/conciliation/OriginalKey.txt", "r") as f:
    reconciled_key = f.read()  # 读取信息协调好之后的密钥
privacy_amplified_key = privacy_amplification(reconciled_key) #使用哈希函数进行隐私增强
bin_privacy_amplified_key= Hex2Bin(privacy_amplified_key) #将十六进制表示的哈希值转换为二进制表示
with open("/home/wkg/code/skg-client/mods/skg/threeSteps/SecretKey.txt", "w") as f:
    f.write(bin_privacy_amplified_key) #将隐私增强后的密钥写入文本中


print('Amp Done!')


### step5 encryption/decryption
if id=='server':
    from encryption.SM4_Encryption import encrypt_oracle
    encrypt_oracle('encryption/Alice_QR.png', 'CBC')
    print('wkg encryption Done!')
elif id=='client':
    from encryption.SM4_Decryption import decrypt_oralce
    decrypt_oralce('decryption/Alice_QR.png.sm4', 'CBC')
    print('wkg decryption Done!')
