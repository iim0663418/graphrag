#!/bin/bash

# GraphRAG UI 完整驗收測試套件
# 自動化執行所有驗收測試

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}GraphRAG UI 完整驗收測試套件${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 清理函數
cleanup() {
    echo ""
    echo -e "${YELLOW}清理中...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "已停止後端服務 (PID: $BACKEND_PID)"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "已停止前端服務 (PID: $FRONTEND_PID)"
    fi
}

# 設定退出時清理
trap cleanup EXIT INT TERM

# 測試計數器
TOTAL_TESTS=7
PASSED_TESTS=0
FAILED_TESTS=0

# ========================================
# 步驟 1: 後端服務啟動
# ========================================
echo -e "${BLUE}步驟 1/${TOTAL_TESTS}: 啟動後端服務...${NC}"
cd backend

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 錯誤：找不到虛擬環境${NC}"
    echo "請先執行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 啟動後端
source venv/bin/activate
export GRAPHRAG_SETTINGS_PATH="${GRAPHRAG_SETTINGS_PATH:-./settings.yaml}"
export GRAPHRAG_DATA_DIR="${GRAPHRAG_DATA_DIR:-./output}"

# 檢查並清理舊進程
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  停止佔用端口 8000 的舊進程...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/graphrag_backend.log 2>&1 &
BACKEND_PID=$!
echo "後端服務 PID: $BACKEND_PID"
echo "等待後端啟動..."
sleep 5

# 驗證後端啟動
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 後端服務啟動成功${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 後端服務啟動失敗${NC}"
    echo "查看日誌: cat /tmp/graphrag_backend.log"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 2: 後端健康檢查
# ========================================
echo -e "${BLUE}步驟 2/${TOTAL_TESTS}: 後端健康檢查...${NC}"
if python health_check.py; then
    echo -e "${GREEN}✅ 後端健康檢查通過${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 後端健康檢查失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 3: 前端服務啟動
# ========================================
echo -e "${BLUE}步驟 3/${TOTAL_TESTS}: 啟動前端服務...${NC}"
cd ../frontend

# 檢查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${RED}❌ 錯誤：找不到 node_modules${NC}"
    echo "請先執行: npm install"
    exit 1
fi

# 檢查並清理舊進程
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  停止佔用端口 5173 的舊進程...${NC}"
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

export VITE_API_BASE_URL="http://localhost:8000"
npm run dev > /tmp/graphrag_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服務 PID: $FRONTEND_PID"
echo "等待前端啟動..."
sleep 10

# 驗證前端啟動
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5173/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 前端服務啟動成功${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "重試 $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ 前端服務啟動失敗${NC}"
    echo "查看日誌: cat /tmp/graphrag_frontend.log"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 4: 前端應用驗證
# ========================================
echo -e "${BLUE}步驟 4/${TOTAL_TESTS}: 前端應用驗證...${NC}"
if python check_frontend.py; then
    echo -e "${GREEN}✅ 前端應用驗證通過${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 前端應用驗證失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 5: API 連接測試
# ========================================
echo -e "${BLUE}步驟 5/${TOTAL_TESTS}: API 連接測試...${NC}"
cd ../tests
if python test_api_connection.py; then
    echo -e "${GREEN}✅ API 連接測試通過${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ API 連接測試失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 6: 搜尋功能端到端測試
# ========================================
echo -e "${BLUE}步驟 6/${TOTAL_TESTS}: 搜尋功能端到端測試...${NC}"
if python test_search_e2e.py; then
    echo -e "${GREEN}✅ 搜尋功能測試通過${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 搜尋功能測試失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 步驟 7: 視覺化功能驗證
# ========================================
echo -e "${BLUE}步驟 7/${TOTAL_TESTS}: 視覺化功能驗證...${NC}"
if python test_visualization.py; then
    echo -e "${GREEN}✅ 視覺化功能驗證通過${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 視覺化功能驗證失敗${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    exit 1
fi
echo ""

# ========================================
# 測試總結
# ========================================
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}測試總結${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo "總測試數: ${TOTAL_TESTS}"
echo -e "通過: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "失敗: ${RED}${FAILED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}✅ 所有驗收測試通過！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${GREEN}GraphRAG UI 已達到生產就緒狀態${NC}"
    echo ""
    echo "服務資訊："
    echo "  後端服務: http://localhost:8000"
    echo "  前端應用: http://localhost:5173"
    echo "  API 文檔: http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止所有服務${NC}"
    echo ""

    # 保持服務運行以便手動測試
    echo "服務將保持運行，按 Ctrl+C 退出..."
    wait
else
    echo -e "${RED}==========================================${NC}"
    echo -e "${RED}❌ 驗收測試失敗${NC}"
    echo -e "${RED}==========================================${NC}"
    echo ""
    echo "請檢查上方錯誤詳情並修復問題"
    echo ""
    exit 1
fi
