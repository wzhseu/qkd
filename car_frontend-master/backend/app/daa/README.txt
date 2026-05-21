git clone git@gitee.com:secretgyt/daa.git

git add .

git commit -m"说明"



更新项目到本地
git pull origin master

上传本地代码
git push origin master

本地强制覆盖远程
git push -f origin master

远程强制覆盖本地
git fetch --all
git reset --hard origin/master


git remote add origin git@gitee.com:secretgyt/daa.git



左小 address:
192.168.0.107

大 address:
192.168.0.106

右 address:
192.168.0.105


+++++++++++++++++++++++++++++++++++++

if you are alice:

sage alice.sage

+++++++++++++++++++++++++++++

if you are bob:

sage bob.sage

+++++++++++++++++++++++++++++

if you are host:

python3 qkd_server.py


