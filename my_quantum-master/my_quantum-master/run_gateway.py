#!/usr/bin/env python3
"""
QKD边缘网关数据库系统启动脚本
同时启动:
- Flask Web服务器 (端口5002)
- Socket服务器 (端口9000，供小车获取密钥)
"""
import sys
import os
import configparser

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gateway_app.app import app
from gateway_app.socket_server import KeySocketServer

if __name__ == '__main__':
    # 读取配置
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gateway_app', 'config.ini')
    cfg.read(config_path, encoding='utf-8')
    
    # 获取端口配置和SM4密钥
    web_port = cfg.getint('server', 'port', fallback=5002)
    socket_port = cfg.getint('socket_server', 'port', fallback=9000)
    sm4_key = cfg.get('socket_server', 'sm4_secret_key', fallback=None)
    
    # 启动 Socket 服务器
    socket_server = KeySocketServer(port=socket_port, app=app, sm4_key=sm4_key)
    socket_server.start()
    
    print(f"\n{'='*60}")
    print(f"  QKD边缘网关系统启动")
    print(f"{'='*60}")
    print(f"  Web管理界面: http://localhost:{web_port}")
    print(f"  Socket服务器: localhost:{socket_port}")
    print(f"  SM4加密: {'已启用' if sm4_key else '未启用（明文传输）'}")
    print(f"  小车发送 'get_key' 获取SM4加密的密钥")
    print(f"{'='*60}\n")
    
    try:
        app.run(host='0.0.0.0', port=web_port, debug=False)
    finally:
        socket_server.stop()
