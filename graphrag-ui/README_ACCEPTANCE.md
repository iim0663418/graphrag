# GraphRAG UI 驗收測試指南

## 快速開始

### 前置條件

1. **後端環境**
   - Python 3.11+
   - 已創建虛擬環境並安裝依賴
   ```bash
   cd graphrag-ui/backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **前端環境**
   - Node.js 18+
   - npm 或 yarn
   - 已安裝依賴
   ```bash
   cd graphrag-ui/frontend
   npm install
   ```

3. **測試環境**
   - Python 3.11+（用於執行測試腳本）
   - `requests` 庫
   ```bash
   pip install requests
   ```

### 一鍵運行所有驗收測試

```bash
cd graphrag-ui
chmod +x run_all_tests.sh
./run_all_tests.sh
```

這將自動：
1. 啟動後端服務
2. 執行後端健康檢查
3. 啟動前端服務
4. 執行前端驗證
5. 執行 API 連接測試
6. 執行搜尋功能 E2E 測試
7. 執行視覺化功能驗證

### 分步執行測試

#### 1. 後端測試

```bash
# 終端 1: 啟動後端
cd graphrag-ui/backend
./start_backend.sh

# 終端 2: 執行健康檢查
cd graphrag-ui/backend
python health_check.py
```

#### 2. 前端測試

```bash
# 終端 1: 啟動前端
cd graphrag-ui/frontend
./start_frontend.sh

# 終端 2: 執行驗證
cd graphrag-ui/frontend
python check_frontend.py
```

#### 3. 整合測試

```bash
# 確保前後端都在運行
cd graphrag-ui/tests

# API 連接測試
python test_api_connection.py

# 搜尋功能測試
python test_search_e2e.py

# 視覺化驗證
python test_visualization.py
```

## 測試套件說明

### 測試文件結構

```
graphrag-ui/
├── backend/
│   ├── start_backend.sh          # 後端啟動腳本
│   └── health_check.py           # 後端健康檢查
├── frontend/
│   ├── start_frontend.sh         # 前端啟動腳本
│   └── check_frontend.py         # 前端驗證
├── tests/
│   ├── test_api_connection.py    # API 連接測試
│   ├── test_search_e2e.py        # 搜尋 E2E 測試
│   └── test_visualization.py     # 視覺化驗證
├── run_all_tests.sh              # 主測試腳本
├── ACCEPTANCE_CHECKLIST.md       # 驗收清單
└── README_ACCEPTANCE.md          # 本文件
```

### 各測試腳本功能

| 腳本 | 功能 | 驗收規格 |
|------|------|----------|
| `start_backend.sh` | 啟動後端服務並執行健康檢查 | Given-When-Then: 服務啟動驗證 |
| `health_check.py` | 驗證所有核心 API 端點 | Given-When-Then: API 端點驗證 |
| `start_frontend.sh` | 啟動前端服務 | Given-When-Then: 前端啟動驗證 |
| `check_frontend.py` | 驗證前端可用性 | Given-When-Then: 前端載入驗證 |
| `test_api_connection.py` | 測試前後端連接 | Given-When-Then: API 連接測試 |
| `test_search_e2e.py` | 端到端搜尋功能測試 | Given-When-Then: 搜尋功能驗證 |
| `test_visualization.py` | 視覺化數據格式驗證 | Given-When-Then: 視覺化驗證 |

## 驗收標準

### 必須通過 (Blocking)

- ✅ 後端服務成功啟動並通過健康檢查
- ✅ 前端應用成功載入且無崩潰
- ✅ 前後端 API 連接正常
- ✅ 搜尋功能正確處理有效查詢
- ✅ 搜尋功能正確處理錯誤查詢
- ✅ 視覺化數據格式正確

### 建議通過 (Non-blocking)

- [ ] 完整 UI 互動測試（使用 Playwright/Cypress）
- [ ] 性能測試（回應時間 < 3s）
- [ ] 負載測試（並發查詢處理）

## 預期輸出

### 成功案例

```
==========================================
GraphRAG UI 完整驗收測試套件
==========================================

步驟 1/7: 啟動後端服務...
✅ 後端服務啟動成功

步驟 2/7: 後端健康檢查...
✅ 後端健康檢查通過

步驟 3/7: 啟動前端服務...
✅ 前端服務啟動成功

步驟 4/7: 前端應用驗證...
✅ 前端應用驗證通過

步驟 5/7: API 連接測試...
✅ API 連接測試通過

步驟 6/7: 搜尋功能端到端測試...
✅ 搜尋功能測試通過

步驟 7/7: 視覺化功能驗證...
✅ 視覺化功能驗證通過

==========================================
測試總結
==========================================

總測試數: 7
通過: 7
失敗: 0

==========================================
✅ 所有驗收測試通過！
==========================================

GraphRAG UI 已達到生產就緒狀態

服務資訊：
  後端服務: http://localhost:8000
  前端應用: http://localhost:5173
  API 文檔: http://localhost:8000/docs

按 Ctrl+C 停止所有服務
```

## 故障排除

### 後端啟動失敗

**問題**：端口 8000 被佔用
```bash
lsof -ti :8000 | xargs kill -9
```

**問題**：虛擬環境未找到
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**問題**：依賴安裝失敗
```bash
# 升級 pip
pip install --upgrade pip
# 重新安裝
pip install -r requirements.txt
```

### 前端啟動失敗

**問題**：端口 5173 被佔用
```bash
lsof -ti :5173 | xargs kill -9
```

**問題**：node_modules 損壞
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**問題**：Node.js 版本過舊
```bash
# 使用 nvm 切換版本
nvm use 18
# 或升級 Node.js
```

### API 連接失敗

**問題**：CORS 錯誤
- 檢查 `backend/main.py` 中的 CORS 設定
- 確保允許前端 origin: `http://localhost:5173`

**問題**：網絡請求超時
- 檢查後端日誌: `cat /tmp/graphrag_backend.log`
- 增加超時時間（在測試腳本中）

### 搜尋測試失敗

**問題**：GraphRAG 服務未初始化
- 確保設定了環境變數：
  ```bash
  export GRAPHRAG_SETTINGS_PATH="./settings.yaml"
  export GRAPHRAG_DATA_DIR="./output"
  ```
- 檢查後端日誌中的初始化錯誤

**問題**：搜尋返回 500 錯誤
- 查看後端日誌獲取詳細錯誤信息
- 確認 GraphRAG 數據目錄存在且包含必要文件

## 進階測試

### UI 互動測試（Playwright）

```bash
# 安裝 Playwright
cd frontend
npm install -D @playwright/test
npx playwright install

# 創建測試文件
mkdir -p tests/e2e
```

創建 `tests/e2e/search.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('搜尋功能測試', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // 輸入查詢
  await page.fill('input[placeholder*="搜尋"]', 'GraphRAG');
  await page.click('button[type="submit"]');

  // 等待結果
  await page.waitForSelector('.search-results');

  // 驗證結果顯示
  const results = await page.locator('.result-item').count();
  expect(results).toBeGreaterThan(0);
});
```

執行：
```bash
npx playwright test
```

### 性能測試

使用 `locust` 或 `artillery` 進行負載測試：

```bash
# 安裝 artillery
npm install -g artillery

# 創建測試配置
cat > load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "搜尋測試"
    flow:
      - post:
          url: "/api/search/global"
          json:
            query: "test query"
            type: "global"
EOF

# 執行負載測試
artillery run load-test.yml
```

## 持續集成 (CI)

### GitHub Actions 範例

創建 `.github/workflows/acceptance.yml`:

```yaml
name: Acceptance Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd graphrag-ui/backend
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

        cd ../frontend
        npm install

    - name: Run acceptance tests
      run: |
        cd graphrag-ui
        chmod +x run_all_tests.sh
        ./run_all_tests.sh
```

## 相關文件

- [驗收清單](./ACCEPTANCE_CHECKLIST.md) - 完整驗收標準與流程
- [規格文件](../.specify/specs/current_spec.md) - Given-When-Then 行為描述
- [項目說明](./README.md) - GraphRAG UI 總體說明

## 聯繫方式

如有問題或建議，請：
1. 查看本文件的故障排除章節
2. 查看 [ACCEPTANCE_CHECKLIST.md](./ACCEPTANCE_CHECKLIST.md) 獲取詳細說明
3. 提交 Issue 到項目倉庫

---

**文件版本**：1.0.0
**最後更新**：2026-01-11
