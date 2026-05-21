from flask import render_template
from flask import request
from flask import Response
from app import app
# from wordcloud import WordCloud
import io
import base64
import os
import socket
import time
import threading

# import utils

from app.A_daa import generation_log, red_logs
from app.q_transfer.vdt_demo import VDT
# from app.video_conn.send import send_webcam
from app.video_conn.A_quantum_receive import quantum_key_agree
import configparser

cfg = configparser.ConfigParser()
cfg.read('config.ini')
cloud_ip = cfg.get('constants', 'cloud_ip')
to_ip = cfg.get('constants', 'to_ip')
local_ip = cfg.get('constants', 'local_ip')

# cloud_ip = '121.248.55.231' #yunduande
port_num = 8000

daa_thread = None
daa_thread_lock = threading.Lock()


def run_generation_log_background():
    try:
        generation_log()
    except Exception as exc:
        print("generation_log failed:", exc)


def start_generation_log_once():
    global daa_thread
    with daa_thread_lock:
        if daa_thread and daa_thread.is_alive():
            return False
        daa_thread = threading.Thread(target=run_generation_log_background, daemon=True)
        daa_thread.start()
        return True

line_number = [0] #存放当前日志行数
# 定义接口把处理日志并返回到前端
@app.route('/car/A/get_log',methods=['POST'])
def get_log():
    log_data = red_logs() # 获取日志
    # 判断如果此次获取日志行数减去上一次获取日志行数大于0，代表获取到新的日志
    if len(log_data) - line_number[0] > 0:
        # print("line_number:",line_number)
        log_type = 2 # 当前获取到日志
        log_difference = len(log_data) - line_number[0] # 计算获取到少行新日志
        log_list = [] # 存放获取到的新日志
        # 遍历获取到的新日志存放到log_list中
        # print("log_data[-1]:",log_data[-1])
        for i in range(log_difference):
            log_i = log_data[-(i+1)].decode('utf-8') # 遍历每一条日志并解码
            log_list.insert(0,log_i) # 将获取的日志存放log_list中

    else:
        log_type = 3
        log_list = ''
    # 已字典形式返回前端
    _log = {
        'log_type' : log_type,
        'log_list' : log_list
    }

    line_number.pop() # 删除上一次获取行数
    line_number.append(len(log_data)) # 添加此次获取行数
    # print("_log:", _log)
    # print("_log.data:", _log.data)
    return (str(_log['log_list'])[2:-4])
 
# 通过前端请求执行生成日志方法
@app.route('/car/A/generation_log',methods=['POST'])
def generation_log_():
    if request.method == 'POST':
        if not start_generation_log_once():
            return "generation_log_running"
        # print("i want to generation a log")
    return "generation_log"

# 通过前端请求执行生成日志方法
# 通过前端请求执行视频通信
@app.route('/car/A/video_call',methods=['POST'])
def video_call():
    if request.method == 'POST':
        # 发送小车：启动send发送视频，也启动receive接收视频（双向通信）
        os.system("gnome-terminal -e 'python3 video_conn/send.py'")
        time.sleep(1)  # 稍等一下再启动接收
        os.system("gnome-terminal -e 'python3 video_conn/receive.py'")
        # print("i want to generation a log")
    return "video_call"
######## if you want to transfer the file use this:

@app.route('/car/A/VDT',methods=['POST'])
def VDT_():
    if request.method == 'POST':
        print("VDT----------------------------------------------------------------")
        time.sleep(5)
        quantum_key_agree() 
        
        # os.system("gnome-terminal -e 'python3 video_conn/A_quantum_receive.py'")

        #与qkd_server之间socket通信开启
        #定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
        client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        #定义IP地址与端口号
        addr= cloud_ip
        port= port_num
        ip_port=(addr,port)
        #进行连接服务器
        client.connect(ip_port)
        
        msg = '车A加密视频通信开启'
        print("车A发送：", msg)
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv( 1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))

        msg = '车A加密视频通信速率为30fps'
        print("车A发送：", msg)
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv( 1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))


        msg = '车A等待视频文件传输'
        print("车A发送：", msg)
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv( 1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))
        print("next is quantum key agree")

        os.system("gnome-terminal -e 'python3 video_conn/receive.py'&& xdotool key Super+h") 

        VDT_res = VDT()   
        # VDT_res = 1  
        if (VDT_res):
            videoState = True
            print("videoState:",videoState)
            msg = '车A视频文件接收并解密成功'
            print("车A发送：", msg)
            client.send(msg.encode('utf-8'))#将发送的数据进行编码0.117
            a=client.recv( 1024 )#接受服务端的信息，最大数据为1k
            print(a.decode('utf-8'))
    return str(videoState)



@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        return render_template('index.html')

if __name__=='__main__':
    print('Now starting to run...')
    app.run(host="0.0.0.0", 
    port = 5001, 
    use_reloader = False, 
    debug = True)
