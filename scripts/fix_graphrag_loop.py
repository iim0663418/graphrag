#!/usr/bin/env python3
"""
GraphRAG 無限循環修復腳本
修復 GraphRAG 實體提取中的無限循環問題
"""

import os
import re
import sys

def find_graphrag_extractor():
    """查找 GraphRAG 提取器文件"""
    try:
        import graphrag.index.graph.extractors.graph.graph_extractor as target_module
        return target_module.__file__
    except ImportError:
        print("❌ 無法導入 GraphRAG 模組")
        return None

def patch_extractor(file_path):
    """修補提取器文件"""
    print(f"🔍 修補文件: {file_path}")
    
    # 讀取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已修補
    if "# PATCH: Zero-yield stopping" in content:
        print("⚠️  文件已修補，跳過")
        return True
    
    # 備份
    backup_path = file_path + ".backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已備份至: {backup_path}")
    
    # 查找修補點
    pattern = r'(results \+= response\.output or "")'
    match = re.search(pattern, content)
    
    if not match:
        print("❌ 找不到修補點")
        return False
    
    # 獲取縮進
    line_start = content.rfind('\n', 0, match.start()) + 1
    indentation = content[line_start:match.start()]
    
    # 構建修補代碼
    patch_code = f"""
{indentation}# PATCH: Zero-yield stopping - 如果沒有新內容則停止
{indentation}if not (response.output or "").strip():
{indentation}    print(f"Gleaning {{i+1}} 產生空結果，提前停止")
{indentation}    break"""
    
    # 應用修補
    new_content = content[:match.end()] + patch_code + content[match.end():]
    
    # 寫回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 修補完成")
    return True

def main():
    print("🔧 GraphRAG 無限循環修復工具")
    print("=" * 30)
    
    # 查找文件
    extractor_file = find_graphrag_extractor()
    if not extractor_file:
        return False
    
    # 應用修補
    success = patch_extractor(extractor_file)
    
    if success:
        print("\n🎉 修復完成！")
        print("現在可以安全地設置 max_gleanings > 0")
    else:
        print("\n❌ 修復失敗")
    
    return success

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
