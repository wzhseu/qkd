#!/usr/bin/env python3
"""
查看数据库统计信息
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway_app import create_app
from gateway_app.db_ops import get_key_stats, get_daily_stats
from gateway_app.models import Key, RunLog, ImportedFile

def main():
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("  QKD边缘网关数据库统计")
        print("="*60 + "\n")
        
        # 密钥统计
        stats = get_key_stats()
        print("📊 密钥统计:")
        print(f"  总密钥数:        {stats['total']}")
        print(f"  未使用密钥:      {stats['unused']}")
        print(f"  已使用密钥:      {stats['used']}")
        print(f"  Device1可用:     {stats['device1_unused']}")
        print(f"  Device2可用:     {stats['device2_unused']}")
        print(f"  未使用总长度:    {stats['total_unused_length']} 字节")
        print()
        
        # 日志统计
        total_logs = RunLog.query.count()
        info_logs = RunLog.query.filter_by(level='INFO').count()
        warning_logs = RunLog.query.filter_by(level='WARNING').count()
        error_logs = RunLog.query.filter_by(level='ERROR').count()
        
        print("📝 日志统计:")
        print(f"  总日志数:        {total_logs}")
        print(f"  INFO级别:        {info_logs}")
        print(f"  WARNING级别:     {warning_logs}")
        print(f"  ERROR级别:       {error_logs}")
        print()
        
        # 导入文件统计
        total_files = ImportedFile.query.count()
        print("📁 导入文件统计:")
        print(f"  已导入文件数:    {total_files}")
        
        if total_files > 0:
            latest = ImportedFile.query.order_by(ImportedFile.imported_at.desc()).first()
            print(f"  最新导入文件:    {os.path.basename(latest.file_path)}")
            print(f"  最新导入时间:    {latest.imported_at}")
        print()
        
        # 每日统计
        daily = get_daily_stats(days=7)
        if daily:
            print("📈 最近7天统计:")
            print(f"  {'日期':<12} {'导入':<8} {'使用':<8} {'Device1':<10} {'Device2':<10}")
            print("  " + "-"*56)
            for stat in daily:
                print(f"  {stat['date']:<12} "
                      f"{stat['imported_count']:<8} "
                      f"{stat['used_count']:<8} "
                      f"{stat['device1_count']:<10} "
                      f"{stat['device2_count']:<10}")
        print()
        
        # 按设备分类统计
        device1_total = Key.query.filter_by(device='device1').count()
        device2_total = Key.query.filter_by(device='device2').count()
        
        print("🔧 按设备分类:")
        print(f"  Device1总数:     {device1_total}")
        print(f"  Device2总数:     {device2_total}")
        print()
        
        print("="*60)
        print()

if __name__ == '__main__':
    main()
