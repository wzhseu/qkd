#!/usr/bin/env python3
"""
创建测试数据 - 用于演示和测试
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway_app import create_app, db
from gateway_app.db_ops import save_key, save_log
import random
import string
from datetime import datetime, timedelta

def generate_random_key(length=64):
    """生成随机密钥"""
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

def create_test_keys(count=50):
    """创建测试密钥"""
    print(f"正在创建 {count} 个测试密钥...")
    
    devices = ['device1', 'device2']
    sources = ['qkd_app', 'manual', 'test']
    
    for i in range(count):
        key_value = generate_random_key()
        device = random.choice(devices)
        source = random.choice(sources)
        
        key = save_key(key_value, device=device, source=source)
        
        # 随机标记一些为已使用
        if random.random() > 0.6:
            key.mark_used()
            db.session.commit()
        
        if (i + 1) % 10 == 0:
            print(f"  已创建 {i + 1} 个密钥...")
    
    print(f"✓ 成功创建 {count} 个测试密钥")

def create_test_logs(count=30):
    """创建测试日志"""
    print(f"正在创建 {count} 条测试日志...")
    
    levels = ['INFO', 'WARNING', 'ERROR']
    messages = [
        'System started successfully',
        'Key imported from file',
        'Key consumed by device',
        'Auto-import running',
        'Database backup completed',
        'Warning: Low key inventory',
        'Error: Failed to import file',
        'Device connected',
        'Device disconnected',
        'Key pool updated',
    ]
    
    for i in range(count):
        level = random.choice(levels)
        message = random.choice(messages)
        source = 'test'
        
        save_log(message, level=level, source=source)
        
        if (i + 1) % 10 == 0:
            print(f"  已创建 {i + 1} 条日志...")
    
    print(f"✓ 成功创建 {count} 条测试日志")

def main():
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("  创建测试数据")
        print("="*60 + "\n")
        
        # 创建测试密钥
        create_test_keys(50)
        print()
        
        # 创建测试日志
        create_test_logs(30)
        print()
        
        print("="*60)
        print("  测试数据创建完成！")
        print("="*60)
        print("\n访问 http://localhost:5002 查看数据\n")

if __name__ == '__main__':
    main()
