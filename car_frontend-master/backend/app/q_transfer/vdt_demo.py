from app.q_transfer.video_receive import socket_service
import os
import socket



def VDT():
 
    print("开始视频传输")
    res = socket_service()
    if (res):
        return True
    
