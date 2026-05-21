clear;
%% 载入codeword
load('SharedCodeword','CodeWord');
%% 载入量化的密钥
load('mods/skg/threeSteps/quantization/SecretKeyQuantized.mat','SecretKey_Quantized');

%%
SecretKey_Quantized = str2num(SecretKey_Quantized(:))';
SecretKey_Quantized = SecretKey_Quantized(1,1:128);
CodeWord = CodeWord(1,1:128);
SecureSketch=double(xor(SecretKey_Quantized,CodeWord));

%% 保存，接下来由Server传递给CLient
save('~/code/skg-client/mods/skg/threeSteps/conciliation/Server/Secure_Sketch.mat','SecureSketch');

fid = fopen('mods/skg/threeSteps/conciliation/OriginalKey.txt','wt');
fprintf(fid,'%g',transpose(SecretKey_Quantized)); 
fclose(fid);

fprintf('Server Reconciliation Done!\n');
fprintf('Waiting for socket...\n');
