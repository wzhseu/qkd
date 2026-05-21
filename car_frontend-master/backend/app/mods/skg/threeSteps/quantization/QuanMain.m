clear all;
MseqLength = 4095;
ChannelSamplingTimes = 300;
Estimated_CSI = [];

j = 1;

% path1 = strcat('quantization/my_wave/' , 'waveform_', num2str(index), '.data');

for index = 0:ChannelSamplingTimes
%采集到了719个信号
    %% 判断信号的有效性
%     path1 = strcat('/Users/kailin/云盘空间/OneDrive/OneDrive - stu.xidian.edu.cn/量子挑战杯/Secret Key Generation/Wave-Alice/' , 'waveform_', num2str(index), '.data');
    path1 = strcat('mods/skg/threeSteps/quantization/my_wave/' , 'waveform_', num2str(index), '.data');
% Change the path1 for importing the matlab engine in python --22.7.10 gyt
    operator = dir(path1);
    Sizes_File = operator.bytes;
    
    if Sizes_File == 0  %Alice或者Bob这一次没有采集到信号
        continue
    end
    %% 信号的对齐
    mseq = read_complex_binary('waveform.data',MseqLength);
    wave = abs(read_complex_binary(path1));
    
    %
    [C21,lag21] = xcorr(wave,mseq);
    C21 = C21/max(C21);
    [M21,I21] = max(C21);
    t21 = lag21(I21);
   

    if t21 > 0
        continue
    end

    wave = wave(-t21:-t21 + MseqLength -1);

    %% 信道估计
    F_mseq = fft(mseq,64);
    F_wave = fft(wave,64);
    Estimated_CSI(j) = LSestimate(F_mseq,F_wave);
    j = j + 1;
end
%% 取信道状态信息的绝对值并进行 0-1 归一化处理
CSIabs = abs(Estimated_CSI);

nMax = max(CSIabs); nMin = min(CSIabs);
NormCSIabs = (CSIabs - nMin)/(nMax - nMin);
NormCSIabs = transpose(NormCSIabs);
%% 量化
Q =  2;
x = zeros(1,2^Q);
for i = 1:2^Q
    x(i) = i/(2^Q);
end

[F,xi]= ksdensity(10*log10(NormCSIabs(:,1)), 10*log10(NormCSIabs(:,1)), ...
    'function','cdf', 'width',.35);

index = zeros(1,2^Q);
for i = 1:2^Q
    index(i) = max(find(sort(F) <= x(i)));
end
xi = sort(xi);
interval = xi(index);
gray = {'00' ;'01'; '10' ;'11' };

% 量化样本点数
n = length(NormCSIabs);
k =zeros(1,n);
for i = 1:n
    temp = 10*log10(NormCSIabs(i));
    if isempty(find(temp >interval))
        k(i) = 0;
    else
        k(i) = max(find(temp >interval));
    end
end

for i = 1:n
    key{i}= gray{k(i)+1};
end

SecretKey_Quantized = '';
for i = 1:length(key)
    SecretKey_Quantized = strcat(SecretKey_Quantized,key{i});
end
%% 量化后的密钥写入文件中
save('~/code/skg-client/mods/skg/threeSteps/quantization/SecretKeyQuantized.mat','SecretKey_Quantized');

fprintf('Quantization Done!\n');
