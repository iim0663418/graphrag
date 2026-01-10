#!/usr/bin/env python3
"""
GraphRAG Local 部署測試腳本

測試整個本地化 GraphRAG 系統是否能正常工作
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path

def check_environment():
    """檢查環境依賴"""
    print("🔍 檢查環境依賴...")
    
    # 檢查 Python 版本
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 10:
        print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"   ❌ Python 版本過低: {python_version}")
        return False
    
    # 檢查必要套件
    required_packages = ['lmstudio', 'graphrag', 'yaml']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (未安裝)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 需要安裝的套件: {', '.join(missing_packages)}")
        print("   執行: pip install lmstudio graphrag pyyaml")
        return False
    
    return True

def check_lmstudio():
    """檢查 LMStudio 狀態"""
    print("\n🎯 檢查 LMStudio 狀態...")
    
    try:
        import lmstudio as lms
        print(f"   ✅ LMStudio SDK 版本: {lms.__version__}")
        
        # 嘗試連接 LMStudio
        try:
            client = lms.get_default_client()
            print("   ✅ LMStudio 客戶端連接成功")
            return True
        except Exception as e:
            print(f"   ⚠️  LMStudio 服務未運行: {e}")
            print("   💡 請確保 LMStudio 應用程式已啟動")
            return False
            
    except ImportError:
        print("   ❌ LMStudio SDK 未安裝")
        return False

def create_test_config():
    """創建測試配置文件"""
    print("\n📝 創建測試配置...")
    
    config = {
        'llm': {
            'type': 'lmstudio_chat',
            'model': 'qwen/qwen3-4b-2507',
            'model_supports_json': True,
            'max_tokens': 4000,
            'temperature': 0.1
        },
        'embeddings': {
            'llm': {
                'type': 'lmstudio_embedding', 
                'model': 'nomic-embed-text-v1.5',
                'batch_size': 16
            }
        },
        'chunks': {
            'size': 300,
            'overlap': 100,
            'group_by_columns': ['id']
        },
        'input': {
            'type': 'file',
            'file_type': 'text',
            'base_dir': 'input',
            'file_encoding': 'utf-8',
            'file_pattern': '.*\\.txt$'
        },
        'cache': {
            'type': 'file',
            'base_dir': 'cache'
        },
        'storage': {
            'type': 'file',
            'base_dir': 'output'
        }
    }
    
    # 創建測試目錄
    test_dir = Path('test_deployment')
    test_dir.mkdir(exist_ok=True)
    
    # 寫入配置文件
    config_file = test_dir / 'settings.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"   ✅ 配置文件已創建: {config_file}")
    return test_dir, config_file

def create_test_data(test_dir):
    """創建測試數據"""
    print("\n📄 創建測試數據...")
    
    input_dir = test_dir / 'input'
    input_dir.mkdir(exist_ok=True)
    
    # 創建簡單的測試文本
    test_content = """
GraphRAG 是一個強大的知識圖譜檢索增強生成系統。

什麼是 GraphRAG？
GraphRAG 結合了圖形資料庫和大型語言模型的優勢，能夠從非結構化文本中提取實體和關係，
建構知識圖譜，並利用這些結構化知識來增強語言模型的回答品質。

主要特點：
1. 實體提取：自動識別文本中的重要實體
2. 關係建構：發現實體之間的關聯關係  
3. 社群檢測：識別相關實體的群組
4. 全域搜尋：基於整個知識圖譜的高層次查詢
5. 局域搜尋：基於特定實體的詳細查詢

應用場景：
- 企業知識管理
- 學術研究分析
- 文檔問答系統
- 智能客服助手

技術優勢：
GraphRAG 相比傳統 RAG 系統，能夠更好地理解文檔間的關聯性，
提供更準確和全面的回答。
"""
    
    test_file = input_dir / 'graphrag_intro.txt'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"   ✅ 測試數據已創建: {test_file}")
    return test_file

def test_graphrag_integration():
    """測試 GraphRAG 整合"""
    print("\n🧪 測試 GraphRAG 整合...")
    
    try:
        # 測試導入我們的適配器
        sys.path.append('.')
        from graphrag_local.adapters.lmstudio_chat_llm import LMStudioChatLLM
        from graphrag_local.adapters.lmstudio_embeddings_llm import LMStudioEmbeddingsLLM
        print("   ✅ 本地適配器導入成功")
        
        # 測試工廠函數
        from graphrag_local.lmstudio_factories import create_lmstudio_chat_llm, create_lmstudio_embeddings_llm
        print("   ✅ 工廠函數導入成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 整合測試失敗: {e}")
        return False

def run_indexing_test(test_dir, config_file):
    """運行索引測試"""
    print("\n🚀 運行 GraphRAG 索引測試...")
    
    try:
        # 切換到測試目錄
        original_dir = os.getcwd()
        os.chdir(test_dir)
        
        # 運行 GraphRAG 初始化
        print("   📋 初始化 GraphRAG...")
        result = subprocess.run(['graphrag', 'init', '--root', '.'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"   ❌ GraphRAG 初始化失敗: {result.stderr}")
            return False
        
        print("   ✅ GraphRAG 初始化成功")
        
        # 複製我們的配置
        import shutil
        shutil.copy('../settings.yaml', './settings.yaml')
        
        # 運行索引
        print("   🔄 開始索引處理...")
        result = subprocess.run(['graphrag', 'index', '--root', '.'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("   ✅ 索引處理成功")
            return True
        else:
            print(f"   ❌ 索引處理失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ 索引處理超時（5分鐘）")
        return False
    except Exception as e:
        print(f"   ❌ 索引測試異常: {e}")
        return False
    finally:
        os.chdir(original_dir)

def run_query_test(test_dir):
    """運行查詢測試"""
    print("\n❓ 運行查詢測試...")
    
    try:
        original_dir = os.getcwd()
        os.chdir(test_dir)
        
        # 測試全域查詢
        print("   🌐 測試全域查詢...")
        result = subprocess.run([
            'graphrag', 'query', 
            '--root', '.', 
            '--method', 'global',
            '--query', '什麼是 GraphRAG？'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("   ✅ 全域查詢成功")
            print(f"   📝 回答預覽: {result.stdout[:100]}...")
        else:
            print(f"   ❌ 全域查詢失敗: {result.stderr}")
            
        # 測試局域查詢
        print("   🎯 測試局域查詢...")
        result = subprocess.run([
            'graphrag', 'query',
            '--root', '.',
            '--method', 'local', 
            '--query', 'GraphRAG 的主要特點是什麼？'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("   ✅ 局域查詢成功")
            print(f"   📝 回答預覽: {result.stdout[:100]}...")
            return True
        else:
            print(f"   ❌ 局域查詢失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ 查詢測試超時")
        return False
    except Exception as e:
        print(f"   ❌ 查詢測試異常: {e}")
        return False
    finally:
        os.chdir(original_dir)

def main():
    """主測試流程"""
    print("=" * 60)
    print("🚀 GraphRAG Local 部署測試")
    print("=" * 60)
    
    # 環境檢查
    if not check_environment():
        print("\n❌ 環境檢查失敗，請先安裝必要依賴")
        return False
    
    # LMStudio 檢查
    lmstudio_ok = check_lmstudio()
    if not lmstudio_ok:
        print("\n⚠️  LMStudio 未就緒，將跳過實際模型測試")
    
    # 創建測試環境
    test_dir, config_file = create_test_config()
    test_file = create_test_data(test_dir)
    
    # 整合測試
    if not test_graphrag_integration():
        print("\n❌ GraphRAG 整合測試失敗")
        return False
    
    # 如果 LMStudio 就緒，進行完整測試
    if lmstudio_ok:
        print("\n🎯 LMStudio 就緒，開始完整測試...")
        
        # 索引測試
        if run_indexing_test(test_dir, config_file):
            # 查詢測試
            run_query_test(test_dir)
        
    else:
        print("\n💡 LMStudio 未就緒，跳過索引和查詢測試")
        print("   請啟動 LMStudio 並載入模型後重新運行測試")
    
    print("\n" + "=" * 60)
    print("📋 測試完成")
    print("=" * 60)
    
    print(f"\n📁 測試文件位置: {test_dir.absolute()}")
    print("🔧 如需手動測試，請執行:")
    print(f"   cd {test_dir}")
    print("   graphrag index --root .")
    print("   graphrag query --method global --query '什麼是 GraphRAG？'")
    
    return True

if __name__ == "__main__":
    main()
