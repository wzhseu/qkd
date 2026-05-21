#Client.py

import imagiz
import cv2
import time
from io import BytesIO
import numpy as np
import base64
import os
import multiprocessing
import signal

import base64
from Crypto.Cipher import AES
# from qkd_receive_demo import quantum_key_agree 
import configparser

# Load config relative to project root so running from subfolders still works.
cfg = configparser.ConfigParser()
config_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
if not cfg.read(config_path):
    raise FileNotFoundError(f"Failed to read config file at {config_path}")
cloud_ip = cfg.get('constants', 'cloud_ip')
to_ip = cfg.get('constants', 'to_ip')
local_ip = cfg.get('constants', 'local_ip')
local127_ip = cfg.get('constants', 'local127_ip')

# local_ip = '121.248.54.244'
# to_ip = '121.248.49.100'



def add_to_16(text):
    if len(text) % 16:
        add = 16 - (len(text) % 16)
    else:
        add = 0
    text = text + (b'\0' * add)
    return text

# 加密函数
def encrypt(text, key):
    # print("hello")
    # key = quantum_key_agree().encode('utf-8')
    # key = '9999999999999999'.encode('utf-8')
    text = add_to_16(text)
    cryptos = AES.new(key=key, mode=AES.MODE_ECB)
    cipher_text = cryptos.encrypt(text)
    msg = base64.b64encode(cipher_text)
    return msg


def send_webcam(port):
    with open("catch_q_key.txt", "r") as f:
        rec = f.readline().strip()
    
    if not rec:
        raise ValueError("密钥文件为空！请先运行 B_quantum_receive.py 获取密钥")
    
    print(f"读取的密钥字符串: {rec}")
    print(f"密钥长度: {len(rec)} 字符")
    
    # 确保密钥是64个十六进制字符（32字节）
    if len(rec) > 64:
        print(f"警告：密钥长度超过64字符，截取前64个字符")
        rec = rec[:64]
    elif len(rec) < 64:
        raise ValueError(f"密钥长度不足！需要64个字符，当前只有{len(rec)}个字符")
    
    try:
        key = int(rec, 16).to_bytes(32,'big')
        print(f"成功加载密钥，密钥字节长度: {len(key)}")
    except ValueError as e:
        raise ValueError(f"密钥格式错误，必须是有效的16进制字符串: {e}")

    vid=cv2.VideoCapture(0)
    client=imagiz.Client(server_port=port,client_name="cc2",server_ip=to_ip) # establishing connection with the server computer. Note: change serveer_ip to ip of administrative computer
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    # t_end = time.time() + int(time_)
    frame_rate = 10
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        r,frame=vid.read()
        print('Original Dimension', frame.shape)
        fps = vid.get(cv2.CAP_PROP_FPS)
        print("fps:",fps)

        if time_elapsed > 1./frame_rate:
            prev = time.time()
            scale_percent = 60 # percent of original size
            width = int(frame.shape[1] * scale_percent / 100) # compressing frame for easy transmission
            height = int(frame.shape[0] * scale_percent / 100)
            dim = (width, height)

            # resize image
            resized = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA) # resizing frame with provided scale factor

            if r:
                try:
                    r,image=cv2.imencode('.jpg',resized, encode_param) # enconding to bytes

                    np_bytes = BytesIO()

                    np.save(np_bytes, image, allow_pickle=True) # allow_pickle = true allows dimension of numpy array to be encrypted alongside
                    np_bytes = np_bytes.getvalue()

                    en_bytes = base64.b64encode(np_bytes) # base64 encoding of numpy array

                    response=client.send(encrypt(en_bytes, key)) # sending encoded bytes over to server computer
                    # print(encrypt(en_bytes, key))
                except:
                    break

    vid.release()
    cv2.destroyAllWindows()
    current_id = multiprocessing.current_process().pid
    os.kill(current_id,signal.SIGTERM)

if __name__ == '__main__':
    send_webcam(8081) 
