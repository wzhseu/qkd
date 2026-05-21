# 导入上面封装好的日志输出
from app.logging_demo import logging_


from app.mods.routers import basic_app_file
from app.mods.utils import STATUS_OK, get_value_with_check, failed_with_explain
# from app.mods.usrp_server.server import USRPServers
# from app.mods.skg.client import SKGClient
import threading
import random
import socket
import json
from sage.all_cmdline import *   # import sage library
import os, time
import configparser

cfg = configparser.ConfigParser()
cfg.read('config.ini')
cloud_ip = cfg.get('constants', 'cloud_ip')
to_ip = cfg.get('constants', 'to_ip')
local_ip = cfg.get('constants', 'local_ip')

#### ip data ####
# local_ip = '121.248.54.244'
# to_ip = '121.248.49.100'
# cloud_ip = '121.248.55.231'
port_num = 8080
log_port = 8000

_path = os.path.dirname(__file__) # 获取当前文件路径
print(_path)
lg = logging_(_path).logger # 实例化类


def register_cloud_device(device_socket):
    payload = {
        "type": "register",
        "device_id": "car-a",
        "name": "Car A"
    }
    device_socket.sendall((json.dumps(payload) + "\n").encode("utf-8"))


class OptionalCloudLogClient:
    def __init__(self):
        self.socket = None
        self.enabled = False

    def connect(self, ip_port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, _sage_const_1)
            self.socket.connect(ip_port)
            self.enabled = True
            print("Cloud log server connected:", ip_port)
        except Exception as e:
            self.socket = None
            self.enabled = False
            print("Cloud log server unavailable, continue locally:", ip_port, e)

    def send(self, data):
        if self.enabled:
            return self.socket.send(data)
        return len(data)

    def recv(self, size):
        if self.enabled:
            return self.socket.recv(size)
        return b"response"

    def shutdown(self, how):
        if self.enabled:
            self.socket.shutdown(how)

    def close(self):
        if self.enabled:
            self.socket.close()

_sage_const_114356107 = Integer(114356107); _sage_const_2 = Integer(2); _sage_const_4 = Integer(4); _sage_const_300 = Integer(300); _sage_const_2p7 = RealNumber('2.7'); _sage_const_3p0 = RealNumber('3.0'); _sage_const_1 = Integer(1); _sage_const_8 = Integer(8); _sage_const_0 = Integer(0); _sage_const_3 = Integer(3); _sage_const_16 = Integer(16); _sage_const_11 = Integer(11); _sage_const_5 = Integer(5); _sage_const_1024 = Integer(1024); _sage_const_8000 = Integer(8000); _sage_const_6969 = Integer(6969); _sage_const_6970 = Integer(6970)
from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
q=_sage_const_114356107 
k=_sage_const_2 
d=_sage_const_4 
sd=_sage_const_300 
M=_sage_const_2p7 
sd=_sage_const_3p0 
K = CyclotomicField(_sage_const_2 *d, names=('zeta',)); (zeta,) = K._first_ngens(1)
OK = K.ring_of_integers()
sigma=K.automorphisms()
sigma_5=K.hom([zeta**(-_sage_const_1 )])
D = DiscreteGaussianDistributionPolynomialSampler(OK, _sage_const_8 , sd)
# usrp_servers = USRPServers()
# skg_client = SKGClient(usrp_servers, socketio, app)

def gen():
    i = _sage_const_0  * zeta + _sage_const_1 
    a_1 = matrix(_sage_const_3 , _sage_const_1 , lambda i, j: OK.random_element(_sage_const_16 ))
    a_2 = matrix(_sage_const_3 , _sage_const_1 , lambda i, j: OK.random_element(_sage_const_16 ))
    r = matrix(_sage_const_3 , _sage_const_1 , lambda i, j: OK.random_element(_sage_const_3 ))
    # a_1=random_matrix(OK,3,1); print("a_1=",a_1)
    # a_2=random_matrix(OK,3,1); print("a_2=",a_2)
    # r=random_matrix(OK,3,1);print("r=",r)
    # 生成承诺值t1,t2
    t_1 = a_1.transpose() * r
    t_2 = a_2.transpose() * r + i
    return (a_1,a_2,r,t_1,t_2)


def sign(a_1,a_2,r,t_1,t_2):
    count = _sage_const_0 
    while True:
        count += _sage_const_1 
        # if count == 1e3:
         #   return (0, 0)
        y_1 = D()
        y_2 = D()
        y_3 = D()
        yy = matrix([y_1, y_2, y_3])
        y = yy.transpose()
        y_5_1 = D()
        y_5_2 = D()
        y_5_3 = D()
        yy_5 = matrix([y_5_1, y_5_2, y_5_3])
        y_5 = yy_5.transpose()
        W_1 = a_1.transpose() * y
        a_1_T = a_1.transpose()
        a_1_T_sig_5 = a_1_T
        for i in range(_sage_const_3 ):
            sigma_5(a_1_T_sig_5[_sage_const_0 , i])
        W_1_5 = a_1_T_sig_5 * y_5
        # 计算W_2_5
        a_2_T = a_2.transpose()
        a_2_T_sig_5 = a_2_T
        for i in range(_sage_const_3 ):
            sigma_5(a_2_T_sig_5[_sage_const_0 , i])
        W_2_5 = a_2_T * y - a_2_T_sig_5 * y_5
        # c = hash((a_1[_sage_const_0 ],a_1[_sage_const_1 ],a_1[_sage_const_2 ],a_2[_sage_const_0 ],a_2[_sage_const_1 ],a_2[_sage_const_2 ]))
        # print(a_1)
        
        c = hash((str(a_1),str(a_2))) # has some problem with hash!!
        c=c%_sage_const_11 
        # 计算z
        z = r * c + y
        # 计算z_5
        r_sigma_5 = r
        for i in range(_sage_const_3 ):
            sigma_5(r_sigma_5[i, _sage_const_0 ])
        z_5 = r_sigma_5 * c + y_5;
        print(type(z))
        
        # z0 = vector(z[_sage_const_0 ][_sage_const_0 ])
        # z1 = vector(z[_sage_const_1 ][_sage_const_0 ])
        # z2 = vector(z[_sage_const_2 ][_sage_const_0 ])
        # z3 = vector(z_5[_sage_const_0 ][_sage_const_0 ])
        # z4 = vector(z_5[_sage_const_1 ][_sage_const_0 ])
        # z5 = vector(z_5[_sage_const_2 ][_sage_const_0 ])
        # rc = r * c;
        # rcc=r_sigma_5 * c
        # rc0 = vector(rc[_sage_const_0 ][_sage_const_0 ])
        # rc1 = vector(rc[_sage_const_1 ][_sage_const_0 ])
        # rc2 = vector(rc[_sage_const_2 ][_sage_const_0 ])
        # rc3 = vector(rcc[_sage_const_0 ][_sage_const_0 ])
        # rc4 = vector(rcc[_sage_const_1 ][_sage_const_0 ])
        # rc5 = vector(rcc[_sage_const_2 ][_sage_const_0 ])
        # pxe0 = float(-_sage_const_2  * z0 * rc0 + (rc0.norm()) ** _sage_const_2 )
        # pxe1 = float(-_sage_const_2  * z1 * rc1 + (rc1.norm()) ** _sage_const_2 )
        # pxe2 = float(-_sage_const_2  * z2 * rc2 + (rc2.norm()) ** _sage_const_2 )
        # pxe3 = float(-_sage_const_2  * z3 * rc3 + (rc3.norm()) ** _sage_const_2 )
        # pxe4 = float(-_sage_const_2  * z4 * rc4 + (rc4.norm()) ** _sage_const_2 )
        # pxe5 = float(-_sage_const_2  * z5 * rc5 + (rc5.norm()) ** _sage_const_2 )
        # r0=exp(pxe0 / (_sage_const_2  * (sd ** _sage_const_2 ))) /M
        # r1=exp(pxe1 / (_sage_const_2  * (sd ** _sage_const_2 ))) / M
        # r2=exp(pxe2 / (_sage_const_2  * (sd ** _sage_const_2 ))) / M
        # r3=exp(pxe3 / (_sage_const_2  * (sd ** _sage_const_2 ))) / M
        # r4=exp(pxe4 / (_sage_const_2  * (sd ** _sage_const_2 ))) / M
        # r5=exp(pxe5 / (_sage_const_2  * (sd ** _sage_const_2 ))) / M
        #if random.random()< r0 and random.random()< r1 and random.random()< r2 and random.random()< r3 and random.random()< r4 and random.random()< r5:
        return (W_1,W_1_5,W_2_5,z,z_5,c,y,y_5,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5)


def verify(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5):
    # check 1
    check1 = W_1 + t_1 * c - a_1_T * z;

    # check 2
    t_1_sigma_5 = t_1
    sigma_5(t_1_sigma_5[_sage_const_0 , _sage_const_0 ])
    check2 = W_1_5 + t_1_sigma_5 * c - a_1_T_sig_5 * z_5;

    # check 3
    t_2_sigma_5 = t_2
    sigma_5(t_2_sigma_5[_sage_const_0 , _sage_const_0 ])
    check3 = W_2_5 + (t_2 - t_2_sigma_5) * c - a_2_T * z + a_2_T_sig_5 * z_5;
    
    p=W_1-W_1
    if((check1==p) & (check2==p) & (check3==p)):
        print("认证成功")
        return _sage_const_1 
    else:
        print("认证失败")
        return _sage_const_0 


def server(device_socket, address, port):

    msgg = "helo i am alice in server" # don't delete!!!!!
    device_socket.send(msgg.encode('utf-8'))

    # server = socket.socket()          # 创建socket对象
    # server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,_sage_const_1 )
    # server.bind((address, port))  # 绑定要监听的端口port

    print("waiting the call")
    # server.listen(_sage_const_5 )
    data = tuple()
    # conn, addr = server.accept()     # 在此处监听端口号
    # print("the call has comming")
    
    while True:
        d = device_socket.recv(_sage_const_1024 )
        if d.decode('utf-8') != "finished":
            # print(d)
            data = data + (d.decode('utf-8'),)  # 将数据存在元组data中
            device_socket.send("receive".encode(encoding='utf-8'))  # 向client发送”receive"表示收到
        else:
            break
    return data


def user(device_socket, addr, port, *value):


    num = len(value)              # 获取数据大小，方便后面的循环
    
    # print("value len:",num)
    #print("value:",value)
    
    i = _sage_const_1 
    
    device_socket.send(str(value[_sage_const_0 ]).encode(encoding='utf-8'))  # 依次发送value中的数据
    while i < num:
        data = device_socket.recv(_sage_const_1024 )
        if data.decode('utf-8') == "receive":      # 收到“receive”再发送下一次数据
            device_socket.send(str(value[i]).encode(encoding='utf-8'))
            i = i+_sage_const_1 
    data = device_socket.recv(_sage_const_1024 )
    if data.decode('utf-8') == "receive":          # 最后一次发送“finished”要在收到回应之后，不然会和最后一次发送数据连在一起，产生错误
        device_socket.send("finished".encode(encoding='utf-8'))
    # client.shutdown(_sage_const_2 )


def str2m(x,dimension):
    y=matrix(dimension, _sage_const_1 , lambda i, j: OK.random_element(_sage_const_16 ))
    y=y-y
    l=len(x)
    i=_sage_const_0 
    d=_sage_const_0 
    coe=''
    index=''
    operation='+'
    symbol=x[_sage_const_0 ]
    while i < l:     
     
        if symbol=='[':
            i+=_sage_const_1 
            symbol=x[i]
            while symbol==' ':
                i+=_sage_const_1 
                symbol=x[i]
            continue
        if(symbol=='+'):
            operation='+'
            i+=_sage_const_1 
            symbol=x[i]
        if(symbol=='-'):
            operation='-' 
            i+=_sage_const_1  
            symbol=x[i]
        while '0' <= symbol <= '9':
            coe += symbol
            i+=_sage_const_1 
            symbol=x[i]
        if coe!='' and (symbol==' ' or symbol== ']'):
            if(operation=='+'):
                y[d,_sage_const_0 ]+=int(coe)
            else:
                y[d,_sage_const_0 ]+=-int(coe)
            coe=''
            operation='+'
        if symbol=='z' or symbol=='e' or symbol=='t' or symbol =='*':
            i+=_sage_const_1 
            symbol=x[i]
        if symbol=='a': # if see zeta
            i+=_sage_const_1 
            symbol=x[i]
            if symbol == '^':
                i+=_sage_const_1 
                symbol=x[i]
                while '0' <= symbol <= '9':
                    index += symbol
                    i+=_sage_const_1 
                    symbol=x[i]
            else:
                index='1'
        if (index!= ''): # do have zeta
            if(coe==''):
                coe='1'
            if(operation=='+'):
                y[d,_sage_const_0 ]+=int(coe)*zeta**int(index)
            else:
                y[d,_sage_const_0 ]+=-int(coe)*zeta**int(index) 
            coe=''
            index=''
            operation='+'

        if symbol=='\n':
            d+=_sage_const_1 
            i+=_sage_const_1 
            symbol=x[i]

        if  i<l-_sage_const_1  and symbol==' ' and x[i-_sage_const_1 ]!= '+' and x[i-_sage_const_1 ]!='-' and x[i-_sage_const_1 ] != ' ' and x[i+_sage_const_1 ]!='+' and x[i+_sage_const_1 ]!= '-':
            d+=_sage_const_1 
          
        if symbol==']':
            if d==dimension-_sage_const_1 :
                if coe=='':
                    break
                else:
                    continue
            else:
                i+=_sage_const_1 
                symbol=x[i]
                continue  
                
        if symbol==' ':
            i+=_sage_const_1 
            symbol=x[i] 
    return y

# 创建方法生成日志
def generation_log(): 

    #与qkd_server之间socket通信开启
    #定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
    client = OptionalCloudLogClient()
    #定义IP地址与端口号
    addr= cloud_ip
    port=log_port 
    ip_port=(addr,port)
    #进行连接服务器
    client.connect(ip_port)

    # 两设备之间socket通信开启
    # 创建一个socket对象
    device_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接到云服务器的IP和端口
    device_socket.connect((cloud_ip, port_num)) # 这里可以改进一下
    register_cloud_device(device_socket)

    daa_start_time = time.time()
    daa_verify(client, device_socket)
    daa_beverified(client, device_socket)
    daa_end_time = time.time()
    daa_transfer_time = round((daa_end_time - daa_start_time), 2)
    msg = "车A进行DAA认证时间共：" + str(daa_transfer_time) +"秒"
    print(msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))

    msg="车A请求量子密钥"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))   
    # lg.info("Alice receive: %s"%(a.decode('utf-8'))) 
    
    msg="车A量子密钥已获取"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))   
    # lg.info("Alice receive: %s"%(a.decode('utf-8'))) 

    msg="车A等待视频文件传输"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))   
    # lg.info("Alice receive: %s"%(a.decode('utf-8'))) 

    device_socket.close()      

    client.shutdown(socket.SHUT_RDWR)
    client.close()

    # time.sleep(4)



        
# 读取日志并返回
def red_logs():
    log_path = f'{_path}/log.log' # 获取日志文件路径
    # print("log_path:",log_path)
    with open(log_path,'rb') as f:
        log_size = os.path.getsize(log_path) # 获取日志大小
        # print("log_size:",log_size)
        offset = -100
        # 如果文件大小为0时返回空
        if log_size == 0:
            return ''
        while True:
            # 判断offset是否大于文件字节数,是则读取所有行,并返回
            if (abs(offset) >= log_size):
                f.seek(-log_size, 2)
                data = f.readlines()
                return data
            # 游标移动倒数的字节数位置
            data = f.readlines()
            # 判断读取到的行数，如果大于1则返回最后一行，否则扩大offset
            if (len(data) > 1):
                return data
            else:
                offset *= 2

def daa_verify(client, device_socket):
    # ######verify#########
    # #定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
    # client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,_sage_const_1 )
    # #定义IP地址与端口号
    # addr='192.168.201.131'
    # port=_sage_const_8000 
    # ip_port=(addr,port)
    # #进行连接服务器
    # client.connect(ip_port)

    # while True:
    msg="车A已就绪"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    # lg.info("Alice receive: %s"%(a.decode('utf-8')))


#### Bob send data to Alice
    W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5=server(device_socket, local_ip, port_num );  # 注意是本机地址
    W_1,W_1_5,W_2_5,t_1,t_2=str2m(W_1,_sage_const_1 ),str2m(W_1_5,_sage_const_1 ),str2m(W_2_5,_sage_const_1 ),str2m(t_1,_sage_const_1 ),str2m(t_2,_sage_const_1 )
    c=int(c)
    #print("a_1_T:",a_1_T)
    #print("z_5:",z_5)
    a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5=str2m(a_1_T,_sage_const_3 ).transpose(),str2m(a_1_T_sig_5,_sage_const_3 ).transpose(),str2m(a_2_T,_sage_const_3 ).transpose(),str2m(a_2_T_sig_5,_sage_const_3 ).transpose()
    z,z_5=str2m(z,_sage_const_3 ),str2m(z_5,_sage_const_3 )

    #print("___________")
    #print(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5)
    #print("a_1_T:",a_1_T)
    #print("z_5:",z_5)

    msg="车A接收到对方数据"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    # lg.info("Alice receive: %s"%(a.decode('utf-8')))


    
    
#### Alice verify
    
    msg="车A尝试验证对方身份"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    # lg.info("Alice receive: %s"%(a.decode('utf-8')))
    
    verification=verify(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5)
    
    if verification:
        msg="车A认证成功，对方身份合法！"
    else:
        msg="车A认证失败！"
    print("车A发送：", msg)
    lg.info("%s"%(msg))
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    # lg.info("Alice receive: %s"%(a.decode('utf-8')))
        
        
        # break


def daa_beverified(client, device_socket):
    ######be verified#########

    # ######verify#########
    # #定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
    # client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,_sage_const_1 )
    # #定义IP地址与端口号
    # addr='192.168.201.131'
    # port=_sage_const_8000 
    # ip_port=(addr,port)
    # #进行连接服务器
    # client.connect(ip_port)


    while True:
        msg="车A请求与对方通信"
        print("车A发送：", msg)
        lg.info("%s"%(msg))
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))
        # lg.info("Alice receive: %s"%(a.decode('utf-8')))

    ####gen
        a_1,a_2,r,t_1,t_2=gen()
        print("gen done")
        msg="车A完成参数生成"
        print("车A发送：", msg)
        lg.info("%s"%(msg))
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))    
        # lg.info("Alice receive: %s"%(a.decode('utf-8')))
        
    ####sign
        W_1,W_1_5,W_2_5,z,z_5,c,y,y_5,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5=sign(a_1,a_2,r,t_1,t_2)
        print("sign done")
        msg="车A加入并签名"
        print("车A发送：", msg)
        lg.info("%s"%(msg))
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))
        # lg.info("Alice receive: %s"%(a.decode('utf-8')))

        # print("___________")
        # print("W_1:",W_1)
        # print("W_1_5:",W_1_5)
        # print("W_2_5:",W_2_5)
        # print("t_1:",t_1)
        # print("t_2:",t_2)
        # print("c:",c)
        # print("a_1_T:",a_1_T)
        # print("a_1_T_sig_5:",a_1_T_sig_5)
        # print("a_2_T:",a_2_T)
        # print("a_2_T_sig_5:",a_2_T_sig_5)
        # print("z:",z)
        # print("z_5:",z_5)

        msg="车A发送身份凭证"
        print("车A发送：", msg)
        lg.info("%s"%(msg))
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))
        # lg.info("Alice receive: %s"%(a.decode('utf-8')))

        user(device_socket, cloud_ip, port_num ,W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5)
        
        msg="车A发送完毕"
        print("车A发送：", msg)
        lg.info("%s"%(msg))
        client.send(msg.encode('utf-8'))#将发送的数据进行编码
        a=client.recv(_sage_const_1024 )#接受服务端的信息，最大数据为1k
        print(a.decode('utf-8'))   
        # lg.info("Alice receive: %s"%(a.decode('utf-8'))) 

        
        break
