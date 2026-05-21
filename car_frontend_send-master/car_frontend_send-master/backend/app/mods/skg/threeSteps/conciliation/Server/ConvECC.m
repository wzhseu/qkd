function y = ConvECC(data,type)
%卷积编码函数，其中type参数控制函数的功能，若type=1
%则进行卷积编码操作，data此时为传入进来的信息比特；
%若type=2，则进行卷积纠错（解码）操作，data此时为码字。
if type==1
    trellis = poly2trellis(7,[133,171]);
    codedout = convenc(data,trellis);
    y=codedout;
elseif type==2
    tbdepth=48;
    trellis = poly2trellis(7,[133,171]);
    conv_decode = vitdec(data,trellis,tbdepth,'cont','hard');
    y=conv_decode(tbdepth+1:end);
end