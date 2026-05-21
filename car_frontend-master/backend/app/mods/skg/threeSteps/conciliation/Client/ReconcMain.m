
clear;
%% 载入codeword
load('SharedCodeword','CodeWord');
%% 载入量化的密钥
load('mods/skg/quantization/SecretKeyQuantized.mat','SecretKey_Quantized');
%% 载入secure sketch
load('new_Secure_Sketch','SecureSketch');

CodeWord = CodeWord(1,1:128);
%%
RecoveredKey = double(xor(SecureSketch,CodeWord));
fid = fopen('mods/skg/conciliation/OriginalKey.txt','wt');
fprintf(fid,'%g',transpose(RecoveredKey)); 
fclose(fid);

fprintf('Client Reconciliation Done!\n');
