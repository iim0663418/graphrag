#!/usr/bin/env python3
"""
GraphRAG 問題診斷腳本
"""

import os
import sys
import logging

# 設置路徑
sys.path.insert(0, '..')

def test_basic_functionality():
    """測試基本功能"""
    print("🔍 GraphRAG 基本功能測試")
    print("=" * 30)
    
    try:
        # 1. 測試配置加載
        from graphrag.config import create_graphrag_config
        config = create_graphrag_config(root_dir='.')
        
        print("✅ 配置加載成功")
        print(f"   LLM: {config.llm.model}")
        print(f"   Embedding: {config.embeddings.llm.model}")
        
        # 2. 測試輸入文件
        input_files = []
        if os.path.exists('input'):
            for f in os.listdir('input'):
                if f.endswith('.txt'):
                    path = os.path.join('input', f)
                    size = os.path.getsize(path)
                    input_files.append((f, size))
        
        print(f"✅ 輸入文件: {len(input_files)} 個")
        for name, size in input_files:
            print(f"   {name}: {size} bytes")
        
        # 3. 測試 API 連接
        from openai import OpenAI
        client = OpenAI(api_key='lm-studio', base_url='http://localhost:1234/v1')
        
        # 測試 LLM
        try:
            response = client.chat.completions.create(
                model='qwen/qwen3-4b-2507',
                messages=[{'role': 'user', 'content': 'Hello'}],
                max_tokens=5
            )
            print("✅ LLM 連接正常")
        except Exception as e:
            print(f"❌ LLM 連接失敗: {e}")
            return False
        
        # 測試 Embedding
        try:
            embed_response = client.embeddings.create(
                model='nomic-embed-text-v1.5',
                input='test'
            )
            print("✅ Embedding 連接正常")
        except Exception as e:
            print(f"❌ Embedding 連接失敗: {e}")
            return False
        
        # 4. 嘗試最小化索引
        print("\n🔄 嘗試最小化索引...")
        
        # 設置簡單日誌
        logging.basicConfig(level=logging.INFO)
        
        from graphrag.index.run import run_pipeline_with_config
        
        # 清理輸出目錄
        import shutil
        if os.path.exists('output'):
            shutil.rmtree('output')
        
        # 運行索引
        result = run_pipeline_with_config(config)
        
        # 檢查結果
        output_files = []
        if os.path.exists('output'):
            for root, dirs, files in os.walk('output'):
                output_files.extend(files)
        
        print(f"📊 生成文件: {len(output_files)} 個")
        
        if output_files:
            print("✅ 索引成功！")
            for f in output_files[:5]:
                print(f"   {f}")
            return True
        else:
            print("❌ 索引未生成輸出")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
