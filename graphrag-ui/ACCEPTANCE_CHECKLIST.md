# GraphRAG UI 驗收測試清單

基於 `.specify/specs/current_spec.md` 的 Given-When-Then 規格書

## 驗收總覽

本文件提供完整的驗收測試清單，用於驗證 GraphRAG UI 的生產就緒狀態。

### 測試套件組成

| 測試類別 | 腳本文件 | 描述 |
|---------|---------|------|
| 後端服務啟動 | `backend/start_backend.sh` | 後端服務啟動與健康檢查 |
| 後端健康檢查 | `backend/health_check.py` | 驗證核心 API 端點 |
| 前端應用啟動 | `frontend/start_frontend.sh` | 前端應用啟動腳本 |
| 前端應用驗證 | `frontend/check_frontend.py` | 驗證前端可用性 |
| API 連接測試 | `tests/test_api_connection.py` | 前後端連接測試 |
| 搜尋功能 E2E | `tests/test_search_e2e.py` | 搜尋功能端到端測試 |
| 視覺化驗證 | `tests/test_visualization.py` | 圖譜視覺化驗證 |

---

## 1. 後端服務啟動驗證

### 驗收規格 (Given-When-Then)

#### 1.1 服務啟動與健康檢查
- **Given** 已完成後端部署設定且具備必要環境變數與依賴
- **When** 啟動後端服務並等待健康檢查
- **Then** 服務狀態為可用且健康檢查端點回應成功（HTTP 200/OK）

#### 1.2 核心 API 端點驗證
- **Given** 後端服務已啟動
- **When** 呼叫核心 API 端點（如 `/health` 或 `/api/status`）
- **Then** 回應內容包含版本/狀態資訊且格式正確

### 執行步驟

```bash
# 1. 啟動後端服務
cd graphrag-ui/backend
./start_backend.sh

# 2. 執行健康檢查
python health_check.py
```

### 驗收標準

- ✅ 後端服務成功啟動於 `http://localhost:8000`
- ✅ 根端點 `/` 返回 HTTP 200 並包含正確的 JSON 格式
- ✅ API 文檔端點 `/docs` 可訪問
- ✅ 索引狀態端點 `/api/indexing/status` 返回正確格式
- ✅ 所有健康檢查測試通過

### 預期輸出

```
✅ 後端服務健康檢查通過：所有端點回應正常
```

---

## 2. 前端應用啟動驗證

### 驗收規格 (Given-When-Then)

#### 2.1 首屏載入
- **Given** 前端建置完成且設定正確的 API Base URL
- **When** 啟動前端應用並於瀏覽器載入首頁
- **Then** 首屏載入完成且無重大錯誤訊息（UI 可操作）

#### 2.2 主要功能頁面
- **Given** 前端已載入
- **When** 進入主要功能頁（如搜尋/工作區）
- **Then** 主要 UI 元件可見且互動無阻礙

### 執行步驟

```bash
# 1. 啟動前端服務
cd graphrag-ui/frontend
./start_frontend.sh

# 2. 在新終端執行前端驗證
python check_frontend.py
```

### 驗收標準

- ✅ 前端服務成功啟動於 `http://localhost:5173`
- ✅ 首頁載入返回 HTTP 200
- ✅ HTML 包含 React root 元素 (`<div id="root">`)
- ✅ Vite 客戶端腳本可用（開發模式）
- ✅ 應用穩定運行無崩潰

### 預期輸出

```
✅ 前端驗證通過：應用已成功載入且可操作
   請訪問 http://localhost:5173 進行手動測試
```

---

## 3. API 連接測試

### 驗收規格 (Given-When-Then)

#### 3.1 成功取得回應
- **Given** 前端已啟動且後端 API 可用
- **When** 前端發出任一讀取型請求（如索引狀態或預設資料）
- **Then** 前端成功取得回應且 UI 正確呈現資料

#### 3.2 錯誤處理
- **Given** 前端發出 API 請求
- **When** API 回傳錯誤或逾時
- **Then** UI 顯示可理解的錯誤提示並不崩潰

### 執行步驟

```bash
# 確保前後端都已啟動，然後執行
cd graphrag-ui/tests
python test_api_connection.py
```

### 驗收標準

- ✅ 基本連接性測試通過
- ✅ 索引狀態查詢返回正確格式
- ✅ 文件列表查詢成功
- ✅ 空查詢正確返回 400 錯誤
- ✅ 無效端點正確返回 404 錯誤
- ✅ 所有錯誤回應包含清晰的錯誤訊息

### 預期輸出

```
✅ 所有 API 連接測試通過
   前端可正常與後端通信
```

---

## 4. 搜尋功能端到端測試

### 驗收規格 (Given-When-Then)

#### 4.1 有效查詢
- **Given** 使用者已進入搜尋頁且後端索引可用
- **When** 輸入有效查詢並提交
- **Then** 顯示搜尋結果列表且包含相關性排序或摘要

#### 4.2 連續搜尋
- **Given** 已執行一次搜尋
- **When** 變更查詢條件或重新提交
- **Then** 結果更新且不出現舊資料殘留或 UI 異常

#### 4.3 無結果查詢
- **Given** 提交無結果的查詢
- **When** 搜尋完成
- **Then** 顯示「無結果」狀態與下一步建議

### 執行步驟

```bash
# 確保後端已啟動，然後執行
cd graphrag-ui/tests
python test_search_e2e.py
```

### 驗收標準

- ✅ 全域搜尋（Global Search）正確處理有效查詢
- ✅ 本地搜尋（Local Search）正確處理有效查詢
- ✅ 連續搜尋結果正確更新
- ✅ 空查詢正確拒絕（HTTP 400）
- ✅ 純空白查詢正確拒絕（HTTP 400）
- ✅ 所有搜尋回應包含 `response` 欄位

### 預期輸出

```
✅ 搜尋功能端到端測試通過
   - 有效查詢正確處理
   - 連續搜尋結果正確更新
   - 錯誤查詢適當處理
```

---

## 5. 視覺化功能驗證

### 驗收規格 (Given-When-Then)

#### 5.1 圖譜渲染
- **Given** 搜尋結果包含圖譜/關聯資料
- **When** 展開視覺化區塊或圖譜視圖
- **Then** 圖譜渲染成功且節點/邊資訊正確

#### 5.2 圖譜互動
- **Given** 使用者操作圖譜（縮放、拖曳、點擊）
- **When** 互動發生
- **Then** 圖譜互動正常且資訊提示正確

### 執行步驟

```bash
# 執行視覺化數據格式驗證
cd graphrag-ui/tests
python test_visualization.py
```

### 驗收標準

- ✅ 圖譜數據結構正確（nodes + edges）
- ✅ 節點包含必要欄位：id, name, type, relationCount
- ✅ 邊包含必要欄位：source, target
- ✅ 圖譜數據一致性（所有邊的 source/target 存在於節點中）
- ✅ 前端組件需求已驗證：
  - D3.js 圖譜渲染
  - 節點點擊互動
  - 節點拖曳互動
  - 圖譜縮放功能
  - 節點 Tooltip
  - 錯誤處理與 Fallback UI

### 預期輸出

```
✅ 視覺化功能驗證測試通過
   - 圖譜數據結構正確
   - 節點和邊數據驗證通過
   - 圖譜一致性驗證通過
   - 前端組件需求已驗證
```

### 完整 UI 互動測試

**注意**：上述測試驗證數據格式和組件需求。完整的 UI 互動測試（縮放、拖曳、點擊）需要使用以下工具：

#### 推薦工具：Playwright

```bash
# 安裝 Playwright
npm install -D @playwright/test
npx playwright install

# 創建測試文件 tests/e2e/visualization.spec.ts
# 執行測試
npx playwright test
```

#### 或使用：Cypress

```bash
# 安裝 Cypress
npm install -D cypress
npx cypress open
```

---

## 完整驗收流程

### 快速驗收（所有測試）

創建主測試腳本 `run_all_tests.sh`：

```bash
#!/bin/bash

echo "=========================================="
echo "GraphRAG UI 完整驗收測試套件"
echo "=========================================="
echo ""

# 1. 啟動後端
echo "步驟 1/6: 啟動後端服務..."
cd backend
./start_backend.sh &
BACKEND_PID=$!
sleep 5

# 2. 後端健康檢查
echo ""
echo "步驟 2/6: 後端健康檢查..."
python health_check.py
if [ $? -ne 0 ]; then
    echo "❌ 後端健康檢查失敗"
    kill $BACKEND_PID
    exit 1
fi

# 3. 啟動前端
echo ""
echo "步驟 3/6: 啟動前端服務..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
sleep 8

# 4. 前端驗證
echo ""
echo "步驟 4/6: 前端應用驗證..."
python check_frontend.py
if [ $? -ne 0 ]; then
    echo "❌ 前端驗證失敗"
    kill $BACKEND_PID $FRONTEND_PID
    exit 1
fi

# 5. API 連接測試
echo ""
echo "步驟 5/6: API 連接測試..."
cd ../tests
python test_api_connection.py
if [ $? -ne 0 ]; then
    echo "❌ API 連接測試失敗"
    kill $BACKEND_PID $FRONTEND_PID
    exit 1
fi

# 6. 搜尋功能測試
echo ""
echo "步驟 6/6: 搜尋功能端到端測試..."
python test_search_e2e.py
if [ $? -ne 0 ]; then
    echo "❌ 搜尋功能測試失敗"
    kill $BACKEND_PID $FRONTEND_PID
    exit 1
fi

# 7. 視覺化驗證
echo ""
echo "步驟 7/6: 視覺化功能驗證..."
python test_visualization.py
if [ $? -ne 0 ]; then
    echo "❌ 視覺化驗證失敗"
    kill $BACKEND_PID $FRONTEND_PID
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有驗收測試通過！"
echo "=========================================="
echo ""
echo "GraphRAG UI 已達到生產就緒狀態"
echo ""
echo "後端服務: http://localhost:8000"
echo "前端應用: http://localhost:5173"
echo "API 文檔: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服務"
echo ""

# 保持服務運行
wait
```

### 執行完整驗收

```bash
chmod +x graphrag-ui/run_all_tests.sh
cd graphrag-ui
./run_all_tests.sh
```

---

## 驗收標準總結

### 必須通過的測試（Blocking）

- [x] 後端服務健康檢查（所有端點返回 200）
- [x] 前端應用載入（無崩潰，UI 可操作）
- [x] API 連接測試（前後端通信正常）
- [x] 搜尋功能（有效查詢、錯誤處理）
- [x] 視覺化數據格式（節點/邊結構正確）

### 建議通過的測試（Non-blocking）

- [ ] 完整 UI 互動測試（Playwright/Cypress）
- [ ] 性能測試（回應時間 < 3s）
- [ ] 負載測試（並發查詢處理）
- [ ] 跨瀏覽器兼容性測試

---

## 驗收狀態報告範本

### 測試執行日期：[填寫日期]

| 測試類別 | 狀態 | 備註 |
|---------|------|------|
| 後端服務啟動 | ✅ / ❌ |  |
| 後端健康檢查 | ✅ / ❌ |  |
| 前端應用啟動 | ✅ / ❌ |  |
| 前端應用驗證 | ✅ / ❌ |  |
| API 連接測試 | ✅ / ❌ |  |
| 搜尋功能 E2E | ✅ / ❌ |  |
| 視覺化驗證 | ✅ / ❌ |  |

### 總體評估

- **生產就緒狀態**：是 / 否
- **阻礙問題**：[列出]
- **建議改進**：[列出]

---

## 故障排除

### 後端服務啟動失敗

```bash
# 檢查端口佔用
lsof -i :8000

# 檢查 Python 環境
cd backend
source venv/bin/activate
pip list

# 查看詳細錯誤
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端應用啟動失敗

```bash
# 檢查端口佔用
lsof -i :5173

# 重新安裝依賴
cd frontend
rm -rf node_modules package-lock.json
npm install

# 查看詳細錯誤
npm run dev
```

### API 連接失敗

```bash
# 確認後端運行
curl http://localhost:8000/

# 確認 CORS 設定
# 檢查 backend/main.py 的 CORS middleware

# 檢查網絡請求
# 在瀏覽器開發者工具 > Network 查看請求
```

---

## 附錄：規格文件參考

本驗收清單嚴格遵循以下規格文件：
- `.specify/specs/current_spec.md` - Given-When-Then 行為描述
- `graphrag-ui/VERIFICATION_REPORT.md` - 驗證報告
- `graphrag-ui/README.md` - 項目說明

---

**文件版本**：1.0.0
**創建日期**：2026-01-11
**維護者**：GraphRAG UI Team
