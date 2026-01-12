#!/usr/bin/env python3
"""
GraphRAG 中文處理監控腳本
實時監控索引進度和問題
"""

import time
import subprocess
import json
import os
from pathlib import Path

def check_lmstudio():
    """檢查 LMStudio 狀態"""
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:1234/v1/models'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data['data'][0]['id'] if data.get('data') else None
    except:
        return None

def monitor_logs():
    """監控日誌文件"""
    output_dir = Path('output')
    if not output_dir.exists():
        return None
    
    # 找到最新的日誌文件
    log_files = list(output_dir.glob('*/reports/indexing-engine.log'))
    if not log_files:
        return None
    
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    
    # 統計關鍵指標
    with open(latest_log, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stats = {
        'errors': content.count('Error Invoking LLM'),
        'http_ok': content.count('HTTP/1.1 200 OK'),
        'timeouts': content.count('timeout'),
        'file_size': len(content)
    }
    
    return stats

def main():
    print("🔍 GraphRAG 中文處理監控啟動")
    
    # 檢查 LMStudio
    model = check_lmstudio()
    if model:
        print(f"✅ LMStudio 運行中: {model}")
    else:
        print("❌ LMStudio 未運行")
        return
    
    print("\n📊 開始監控 (每 30 秒更新)...")
    print("按 Ctrl+C 停止監控")
    
    try:
        while True:
            stats = monitor_logs()
            if stats:
                print(f"\n⏰ {time.strftime('%H:%M:%S')}")
                print(f"📝 日誌大小: {stats['file_size']:,} bytes")
                print(f"✅ 成功請求: {stats['http_ok']}")
                print(f"❌ LLM 錯誤: {stats['errors']}")
                print(f"⏱️ 超時錯誤: {stats['timeouts']}")
                
                # 計算成功率
                total_requests = stats['http_ok'] + stats['errors']
                if total_requests > 0:
                    success_rate = (stats['http_ok'] / total_requests) * 100
                    print(f"📈 成功率: {success_rate:.1f}%")
            else:
                print(f"⏰ {time.strftime('%H:%M:%S')} - 等待日誌文件...")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n🛑 監控已停止")

if __name__ == "__main__":
    main()
