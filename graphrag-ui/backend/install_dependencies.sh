#!/bin/bash

# GraphRAG UI Backend 依賴安裝腳本
# 用途：安裝所有必要的依賴，包括 GraphRAG 本地版本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "GraphRAG UI Backend - 依賴安裝"
echo "=========================================="

# 檢查 Python 版本
echo "✓ 檢查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "  Python 版本: $PYTHON_VERSION"

PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 10 ] || [ "$PYTHON_MINOR" -gt 12 ]; then
    echo "❌ 錯誤：需要 Python 3.10-3.12，當前版本為 $PYTHON_VERSION"
    exit 1
fi

# 檢查或創建虛擬環境
if [ ! -d "venv" ]; then
    echo "✓ 創建 Python 虛擬環境..."
    python -m venv venv
else
    echo "✓ 虛擬環境已存在"
fi

# 啟動虛擬環境
echo "✓ 啟動虛擬環境..."
source venv/bin/activate

# 升級 pip
echo "✓ 升級 pip..."
pip install --upgrade pip

# 安裝 requirements.txt 中的依賴
echo "✓ 安裝基礎依賴..."
pip install -r requirements.txt

# 從專案根目錄安裝 GraphRAG（本地開發模式）
echo "✓ 安裝 GraphRAG 本地版本..."
GRAPHRAG_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$GRAPHRAG_ROOT/pyproject.toml" ]; then
    echo "  找到 GraphRAG 專案：$GRAPHRAG_ROOT"
    pip install -e "$GRAPHRAG_ROOT"
    echo "✅ GraphRAG 本地版本安裝成功（可編輯模式）"
else
    echo "⚠️  警告：找不到 GraphRAG 專案根目錄"
    echo "  預期位置：$GRAPHRAG_ROOT/pyproject.toml"
    echo "  嘗試從 PyPI 安裝..."
    pip install graphrag
fi

# 驗證安裝
echo ""
echo "=========================================="
echo "✓ 驗證依賴安裝..."
echo "=========================================="

python -c "
import sys
packages = [
    'fastapi',
    'uvicorn',
    'pandas',
    'pydantic',
    'datashaper',
    'graphrag'
]

all_ok = True
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg:20s} OK')
    except ImportError as e:
        print(f'❌ {pkg:20s} FAILED: {e}')
        all_ok = False

if not all_ok:
    print('')
    print('❌ 某些依賴安裝失敗')
    sys.exit(1)
else:
    print('')
    print('✅ 所有依賴驗證通過！')
"

echo ""
echo "=========================================="
echo "✅ 依賴安裝完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 執行 ./start_backend.sh 啟動後端服務"
echo "  2. 或執行 ./run.sh 啟動服務（會自動重新安裝依賴）"
echo ""
