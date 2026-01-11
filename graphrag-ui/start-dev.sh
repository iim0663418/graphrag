#!/bin/bash

# GraphRAG UI 開發啟動腳本

echo "🚀 啟動 GraphRAG UI 開發環境"

# 啟動後端 API
echo "📡 啟動後端 API 服務..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# 等待後端啟動
sleep 3

# 啟動前端開發服務器
echo "🎨 啟動前端開發服務器..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ 開發環境已啟動"
echo "📡 後端 API: http://localhost:8000"
echo "🎨 前端應用: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 等待中斷信號
trap "echo '🛑 停止服務...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
