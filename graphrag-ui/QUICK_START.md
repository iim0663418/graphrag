# GraphRAG UI 驗收測試 - 快速開始

## 🚀 一鍵驗收

```bash
cd graphrag-ui
chmod +x run_all_tests.sh
chmod +x backend/start_backend.sh
chmod +x frontend/start_frontend.sh
./run_all_tests.sh
```

## 📋 前置條件檢查

### 後端
```bash
cd backend
python --version  # 需要 Python 3.11+
[ -d "venv" ] && echo "✅ venv exists" || echo "❌ 需要創建 venv"
source venv/bin/activate
pip list | grep fastapi  # 驗證依賴
```

### 前端
```bash
cd frontend
node --version  # 需要 Node.js 18+
npm --version
[ -d "node_modules" ] && echo "✅ node_modules exists" || echo "❌ 需要 npm install"
```

## 🧪 分步測試

### 1️⃣ 後端測試
```bash
# 終端 1
cd backend
./start_backend.sh

# 終端 2
cd backend
python health_check.py
```

### 2️⃣ 前端測試
```bash
# 終端 1
cd frontend
./start_frontend.sh

# 終端 2
cd frontend
python check_frontend.py
```

### 3️⃣ 整合測試
```bash
cd tests
python test_api_connection.py
python test_search_e2e.py
python test_visualization.py
```

## 📊 預期結果

### 成功輸出
```
✅ 所有驗收測試通過！
GraphRAG UI 已達到生產就緒狀態

後端服務: http://localhost:8000
前端應用: http://localhost:5173
API 文檔: http://localhost:8000/docs
```

### 失敗排查
```bash
# 查看後端日誌
cat /tmp/graphrag_backend.log

# 查看前端日誌
cat /tmp/graphrag_frontend.log

# 檢查端口
lsof -i :8000
lsof -i :5173
```

## 📚 完整文檔

- [驗收清單](./ACCEPTANCE_CHECKLIST.md) - 完整驗收標準
- [測試指南](./README_ACCEPTANCE.md) - 詳細執行指南
- [實作總結](./ACCEPTANCE_SUMMARY.md) - 實作說明

## 🆘 常見問題

**Q: 端口被佔用？**
```bash
lsof -ti :8000 | xargs kill -9
lsof -ti :5173 | xargs kill -9
```

**Q: venv 不存在？**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Q: node_modules 不存在？**
```bash
cd frontend
npm install
```

**Q: 測試失敗？**
- 確保前後端都在運行
- 檢查日誌文件
- 查看 [README_ACCEPTANCE.md](./README_ACCEPTANCE.md) 故障排除章節

## ✅ 驗收標準

- [ ] 後端服務成功啟動
- [ ] 後端健康檢查通過
- [ ] 前端應用成功載入
- [ ] 前端驗證通過
- [ ] API 連接測試通過
- [ ] 搜尋功能測試通過
- [ ] 視覺化功能驗證通過

---

**提示**: 執行 `./run_all_tests.sh` 可自動完成所有測試
