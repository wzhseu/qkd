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
    else:
        print("认证失败")
    return 0



import socket


def server(port):
    server = socket.socket()          # 创建socket对象
    server.bind(("localhost", port))  # 绑定要监听的端口port
    print("waiting the call")
    server.listen(5)
    data = tuple()
    conn, addr = server.accept()     # 在此处监听端口号
    print("the call has comming")
    while True:
        d = conn.recv(1024)
        if d.decode('utf-8') == 'finished':    # 收到finished代表client发送数据结束
            conn.close()                       # 关闭连接
            break
        else:
            data = data + (d.decode('utf-8'),)  # 将数据存在元组data中
            conn.send("receive".encode(encoding='utf-8'))  # 向client发送”receive"表示收到
    return data



import socket


def user(addr, port, *value):
    client = socket.socket()      # 创建socket对象
    client.connect((addr, port))  # 向指定地址和端口的服务端发起连接请求
    num = len(value)              # 获取数据大小，方便后面的循环
    i = 1
    client.send(value[0].encode(encoding='utf-8'))  # 依次发送value中的数据
    while i < num:
        data = client.recv(1024)
        if data.decode('utf-8') == "receive":      # 收到“receive”再发送下一次数据
            client.send(value[i].encode(encoding='utf-8'))
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
    while i < l:
        symbol=x[i]
        if(symbol=='+'):
            operation='+'
        if(symbol=='-'):
            operation='-'  
        while '0' <= symbol <= '9':
            coe += symbol
            i+=1
            symbol=x[i]
        if symbol=='a':
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
        if (index!= ''):
            if(coe==''):
                coe='1'
            if(operation=='+'):
                y[d,0]+=int(coe)*zeta^int(index)
            else:
                y[d,0]+=-int(coe)*zeta^int(index) 
            coe=''
            index=''
        elif (symbol==']'):
            if(coe==''):
                coe='0'
            if(operation=='+'):
                y[d,0]+=int(coe)
            else:
                y[d,0]+=-int(coe)
            coe=''
            operation='+'
        if symbol=='\n':
            d+=1
        i+=1
    return y



W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5=server(6969);
W_1,W_1_5,W_2_5,t_1,t_2=str2m(W_1,1),str2m(W_1_5,1),str2m(W_2_5,1),str2m(t_1,1),str2m(t_2,1)
c=int(c)
a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5=str2m(a_1_T,3).transpose(),str2m(a_1_T_sig_5,3).transpose(),str2m(a_2_T,3).transpose(),str2m(a_2_T_sig_5,3).transpose()
z,z_5=str2m(z,3),str2m(z_5,3)
verify(W_1,W_1_5,W_2_5,t_1,t_2,c,a_1_T,a_1_T_sig_5,a_2_T,a_2_T_sig_5,z,z_5);




