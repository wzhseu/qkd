#!/usr/bin/env python3
"""
从目录批量导入密钥文件
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway_app import create_app
from gateway_app.db_ops import ingest_keys_from_dir, save_log

def main():
    parser = argparse.ArgumentParser(description='从目录批量导入密钥文件')
    parser.add_argument('dir_path', help='要扫描的目录路径')
    parser.add_argument('--device', default='device1', help='设备标识 (device1/device2)')
    parser.add_argument('--source', default='manual-import', help='来源标识')
    parser.add_argument('--per-line', action='store_true', help='是否按行读取（每行一个密钥）')
    parser.add_argument('--recursive', action='store_true', help='是否递归扫描子目录')
    parser.add_argument('--patterns', default='*.txt,*.key', help='文件匹配模式（逗号分隔）')
    
    args = parser.parse_args()
    
    # 解析模式
    patterns = [p.strip() for p in args.patterns.split(',') if p.strip()]
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("  批量导入密钥文件")
        print("="*60 + "\n")
        print(f"目录路径:     {args.dir_path}")
        print(f"设备标识:     {args.device}")
        print(f"来源标识:     {args.source}")
        print(f"按行读取:     {args.per_line}")
        print(f"递归扫描:     {args.recursive}")
        print(f"文件模式:     {', '.join(patterns)}")
        print()
        
        # 检查目录是否存在
        if not os.path.isdir(args.dir_path):
            print(f"❌ 错误: 目录不存在: {args.dir_path}")
            return 1
        
        print("开始扫描和导入...")
        
        # 导入密钥
        summary = ingest_keys_from_dir(
            args.dir_path,
            device=args.device,
            source=args.source,
            per_line=args.per_line,
            recursive=args.recursive,
            file_patterns=patterns,
            skip_imported=True,
        )
        
        print()
        print("="*60)
        print("  导入完成")
        print("="*60)
        print(f"匹配文件数:   {summary['files']}")
        print(f"导入密钥数:   {summary['ingested']}")
        print()
        
        if summary['matched_files']:
            print("已导入文件:")
            for f in summary['matched_files'][:10]:
                print(f"  - {f}")
            if len(summary['matched_files']) > 10:
                print(f"  ... 还有 {len(summary['matched_files']) - 10} 个文件")
        
        print()
        
        # 记录日志
        save_log(
            f"Manual import: {summary['ingested']} keys from {summary['files']} files",
            source='tools/import_keys_from_dir'
        )
        
        return 0

if __name__ == '__main__':
    sys.exit(main())
