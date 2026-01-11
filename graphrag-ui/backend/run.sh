#!/bin/bash

# GraphRAG UI Backend 啟動腳本

set -e

echo "🚀 Starting GraphRAG UI Backend..."

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# 啟動虛擬環境
echo "✓ Activating virtual environment..."
source venv/bin/activate

# 安裝依賴
echo "✓ Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 從專案根目錄安裝 GraphRAG（本地開發模式）
echo "✓ Installing GraphRAG from local source..."
GRAPHRAG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -f "$GRAPHRAG_ROOT/pyproject.toml" ]; then
    pip install -q -e "$GRAPHRAG_ROOT"
    echo "✅ GraphRAG installed successfully from local source"
else
    echo "⚠️  Warning: GraphRAG project root not found, installing from PyPI..."
    pip install -q graphrag
fi

# 設定環境變數（可選）
export GRAPHRAG_SETTINGS_PATH="${GRAPHRAG_SETTINGS_PATH:-../../graphrag_local/settings.yaml}"
export GRAPHRAG_DATA_DIR="${GRAPHRAG_DATA_DIR:-../../graphrag_local/output}"

echo "✓ Configuration:"
echo "  - Settings: $GRAPHRAG_SETTINGS_PATH"
echo "  - Data Dir: $GRAPHRAG_DATA_DIR"

# 啟動服務
echo "✓ Starting FastAPI server on http://localhost:8000"
python main.py
