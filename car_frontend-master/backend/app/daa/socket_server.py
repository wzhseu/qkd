#!/usr/bin/env python
# -*- coding=utf-8 -*-


"""
file: recv.py
socket to
"""

import socket
import threading
import time
import sys
import os
import struct


def socket_to(addr, port, filepath):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((addr, port))
        s.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('Waiting connection...')

    while 1:
        conn, addr = s.accept()
        # t = threading.Thread(target=deal_data, args=(conn, addr))
        # t.start()
        deal_data(conn, addr, filepath)
        break


def deal_data(conn, addr, filepath):
    print('Accept new connection from {0}'.format(addr))
    # conn.settimeout(500)
    welcome = bytes('Hi, Welcome to the server!', 'utf-8')
    conn.send(welcome)

    while 1:
        fileinfo_size = struct.calcsize('128sl')
        buf = conn.recv(fileinfo_size)
        if buf:
            filename, filesize = struct.unpack('128sl', buf)
            filename = str(filename, 'utf-8')
            print(filename)
            print(filesize)
            fn = (str(filename)).strip('\00')
            #new_filename = os.path.join('./', 'new_' + fn)
            new_filename = os.path.join('', 'new_' + fn)
            print('file new name is {0}, filesize if {1}'.format(new_filename,
                                                                 filesize))

            recvd_size = 0  # 定义已接收文件的大小
            fp = open(filepath + new_filename, 'wb')
            print('start receiving...')

            while not recvd_size == filesize:
                if filesize - recvd_size > 1024:
                    data = conn.recv(1024)
                    recvd_size += len(data)
                else:
                    data = conn.recv(filesize - recvd_size)
                    recvd_size = filesize
                fp.write(data)
            fp.close()
            print('end receive...')
        conn.close()
        break



if __name__ == '__main__':
    socket_to(addr='192.168.158.128', port=6666, filepath='~/daa-qkd')
