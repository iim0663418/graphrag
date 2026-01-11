# GraphRAG UI Backend

GraphRAG 查詢服務的 FastAPI 後端。

## 修復說明

### 問題診斷

原始程式碼無法正確導入 GraphRAG 模組，因為：
- `graphrag` 模組位於專案根目錄 (`/Users/shengfanwu/GitHub/graphrag/graphrag/`)
- Backend 位於 `graphrag-ui/backend/`
- Python 預設無法找到上層目錄的模組

### 解決方案

在 `main.py` 和 `graphrag_service.py` 檔案開頭添加了以下程式碼：

```python
import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

這段程式碼會：
1. 計算專案根目錄的絕對路徑 (`graphrag/`)
2. 將該路徑添加到 `sys.path` 的開頭
3. 使 Python 能夠找到 `graphrag` 模組

### 修改的檔案

1. **main.py** (行 1-6)
   - 添加 `sys.path` 設定
   - 確保 FastAPI 啟動時能載入 GraphRAG 模組

2. **services/graphrag_service.py** (行 1-8)
   - 添加 `sys.path` 設定
   - 確保服務初始化時能導入 GraphRAG 配置和查詢 API

3. **requirements.txt**
   - 添加 `pyyaml==6.0.2` (用於讀取 settings.yaml)
   - 添加 `pyarrow==18.1.0` (用於讀取 Parquet 檔案)

## 安裝與啟動

### 方法 1：使用啟動腳本（推薦）

```bash
./run.sh
```

### 方法 2：手動啟動

```bash
# 1. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數（可選）
export GRAPHRAG_SETTINGS_PATH="../../graphrag_local/settings.yaml"
export GRAPHRAG_DATA_DIR="../../graphrag_local/output"

# 4. 啟動服務
python main.py
```

## 測試 Import

使用測試腳本驗證 GraphRAG 模組導入：

```bash
python test_import.py
```

成功輸出範例：
```
✓ Project root added to sys.path: /Users/shengfanwu/GitHub/graphrag
✓ Current sys.path: [...]
✓ Successfully imported: graphrag.config.create_graphrag_config
✓ Successfully imported: graphrag.config.models.graph_rag_config
✓ Successfully imported: graphrag.query.api (global_search, local_search)

✓ All GraphRAG imports successful!
```

## API 端點

- `GET /` - 服務狀態
- `POST /api/search/global` - 全域搜尋
- `POST /api/search/local` - 本地搜尋
- `POST /api/files/upload` - 檔案上傳
- `GET /api/files` - 檔案列表
- `DELETE /api/files/{file_id}` - 刪除檔案
- `POST /api/indexing/start` - 開始索引
- `GET /api/indexing/status` - 索引狀態

## 環境變數

- `GRAPHRAG_SETTINGS_PATH`: GraphRAG 配置檔路徑（預設：`./settings.yaml`）
- `GRAPHRAG_DATA_DIR`: Parquet 資料目錄路徑（預設：`./output`）

## 技術細節

### sys.path 計算邏輯

```
當前檔案: graphrag-ui/backend/main.py
__file__.parent           → graphrag-ui/backend/
__file__.parent.parent    → graphrag-ui/
project_root              → graphrag/ (專案根目錄)
```

### GraphRAG 模組結構

```
graphrag/
├── graphrag/
│   ├── config/
│   │   ├── create_graphrag_config.py
│   │   └── models/
│   │       └── graph_rag_config.py
│   └── query/
│       └── api.py
└── graphrag-ui/
    └── backend/
        ├── main.py
        └── services/
            └── graphrag_service.py
```

## 故障排除

### Import 錯誤

如果仍然遇到 `ModuleNotFoundError: No module named 'graphrag'`：

1. 檢查專案根目錄是否包含 `graphrag/` 資料夾
2. 確認 `sys.path` 設定正確（使用 `test_import.py`）
3. 確認虛擬環境已啟動
4. 重新安裝依賴：`pip install -r requirements.txt`

### YAML 錯誤

如果遇到 `ModuleNotFoundError: No module named 'yaml'`：

```bash
pip install pyyaml
```

### Parquet 錯誤

如果遇到 Parquet 讀取錯誤：

```bash
pip install pyarrow pandas
```
