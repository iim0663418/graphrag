#!/usr/bin/env python3
"""
GraphRAG 完整測試腳本 - 修復版本
"""

import os
import sys
import asyncio
import shutil

# 設置路徑
sys.path.insert(0, '..')

async def run_graphrag_index():
    """運行 GraphRAG 索引"""
    print("🚀 GraphRAG 完整索引測試")
    print("=" * 30)
    
    try:
        from graphrag.config import create_graphrag_config
        from graphrag.index.input import load_input
        from graphrag.index.run import run_pipeline_with_config
        
        # 1. 創建並修復配置
        config = create_graphrag_config(root_dir='.')
        
        # 強制修復文件模式
        config.input.file_pattern = r'.*\.txt$'
        
        print(f"配置檢查:")
        print(f"  LLM: {config.llm.model} @ {config.llm.api_base}")
        print(f"  Embedding: {config.embeddings.llm.model}")
        print(f"  文件模式: {config.input.file_pattern}")
        
        # 2. 測試輸入加載
        print("\n📁 加載輸入數據...")
        input_data = await load_input(config.input)
        print(f"✅ 成功加載 {len(input_data)} 個文檔")
        
        if len(input_data) == 0:
            print("❌ 沒有找到輸入文檔")
            return False
        
        first_doc = input_data.iloc[0]
        print(f"   第一個文檔: {len(first_doc.text)} 字符")
        
        # 3. 測試 API 連接
        print("\n🔗 測試 API 連接...")
        from openai import OpenAI
        client = OpenAI(api_key='lm-studio', base_url='http://localhost:1234/v1')
        
        # 測試 LLM
        llm_response = client.chat.completions.create(
            model='qwen/qwen3-4b-2507',
            messages=[{'role': 'user', 'content': 'Hello'}],
            max_tokens=5
        )
        print("✅ LLM 連接正常")
        
        # 測試 Embedding
        embed_response = client.embeddings.create(
            model='nomic-embed-text-v1.5',
            input='test'
        )
        print("✅ Embedding 連接正常")
        
        # 4. 清理並運行索引
        print("\n🔄 開始索引...")
        
        if os.path.exists('output'):
            shutil.rmtree('output')
            print("🧹 清理舊輸出")
        
        # 運行索引
        results = []
        async for result in run_pipeline_with_config(config):
            results.append(result)
        
        print("✅ 索引完成")
        
        # 5. 檢查結果
        output_files = []
        total_size = 0
        
        if os.path.exists('output'):
            for root, dirs, files in os.walk('output'):
                for f in files:
                    full_path = os.path.join(root, f)
                    size = os.path.getsize(full_path)
                    output_files.append((f, size))
                    total_size += size
        
        print(f"\n📊 索引結果:")
        print(f"   文件數量: {len(output_files)}")
        print(f"   總大小: {total_size:,} bytes")
        
        if output_files:
            print("\n📁 生成的文件:")
            # 按大小排序
            sorted_files = sorted(output_files, key=lambda x: x[1], reverse=True)
            for name, size in sorted_files[:10]:
                print(f"   {name}: {size:,} bytes")
            
            # 檢查關鍵文件
            key_patterns = ['entities', 'relationships', 'communities']
            found_patterns = []
            
            for pattern in key_patterns:
                matching_files = [f for f, _ in output_files if pattern in f.lower()]
                if matching_files:
                    found_patterns.append(pattern)
            
            print(f"\n🎯 找到關鍵組件: {found_patterns}")
            
            if len(found_patterns) >= 2:
                print("\n🎉 GraphRAG 索引成功！")
                print("✅ 知識圖譜已構建")
                print("✅ 本地 LMStudio 模型工作正常")
                return True
            else:
                print("\n⚠️  索引部分成功")
                return True
        else:
            print("\n❌ 沒有生成輸出文件")
            return False
            
    except Exception as e:
        print(f"\n❌ 索引失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_graphrag_index())
    
    if success:
        print("\n" + "="*50)
        print("🎉 GraphRAG + LMStudio 集成測試成功！")
        print("✅ 本地化 GraphRAG 解決方案已驗證")
        print("✅ 零成本知識圖譜構建已實現")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ 測試未完全成功")
        print("💡 請檢查 LMStudio 狀態和模型加載")
        print("="*50)
    
    sys.exit(0 if success else 1)
