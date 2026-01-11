# GraphRAG 模組 Import 錯誤修復報告

## 問題描述

GraphRAG UI Backend 無法正確導入 GraphRAG 模組，導致服務初始化失敗。

### 錯誤訊息
```
ModuleNotFoundError: No module named 'graphrag'
```

### 根本原因

1. **路徑問題**：
   - GraphRAG 核心模組位於：`/Users/shengfanwu/GitHub/graphrag/graphrag/`
   - Backend 程式碼位於：`/Users/shengfanwu/GitHub/graphrag/graphrag-ui/backend/`
   - Python 預設只搜尋當前目錄和已安裝的套件

2. **缺少依賴**：
   - `pyyaml`：讀取 `settings.yaml` 配置檔
   - `pyarrow`：讀取 Parquet 資料檔案

## 解決方案

### 1. 修改 `main.py`

**位置**：`graphrag-ui/backend/main.py:1-6`

**新增程式碼**：
```python
import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

**作用**：
- 在 FastAPI 應用啟動前設定 `sys.path`
- 確保可以從專案根目錄導入 `graphrag` 模組

### 2. 修改 `graphrag_service.py`

**位置**：`graphrag-ui/backend/services/graphrag_service.py:1-8`

**新增程式碼**：
```python
import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

**作用**：
- 在服務類別導入前設定 `sys.path`
- 確保可以導入 GraphRAG 配置和查詢 API

### 3. 更新 `requirements.txt`

**位置**：`graphrag-ui/backend/requirements.txt`

**新增依賴**：
```
pyyaml==6.0.2
pyarrow==18.1.0
```

**作用**：
- `pyyaml`：解析 YAML 格式的配置檔
- `pyarrow`：讀取 GraphRAG 索引產生的 Parquet 檔案

## 技術細節

### sys.path 路徑計算

**main.py**:
```
檔案路徑: graphrag-ui/backend/main.py
__file__.parent           → graphrag-ui/backend/
__file__.parent.parent    → graphrag-ui/
project_root (往上3層)    → graphrag/
```

**graphrag_service.py**:
```
檔案路徑: graphrag-ui/backend/services/graphrag_service.py
__file__.parent                  → services/
__file__.parent.parent           → backend/
__file__.parent.parent.parent    → graphrag-ui/
project_root (往上4層)           → graphrag/
```

### 導入流程

修復後的導入流程：

1. **應用啟動**：
   ```
   main.py 執行
   → 設定 sys.path (添加專案根目錄)
   → 導入 services.graphrag_service
   → 成功導入 graphrag 模組
   ```

2. **服務初始化**：
   ```
   GraphRagService.__init__()
   → 設定 sys.path (防禦性編程)
   → 導入 graphrag.config.create_graphrag_config
   → 導入 graphrag.config.models.graph_rag_config
   → 導入 graphrag.query.api
   → 載入配置檔
   → 初始化 Parquet 適配器
   ```

## 驗證方法

### 1. 使用測試腳本

```bash
cd graphrag-ui/backend
python test_import.py
```

**預期輸出**：
```
✓ Project root added to sys.path: /Users/shengfanwu/GitHub/graphrag
✓ Current sys.path: ['/Users/shengfanwu/GitHub/graphrag', ...]
✓ Successfully imported: graphrag.config.create_graphrag_config
✓ Successfully imported: graphrag.config.models.graph_rag_config
✓ Successfully imported: graphrag.query.api (global_search, local_search)

✓ All GraphRAG imports successful!
✓ GraphRAG module location: /Users/shengfanwu/GitHub/graphrag/graphrag
```

### 2. 啟動服務測試

```bash
cd graphrag-ui/backend
./run.sh
```

**預期日誌**：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     GraphRAG service initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 檔案清單

### 修改的檔案

1. ✅ `graphrag-ui/backend/main.py`
   - 添加 sys.path 設定 (行 1-6)

2. ✅ `graphrag-ui/backend/services/graphrag_service.py`
   - 添加 sys.path 設定 (行 1-8)

3. ✅ `graphrag-ui/backend/requirements.txt`
   - 添加 pyyaml 和 pyarrow 依賴

### 新建的檔案

4. ✅ `graphrag-ui/backend/test_import.py`
   - GraphRAG 模組導入測試腳本

5. ✅ `graphrag-ui/backend/run.sh`
   - 服務啟動腳本

6. ✅ `graphrag-ui/backend/README.md`
   - 使用說明文檔

7. ✅ `graphrag-ui/backend/IMPORT_FIX.md`
   - 修復報告（本檔案）

## 最佳實踐

### 為什麼使用 sys.path.insert(0, ...)?

```python
sys.path.insert(0, str(project_root))  # ✅ 推薦
# vs
sys.path.append(str(project_root))     # ❌ 不推薦
```

**原因**：
- `insert(0, ...)` 將路徑添加到搜尋順序的**最前面**
- 確保優先使用專案內的 `graphrag` 模組
- 避免與系統安裝的其他套件衝突

### 為什麼檢查路徑是否已存在?

```python
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

**原因**：
- 防止重複添加相同路徑
- 避免 `sys.path` 過度膨脹
- 提高導入效率

### 為什麼使用 Path.absolute()?

```python
project_root = Path(__file__).parent.parent.parent.absolute()
```

**原因**：
- 確保路徑為絕對路徑
- 避免相對路徑導致的定位問題
- 提高程式碼可移植性

## 後續建議

### 1. 考慮使用 PYTHONPATH 環境變數

```bash
export PYTHONPATH="/Users/shengfanwu/GitHub/graphrag:$PYTHONPATH"
python main.py
```

### 2. 考慮安裝 GraphRAG 為可編輯套件

```bash
cd /Users/shengfanwu/GitHub/graphrag
pip install -e .
```

**優點**：
- 不需要修改 `sys.path`
- 符合 Python 套件標準做法
- 更容易管理依賴

### 3. 監控日誌

確保啟動時檢查日誌：
```python
logger.info(f"Successfully loaded GraphRAG config from {self.settings_path}")
logger.info(f"Successfully initialized ParquetDataAdapter for {self.data_dir}")
```

## 總結

✅ **問題已修復**：GraphRAG 模組現在可以正確導入
✅ **服務可啟動**：GraphRagService 能夠成功初始化
✅ **依賴已補齊**：添加了 pyyaml 和 pyarrow
✅ **文檔已完善**：提供了測試腳本和使用說明

修復方案簡單有效，只需在程式碼開頭動態調整 Python 模組搜尋路徑即可。
