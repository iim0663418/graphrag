# GraphRAG UI Backend - 設置說明

## 問題診斷

如果您遇到 `ModuleNotFoundError: No module named 'datashaper'` 錯誤，這是因為後端服務需要 GraphRAG 及其所有依賴。

## 解決方案

我們已經修復了以下內容：

### 1. 更新 `requirements.txt`
已添加所有必要的 GraphRAG 依賴，包括：
- `datashaper` - GraphRAG 核心數據處理庫
- 所有 LLM 相關依賴（openai, tiktoken, nltk）
- 數據科學依賴（numpy, scipy, networkx 等）
- Azure 和向量數據庫支持

### 2. 更新啟動腳本
- `start_backend.sh` - 自動檢測並安裝缺失的依賴
- `run.sh` - 同樣支持自動安裝
- 兩個腳本都會從專案根目錄安裝 GraphRAG 本地版本（開發模式）

### 3. 新增安裝腳本
創建了 `install_dependencies.sh` 用於獨立安裝所有依賴。

## 使用方法

### 方法 1：使用安裝腳本（推薦）

```bash
cd graphrag-ui/backend
chmod +x install_dependencies.sh
./install_dependencies.sh
```

此腳本會：
1. 檢查 Python 版本（需要 3.10-3.12）
2. 創建或使用現有虛擬環境
3. 升級 pip
4. 安裝所有依賴
5. 從專案根目錄安裝 GraphRAG（可編輯模式）
6. 驗證所有依賴是否正確安裝

### 方法 2：使用 start_backend.sh

```bash
cd graphrag-ui/backend
chmod +x start_backend.sh
./start_backend.sh
```

此腳本會：
1. 檢查虛擬環境是否存在
2. 自動檢測並安裝缺失的依賴
3. 啟動 FastAPI 服務
4. 執行健康檢查

### 方法 3：使用 run.sh

```bash
cd graphrag-ui/backend
chmod +x run.sh
./run.sh
```

此腳本會每次重新安裝依賴（適合開發環境）。

### 方法 4：手動安裝

```bash
cd graphrag-ui/backend

# 創建虛擬環境
python -m venv venv
source venv/bin/activate

# 升級 pip
pip install --upgrade pip

# 安裝依賴
pip install -r requirements.txt

# 安裝 GraphRAG 本地版本
cd ../..
pip install -e .

# 返回 backend 目錄
cd graphrag-ui/backend

# 啟動服務
python main.py
```

## 驗證安裝

安裝完成後，您可以驗證依賴：

```bash
source venv/bin/activate
python -c "import datashaper, graphrag; print('✅ 所有依賴正常')"
```

## 環境要求

- **Python 版本**：3.10、3.11 或 3.12
- **作業系統**：macOS、Linux 或 Windows
- **依賴**：見 `requirements.txt`

## 環境變數

啟動腳本會自動設置以下環境變數（如果未設置）：

```bash
GRAPHRAG_SETTINGS_PATH=./settings.yaml
GRAPHRAG_DATA_DIR=./output
```

您可以在啟動前自行設置這些變數以使用不同的配置。

## 服務端點

後端服務啟動後，可以訪問：

- **主頁**：http://localhost:8000/
- **API 文檔**：http://localhost:8000/docs
- **OpenAPI 規範**：http://localhost:8000/openapi.json

## 故障排除

### 問題：Python 版本不符
**錯誤**：需要 Python 3.10-3.12
**解決**：使用 pyenv 或 conda 安裝正確的 Python 版本

### 問題：依賴安裝失敗
**錯誤**：某些套件無法安裝
**解決**：
1. 確保有網路連接
2. 升級 pip：`pip install --upgrade pip`
3. 檢查是否有編譯工具（特別是 numba、scipy）

### 問題：找不到 GraphRAG 模組
**錯誤**：`ModuleNotFoundError: No module named 'graphrag'`
**解決**：
1. 確保從專案根目錄安裝：`pip install -e /path/to/graphrag`
2. 或直接執行 `install_dependencies.sh`

### 問題：端口被佔用
**錯誤**：端口 8000 已被使用
**解決**：
1. `start_backend.sh` 會自動停止舊進程
2. 手動停止：`lsof -ti :8000 | xargs kill -9`
3. 使用不同端口：修改 `start_backend.sh` 中的 `PORT` 變數

## 開發模式

在開發模式下，GraphRAG 以可編輯模式（`-e`）安裝，這意味著：
- 對 GraphRAG 原始碼的修改會立即生效
- 不需要重新安裝套件
- 適合同時開發 GraphRAG 核心和 UI

## 生產部署

對於生產環境，建議：
1. 使用固定版本的依賴
2. 考慮使用 Docker 容器
3. 設置適當的環境變數
4. 使用 gunicorn 或其他 WSGI 服務器（而非 uvicorn --reload）

## 額外資源

- GraphRAG 文檔：參見專案根目錄的 README
- FastAPI 文檔：https://fastapi.tiangolo.com/
- Uvicorn 文檔：https://www.uvicorn.org/
