#!/bin/bash

# GraphRAG UI 後端服務啟動腳本
# Given 已完成後端部署設定且具備必要環境變數與依賴
# When 啟動後端服務並等待健康檢查
# Then 服務狀態為可用且健康檢查端點回應成功（HTTP 200/OK）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "GraphRAG UI Backend Service Startup"
echo "=========================================="

# 檢查 Python 虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 錯誤：找不到虛擬環境 (venv)"
    echo "請先執行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 啟動虛擬環境
echo "✓ 啟動 Python 虛擬環境..."
source venv/bin/activate

# 驗證依賴
echo "✓ 驗證必要依賴..."
python -c "import fastapi, uvicorn, pandas, pydantic, datashaper, graphrag" 2>/dev/null || {
    echo "❌ 錯誤：缺少必要依賴（包括 GraphRAG 與 datashaper）"
    echo "正在安裝依賴..."
    pip install -q --upgrade pip

    # 先安裝 requirements.txt 中的依賴
    pip install -q -r requirements.txt

    # 從專案根目錄安裝 GraphRAG（本地開發模式）
    echo "✓ 安裝 GraphRAG 本地版本..."
    GRAPHRAG_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    if [ -f "$GRAPHRAG_ROOT/pyproject.toml" ]; then
        pip install -q -e "$GRAPHRAG_ROOT"
        echo "✅ GraphRAG 本地版本安裝成功"
    else
        echo "⚠️  警告：找不到 GraphRAG 專案根目錄，嘗試從 PyPI 安裝..."
        pip install -q graphrag
    fi

    # 驗證安裝是否成功
    python -c "import fastapi, uvicorn, pandas, pydantic, datashaper, graphrag" 2>/dev/null || {
        echo "❌ 依賴安裝失敗"
        echo "請手動檢查以下問題："
        echo "  1. Python 版本是否為 3.10-3.12"
        echo "  2. 是否有網路連接"
        echo "  3. pip 是否能正常安裝套件"
        exit 1
    }
    echo "✅ 所有依賴安裝成功"
}

# 設定環境變數（若未設定）
export GRAPHRAG_SETTINGS_PATH="${GRAPHRAG_SETTINGS_PATH:-./settings.yaml}"
export GRAPHRAG_DATA_DIR="${GRAPHRAG_DATA_DIR:-./output}"

echo "✓ 環境變數設定："
echo "  - GRAPHRAG_SETTINGS_PATH: $GRAPHRAG_SETTINGS_PATH"
echo "  - GRAPHRAG_DATA_DIR: $GRAPHRAG_DATA_DIR"

# 檢查端口是否被佔用
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  警告：端口 $PORT 已被佔用"
    echo "正在停止舊進程..."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 啟動後端服務
echo "✓ 啟動 FastAPI 服務於 http://0.0.0.0:$PORT ..."
echo ""

# 使用 uvicorn 啟動，並將 PID 寫入文件以便後續管理
uvicorn main:app --host 0.0.0.0 --port $PORT --reload &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

echo "後端服務 PID: $BACKEND_PID"
echo ""
echo "等待服務啟動..."
sleep 3

# 健康檢查
echo "執行健康檢查..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
        echo "✅ 後端服務健康檢查通過！"
        echo ""
        echo "服務狀態："
        curl -s http://localhost:$PORT/ | python -m json.tool
        echo ""
        echo "=========================================="
        echo "後端服務已成功啟動並可用"
        echo "API 文件: http://localhost:$PORT/docs"
        echo "=========================================="
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "重試 $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

echo "❌ 健康檢查失敗：服務未能在預期時間內啟動"
kill $BACKEND_PID 2>/dev/null || true
exit 1
