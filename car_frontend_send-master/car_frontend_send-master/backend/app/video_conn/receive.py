import imagiz
import cv2
import multiprocessing
import os
import signal
import base64
import numpy
from io import BytesIO

from Crypto.Cipher import AES
# from qkd_receive_demo import quantum_key_agree 

# 解密后，去掉补足的空格用strip() 去掉
def decrypt(text, key):

    # rec = '1968efda000000000100000000000000c0d27f23ce7f0000a0d87f23ce7f0000'
    # rec = str((quantum_key_agree().hex())[0:64])
    # key = int(rec, 16).to_bytes(32,'big')
    # key = (quantum_key_agree().hex())[0:64]

    mode = AES.MODE_ECB
    cryptor = AES.new(key, mode)
    res = base64.decodebytes(text)
    plain_text = cryptor.decrypt(res).decode("utf-8").rstrip('\0')
    return bytes(plain_text, encoding='utf-8')


def start_server(port, sv_op):

    print("start server!")
    server=imagiz.Server(port=port) # Starting server instance on port 7070
    
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
    if sv_op: # if sv_op is True the incoming video frame will be saved as Video.avi
      vid_cod = cv2.VideoWriter_fourcc(*'XVID')
      output = cv2.VideoWriter("Video.avi", vid_cod, 10.0, (640,480))  # 帧率，（长*宽）


    while True:
        message=server.receive() # Recieve incoming frame forever with While True loop.
        tmp = decrypt(message.image, key)

        dc_bytes = base64.b64decode(tmp) # Decoding the recieved message using base64 as was encrypted on client side using base64
        df = BytesIO(dc_bytes)
        df = numpy.load(df) # converting bytes into numpy array

        message = cv2.imdecode(df,1)

        # setting resizing parameter as it was compressed to 60% of original size while transmission

        width = int(message.shape[1] / 0.6) 
        height = int(message.shape[0] / 0.6)
        dim = (width, height)

        # resizing frame to original size
        resized = cv2.resize(message, dim, interpolation = cv2.INTER_AREA) 
        
        # ######################## ???
        # ret, jpeg = cv2.imencode('.jpg', resized)
        # yield(b'--frame\r\n'
        #       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes()+b'\r\n\r\n')


        cv2.imshow("Video",resized) # showing resized frame

        if sv_op:
            output.write(resized) # Writing frame to file if save option is provided true



        if cv2.waitKey(1) & 0xFF == ord('q'): # Close visualization panel if 'q' is pressed
          break

    try:
        output.release() 
    except:
        pass 

    cv2.destroyAllWindows() # detroy  cv2 window
    current_id = multiprocessing.current_process().pid # getting current server process ID
    os.kill(current_id,signal.SIGTERM) # Making sure the server process is terminated and not running in background

if __name__ == '__main__':
    start_server(8082,True) 

