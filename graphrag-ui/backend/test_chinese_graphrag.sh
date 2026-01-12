#!/bin/bash
# GraphRAG 中文處理測試驗證腳本

echo "=== GraphRAG 中文處理全面測試 ==="

# 1. 環境檢查
echo "1. 檢查環境狀態:"
echo "LMStudio 狀態:"
curl -s http://localhost:1234/v1/models | jq '.data[0].id' || echo "❌ LMStudio 未運行"

echo -e "\n2. 清理環境:"
pkill -f "graphrag.index"
rm -rf output/20260112-* cache/entity_extraction/*

# 3. 創建測試文件
echo -e "\n3. 創建中文測試文件:"
cat > input/chinese_test_final.txt << 'EOF'
微軟公司是一家美國科技企業。
比爾·蓋茨創立了微軟公司。
微軟總部位於華盛頓州雷德蒙德。
GraphRAG是微軟開發的知識圖譜工具。
EOF

echo "測試文件內容:"
cat input/chinese_test_final.txt

# 4. 使用優化配置
echo -e "\n4. 使用優化配置文件:"
cp settings_optimized.yaml settings.yaml
echo "✅ 配置已更新"

# 5. 啟動測試
echo -e "\n5. 啟動 GraphRAG 測試 (限時 5 分鐘):"
cd /Users/shengfanwu/GitHub/graphrag
timeout 300s python -m graphrag.index --root ./graphrag-ui/backend &
INDEXING_PID=$!

# 6. 監控進度
echo "監控進程 PID: $INDEXING_PID"
sleep 60

if ps -p $INDEXING_PID > /dev/null; then
    echo "✅ 索引進程運行正常 (60秒)"
    sleep 120
    
    if ps -p $INDEXING_PID > /dev/null; then
        echo "✅ 索引進程持續運行 (3分鐘)"
        kill $INDEXING_PID
        echo "測試完成，進程已終止"
    else
        echo "⚠️ 索引進程在 3 分鐘後結束"
    fi
else
    echo "❌ 索引進程在 60 秒內結束"
fi

# 7. 檢查結果
echo -e "\n7. 檢查測試結果:"
cd graphrag-ui/backend

echo "錯誤統計:"
find output/ -name "*.log" -exec grep -c "Error Invoking LLM" {} \; 2>/dev/null | head -1 || echo "0"

echo "成功調用統計:"
find output/ -name "*.log" -exec grep -c "HTTP/1.1 200 OK" {} \; 2>/dev/null | head -1 || echo "0"

echo "輸出文件:"
ls -la output/ 2>/dev/null | tail -5

echo -e "\n=== 測試完成 ==="
