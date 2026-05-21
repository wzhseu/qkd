from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler
q=114356107
k=2
d=4
sd=300
M=2.7
sd=3.0
K.<zeta> = CyclotomicField(2*d)
OK = K.ring_of_integers()
sigma=K.automorphisms()
sigma_5=K.hom([zeta^(-1)])
D = DiscreteGaussianDistributionPolynomialSampler(OK, 8, sd)



def gen():
    i = 0 * zeta + 1
    a_1 = matrix(3, 1, lambda i, j: OK.random_element(16));
    a_2 = matrix(3, 1, lambda i, j: OK.random_element(16));
    r = matrix(3, 1, lambda i, j: OK.random_element(3));
    # a_1=random_matrix(OK,3,1); print("a_1=",a_1)
    # a_2=random_matrix(OK,3,1); print("a_2=",a_2)
    # r=random_matrix(OK,3,1);print("r=",r)
    # 生成承诺值t1,t2
    t_1 = a_1.transpose() * r;
    t_2 = a_2.transpose() * r + i;
    return (a_1,a_2,r,t_1,t_2)


import random
def sign(a_1,a_2,r,t_1,t_2):
    count = 0
    while True:
        count += 1
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
        for i in range(3):
            sigma_5(a_1_T_sig_5[0, i])
        W_1_5 = a_1_T_sig_5 * y_5
        # 计算W_2_5
        a_2_T = a_2.transpose()
        a_2_T_sig_5 = a_2_T
        for i in range(3):
            sigma_5(a_2_T_sig_5[0, i])
        W_2_5 = a_2_T * y - a_2_T_sig_5 * y_5
        c = hash((a_1[0],a_1[1],a_1[2],a_2[0],a_2[1],a_2[2]))
        c=c%11
        # 计算z
        z = r * c + y;
        # 计算z_5
        r_sigma_5 = r
        for i in range(3):
            sigma_5(r_sigma_5[i, 0])
        z_5 = r_sigma_5 * c + y_5;
        z0 = vector(z[0][0])
        z1 = vector(z[1][0])
        z2 = vector(z[2][0])
        z3 = vector(z_5[0][0])
        z4 = vector(z_5[1][0])
        z5 = vector(z_5[2][0])
        rc = r * c;
        rcc=r_sigma_5 * c
        rc0 = vector(rc[0][0])
        rc1 = vector(rc[1][0])
        rc2 = vector(rc[2][0])
        rc3 = vector(rcc[0][0])
        rc4 = vector(rcc[1][0])
        rc5 = vector(rcc[2][0])
        pxe0 = float(-2 * z0 * rc0 + (rc0.norm()) ** 2)
        pxe1 = float(-2 * z1 * rc1 + (rc1.norm()) ** 2)
        pxe2 = float(-2 * z2 * rc2 + (rc2.norm()) ** 2)
        pxe3 = float(-2 * z3 * rc3 + (rc3.norm()) ** 2)
        pxe4 = float(-2 * z4 * rc4 + (rc4.norm()) ** 2)
        pxe5 = float(-2 * z5 * rc5 + (rc5.norm()) ** 2)
        r0=exp(pxe0 / (2 * (sd ** 2))) /M
        r1=exp(pxe1 / (2 * (sd ** 2))) / M
        r2=exp(pxe2 / (2 * (sd ** 2))) / M
        r3=exp(pxe3 / (2 * (sd ** 2))) / M
        r4=exp(pxe4 / (2 * (sd ** 2))) / M
        r5=exp(pxe5 / (2 * (sd ** 2))) / M
        #if random.random()< r0 and random.random()< r1 and random.random()< r2 and random.random()< r3 and random.random()< r4 and random.random()< r5:
        return (W_1,W_1_5,W_2_5,z,z_5,c,y,y_5,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5)


def verify(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5):
    # check 1
    check1 = W_1 + t_1 * c - a_1_T * z;

    # check 2
    t_1_sigma_5 = t_1
    sigma_5(t_1_sigma_5[0, 0])
    check2 = W_1_5 + t_1_sigma_5 * c - a_1_T_sig_5 * z_5;

    # check 3
    t_2_sigma_5 = t_2
    sigma_5(t_2_sigma_5[0, 0])
    check3 = W_2_5 + (t_2 - t_2_sigma_5) * c - a_2_T * z + a_2_T_sig_5 * z_5;
    
    p=W_1-W_1
    if((check1==p) & (check2==p) & (check3==p)):
        print("认证成功")
        return 1
    else:
        print("认证失败")
        return 0



import socket


def server(addr, port):
    server = socket.socket()          # 创建socket对象
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind((addr, port))  # 绑定要监听的端口port
    print("waiting the call")
    server.listen(5)
    data = tuple()
    conn, addr = server.accept()     # 在此处监听端口号
    print("the call has coming")
    while True:
        d = conn.recv(1024)
        if d.decode('utf-8') == 'finished':    # 收到finished代表client发送数据结束
            conn.close()                       # 关闭连接
            break
        else:
            data = data + (d.decode('utf-8'),)  # 将数据存在元组data中
            conn.send("receive".encode(encoding='utf-8'))  # 向client发送”receive"表示收到
    
    # print("data:",data)
    server.shutdown(2)
    
    return data



import socket


def user(addr, port, *value):
    client = socket.socket()      # 创建socket对象
    client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
    client.connect((addr, port))  # 向指定地址和端口的服务端发起连接请求
    num = len(value)              # 获取数据大小，方便后面的循环
    # print("value len:",num)
    # print("value:",value)
    i = 1
    client.send(str(value[0]).encode(encoding='utf-8'))  # 依次发送value中的数据
    while i < num:
        data = client.recv(1024)
        if data.decode('utf-8') == "receive":      # 收到“receive”再发送下一次数据
            client.send(str(value[i]).encode(encoding='utf-8'))
            i = i+1
    data = client.recv(1024)
    if data.decode('utf-8') == "receive":          # 最后一次发送“finished”要在收到回应之后，不然会和最后一次发送数据连在一起，产生错误
        client.send("finished".encode(encoding='utf-8'))
    client.close()


def str2m(x,dimension):
    y=matrix(dimension, 1, lambda i, j: OK.random_element(16))
    y=y-y
    l=len(x)
    i=0
    d=0
    coe=''
    index=''
    operation='+'
    symbol=x[0]
    while i < l:     
     
        if symbol=='[':
            i+=1
            symbol=x[i]
            while symbol==' ':
                i+=1
                symbol=x[i]
            continue
        if(symbol=='+'):
            operation='+'
            i+=1
            symbol=x[i]
        if(symbol=='-'):
            operation='-' 
            i+=1 
            symbol=x[i]
        while '0' <= symbol <= '9':
            coe += symbol
            i+=1
            symbol=x[i]
        if coe!='' and (symbol==' ' or symbol== ']'):
            if(operation=='+'):
                y[d,0]+=int(coe)
            else:
                y[d,0]+=-int(coe)
            coe=''
            operation='+'
        if symbol=='z' or symbol=='e' or symbol=='t' or symbol =='*':
            i+=1
            symbol=x[i]
        if symbol=='a': # if see zeta
            i+=1
            symbol=x[i]
            if symbol == '^':
                i+=1
                symbol=x[i]
                while '0' <= symbol <= '9':
                    index += symbol
                    i+=1
                    symbol=x[i]
            else:
                index='1'
        if (index!= ''): # do have zeta
            if(coe==''):
                coe='1'
            if(operation=='+'):
                y[d,0]+=int(coe)*zeta^int(index)
            else:
                y[d,0]+=-int(coe)*zeta^int(index) 
            coe=''
            index=''
            operation='+'

        if symbol=='\n':
            d+=1
            i+=1
            symbol=x[i]

        if  i<l-1 and symbol==' ' and x[i-1]!= '+' and x[i-1]!='-' and x[i-1] != ' ' and x[i+1]!='+' and x[i+1]!= '-':
            d+=1
          
        if symbol==']':
            if d==dimension-1:
                if coe=='':
                    break
                else:
                    continue
            else:
                i+=1
                symbol=x[i]
                continue  
                
        if symbol==' ':
            i+=1
            symbol=x[i] 
    return y


######verify#########
#定义一个ip协议版本AF_INET，为IPv4；同时也定义一个传输协议（TCP）SOCK_STREAM
client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
#定义IP地址与端口号
addr='192.168.201.131'
port=8000
ip_port=(addr,port)
#进行连接服务器
client.connect(ip_port)

while True:
    msg="Alice is ready"
    print("Alice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))


#### Bob send data to Alice
    W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5=server('192.168.201.131', 6969);  # 注意是本机地址
    W_1,W_1_5,W_2_5,t_1,t_2=str2m(W_1,1),str2m(W_1_5,1),str2m(W_2_5,1),str2m(t_1,1),str2m(t_2,1)
    c=int(c)
    #print("a_1_T:",a_1_T)
    #print("z_5:",z_5)
    a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5=str2m(a_1_T,3).transpose(),str2m(a_1_T_sig_5,3).transpose(),str2m(a_2_T,3).transpose(),str2m(a_2_T_sig_5,3).transpose()
    z,z_5=str2m(z,3),str2m(z_5,3)

    #print("___________")
    #print(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5)
    #print("a_1_T:",a_1_T)
    #print("z_5:",z_5)

    msg="Alice received Bob's verification data"
    print("Alice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    
    
#### Alice verify
    
    msg="Alice try to verify Bob"
    print("Alice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    
    verification=verify(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5);
    
    if verification:
        msg="Verification Done!"
    else:
        msg="Verification Failed"
    print("Alice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))
    
    
    break



######be verified#########


while True:
    msg="Alice ask to communicate with Bob..."
    print("ALice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))

####gen
    a_1,a_2,r,t_1,t_2=gen()
    print("gen done")
    msg="ALice generate the parameter"
    print("ALice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))    
    
####sign
    W_1,W_1_5,W_2_5,z,z_5,c,y,y_5,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5=sign(a_1,a_2,r,t_1,t_2)
    print("sign done")
    msg="ALice join and sign"
    print("ALice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))

    print("___________")
    print("W_1:",W_1)
    print("W_1_5:",W_1_5)
    print("W_2_5:",W_2_5)
    print("t_1:",t_1)
    print("t_2:",t_2)
    print("c:",c)
    print("a_1_T:",a_1_T)
    print("a_1_T_sig_5:",a_1_T_sig_5)
    print("a_2_T:",a_2_T)
    print("a_2_T_sig_5:",a_2_T_sig_5)
    print("z:",z)
    print("z_5:",z_5)

    msg="ALice send its sig to Bob"
    print("ALice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))

    user('192.168.201.131', 6970,W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5)
    
    msg="ALice sending over."
    print("ALice send: ", msg)
    client.send(msg.encode('utf-8'))#将发送的数据进行编码
    a=client.recv(1024)#接受服务端的信息，最大数据为1k
    print(a.decode('utf-8'))    
    
    client.close()
    break


