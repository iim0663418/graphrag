#!/bin/bash

# GraphRAG UI Backend - 設置驗證腳本
# 用途：驗證環境設置是否正確

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "GraphRAG UI Backend - 環境驗證"
echo "=========================================="
echo ""

# 檢查虛擬環境
echo "1. 檢查虛擬環境..."
if [ -d "venv" ]; then
    echo "   ✅ 虛擬環境存在"
else
    echo "   ❌ 虛擬環境不存在"
    echo "   請執行: ./install_dependencies.sh"
    exit 1
fi

# 啟動虛擬環境
source venv/bin/activate

# 檢查 Python 版本
echo ""
echo "2. 檢查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "   Python 版本: $PYTHON_VERSION"

PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ] && [ "$PYTHON_MINOR" -le 12 ]; then
    echo "   ✅ Python 版本符合要求（3.10-3.12）"
else
    echo "   ⚠️  警告：Python 版本可能不相容（建議 3.10-3.12）"
fi

# 檢查必要模組
echo ""
echo "3. 檢查必要模組..."

python << 'EOF'
import sys

modules = {
    'fastapi': 'FastAPI Web 框架',
    'uvicorn': 'ASGI 伺服器',
    'pandas': '數據處理',
    'pydantic': '數據驗證',
    'datashaper': 'GraphRAG 數據處理核心',
    'graphrag': 'GraphRAG 主模組',
    'openai': 'OpenAI API 客戶端',
    'tiktoken': 'Token 計數',
    'numpy': '數值計算',
    'networkx': '圖形處理',
}

all_ok = True
for module, description in modules.items():
    try:
        __import__(module)
        print(f'   ✅ {module:20s} - {description}')
    except ImportError as e:
        print(f'   ❌ {module:20s} - {description} (未安裝)')
        all_ok = False

print()
if not all_ok:
    print('   ❌ 某些模組未安裝')
    print('   請執行: ./install_dependencies.sh')
    sys.exit(1)
else:
    print('   ✅ 所有必要模組已安裝')
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# 檢查 GraphRAG 安裝模式
echo ""
echo "4. 檢查 GraphRAG 安裝模式..."

python << 'EOF'
import graphrag
import os

graphrag_path = graphrag.__file__
graphrag_dir = os.path.dirname(graphrag_path)

# 檢查是否為開發模式（.egg-link 或直接在專案目錄）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if project_root in graphrag_dir:
    print(f'   ✅ GraphRAG 以開發模式安裝（可編輯）')
    print(f'   路徑: {graphrag_dir}')
else:
    print(f'   ℹ️  GraphRAG 以標準模式安裝')
    print(f'   路徑: {graphrag_dir}')

print(f'   版本: {graphrag.__version__ if hasattr(graphrag, "__version__") else "未知"}')
EOF

# 檢查必要文件
echo ""
echo "5. 檢查必要文件..."

FILES=(
    "main.py:主應用程式"
    "requirements.txt:依賴列表"
    "start_backend.sh:啟動腳本"
    "install_dependencies.sh:安裝腳本"
    "services/graphrag_service.py:GraphRAG 服務"
)

for file_desc in "${FILES[@]}"; do
    IFS=':' read -r file desc <<< "$file_desc"
    if [ -f "$file" ] || [ -d "$(dirname "$file")" ]; then
        echo "   ✅ $file - $desc"
    else
        echo "   ❌ $file - $desc (缺失)"
    fi
done

# 檢查環境變數設置（可選）
echo ""
echo "6. 檢查環境變數（可選）..."

if [ -n "$GRAPHRAG_SETTINGS_PATH" ]; then
    echo "   ℹ️  GRAPHRAG_SETTINGS_PATH: $GRAPHRAG_SETTINGS_PATH"
else
    echo "   ℹ️  GRAPHRAG_SETTINGS_PATH: 未設置（將使用預設值）"
fi

if [ -n "$GRAPHRAG_DATA_DIR" ]; then
    echo "   ℹ️  GRAPHRAG_DATA_DIR: $GRAPHRAG_DATA_DIR"
else
    echo "   ℹ️  GRAPHRAG_DATA_DIR: 未設置（將使用預設值）"
fi

# 測試導入後端主程式
echo ""
echo "7. 測試導入後端主程式..."

python << 'EOF'
import sys
import os

# 將當前目錄加入路徑
sys.path.insert(0, os.getcwd())

try:
    # 測試導入（不實際啟動服務）
    from main import app
    print('   ✅ 主程式導入成功')
    print(f'   應用名稱: {app.title}')
    print(f'   應用版本: {app.version}')
except Exception as e:
    print(f'   ❌ 主程式導入失敗: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

# 總結
echo ""
echo "=========================================="
echo "✅ 環境驗證完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 執行 ./start_backend.sh 啟動後端服務"
echo "  2. 訪問 http://localhost:8000/docs 查看 API 文檔"
echo ""
echo "如需重新安裝依賴："
echo "  ./install_dependencies.sh"
echo ""
