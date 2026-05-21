clear
paddings=randi([0,1],1,48);

bitstring=randi([0,1],1,80); %产生随机字符r
CodeWord=ConvECC([bitstring paddings],1);%进行卷积编码，第一个参数是编码的信息元，第二个参数1代表这是编码操作

save('SharedCodeword','CodeWord');