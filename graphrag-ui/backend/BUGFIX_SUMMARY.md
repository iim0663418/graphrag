# 後端服務啟動問題修復總結

## 問題描述

**錯誤訊息**：`ModuleNotFoundError: No module named 'datashaper'`

**根本原因**：
1. 後端服務依賴 GraphRAG 核心模組
2. GraphRAG 需要 `datashaper` 作為核心依賴
3. 原始的 `requirements.txt` 只包含 FastAPI 相關基礎依賴
4. 未安裝 GraphRAG 及其完整依賴鏈

## 修復方案

### 1. 更新 `requirements.txt`

**文件位置**：`graphrag-ui/backend/requirements.txt`

**新增內容**：
```txt
# GraphRAG 及其核心依賴
datashaper>=0.0.49
environs>=11.0.0

# GraphRAG LLM 依賴
openai>=1.37.1
nltk==3.9.1
tiktoken>=0.7.0

# GraphRAG 數據科學依賴
numpy>=1.25.2
numba==0.60.0
scipy==1.12.0
networkx>=3
graspologic>=3.4.1
fastparquet>=2024.2.0

# GraphRAG 其他依賴
tenacity>=9.0.0
python-dotenv>=1.0.0
pyaml-env>=1.2.1
aiolimiter>=1.1.0
uvloop>=0.20.0
nest-asyncio>=1.6.0

# Azure 依賴（如需要）
azure-search-documents>=11.4.0
lancedb>=0.11.0
```

### 2. 修復 `start_backend.sh`

**文件位置**：`graphrag-ui/backend/start_backend.sh`

**主要改進**：
- 自動檢測 `datashaper` 和 `graphrag` 模組
- 缺失時自動安裝所有依賴
- 從專案根目錄安裝 GraphRAG 本地版本（開發模式）
- 完整的錯誤處理和用戶提示

**關鍵代碼段**：
```bash
# 驗證依賴
python -c "import fastapi, uvicorn, pandas, pydantic, datashaper, graphrag" || {
    echo "正在安裝依賴..."
    pip install -q -r requirements.txt

    # 從專案根目錄安裝 GraphRAG
    GRAPHRAG_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    if [ -f "$GRAPHRAG_ROOT/pyproject.toml" ]; then
        pip install -q -e "$GRAPHRAG_ROOT"
    fi
}
```

### 3. 修復 `run.sh`

**文件位置**：`graphrag-ui/backend/run.sh`

**主要改進**：
- 同樣支持 GraphRAG 本地版本安裝
- 每次執行都會重新安裝依賴（適合開發）

### 4. 新增 `install_dependencies.sh`

**文件位置**：`graphrag-ui/backend/install_dependencies.sh`

**功能**：
- 獨立的依賴安裝腳本
- 完整的 Python 版本檢查（需要 3.10-3.12）
- 自動創建虛擬環境
- 從專案根目錄安裝 GraphRAG（可編輯模式）
- 驗證所有依賴是否正確安裝

**使用方法**：
```bash
cd graphrag-ui/backend
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### 5. 新增 `verify_setup.sh`

**文件位置**：`graphrag-ui/backend/verify_setup.sh`

**功能**：
- 全面的環境驗證腳本
- 檢查 Python 版本
- 檢查所有必要模組
- 檢查 GraphRAG 安裝模式（開發/標準）
- 測試主程式導入

**使用方法**：
```bash
cd graphrag-ui/backend
chmod +x verify_setup.sh
./verify_setup.sh
```

### 6. 新增 `README_SETUP.md`

**文件位置**：`graphrag-ui/backend/README_SETUP.md`

**內容**：
- 問題診斷說明
- 詳細的安裝步驟（4 種方法）
- 環境要求說明
- 故障排除指南
- 開發和生產部署建議

## 修復後的啟動流程

### 方法 1：使用安裝腳本（推薦首次設置）

```bash
cd graphrag-ui/backend
./install_dependencies.sh
./start_backend.sh
```

### 方法 2：直接啟動（自動安裝）

```bash
cd graphrag-ui/backend
./start_backend.sh
```

啟動腳本會自動：
1. 檢查虛擬環境
2. 檢測缺失的依賴
3. 自動安裝所有必要套件
4. 從專案根目錄安裝 GraphRAG
5. 啟動服務並執行健康檢查

### 方法 3：驗證後啟動

```bash
cd graphrag-ui/backend
./verify_setup.sh  # 驗證環境
./start_backend.sh # 啟動服務
```

## 技術細節

### GraphRAG 安裝模式

採用 **可編輯模式（editable mode）** 安裝：

```bash
pip install -e /path/to/graphrag
```

**優點**：
1. 對 GraphRAG 原始碼的修改立即生效
2. 不需要重新安裝套件
3. 適合同時開發 GraphRAG 核心和 UI
4. 保持代碼同步

### 依賴解析

依賴安裝順序：
1. 基礎依賴（FastAPI, Uvicorn, Pandas 等）
2. GraphRAG 特定依賴（從 `requirements.txt`）
3. GraphRAG 本地版本（從專案根目錄）

### 錯誤處理

腳本包含多層錯誤檢查：
1. Python 版本驗證
2. 虛擬環境存在性檢查
3. 依賴安裝驗證
4. 模組導入測試
5. 服務健康檢查

## 驗證修復

執行以下命令確認修復成功：

```bash
cd graphrag-ui/backend
source venv/bin/activate
python -c "import datashaper, graphrag; print('✅ 所有依賴正常')"
```

預期輸出：
```
✅ 所有依賴正常
```

## 環境要求

- **Python**：3.10、3.11 或 3.12
- **作業系統**：macOS、Linux、Windows
- **磁碟空間**：約 500MB（用於所有依賴）
- **網路**：需要下載 PyPI 套件

## 後續維護

### 更新依賴

```bash
cd graphrag-ui/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 重新安裝

```bash
cd graphrag-ui/backend
rm -rf venv
./install_dependencies.sh
```

### 切換到生產模式

修改 `requirements.txt`，固定版本號：
```txt
fastapi==0.115.12  # 而非 >=0.115.12
```

## 相關文件

1. **README_SETUP.md** - 詳細設置說明
2. **install_dependencies.sh** - 依賴安裝腳本
3. **verify_setup.sh** - 環境驗證腳本
4. **start_backend.sh** - 服務啟動腳本（已修復）
5. **run.sh** - 開發模式啟動腳本（已修復）
6. **requirements.txt** - 依賴列表（已更新）

## 測試結果

修復完成後，服務應能正常啟動並顯示：

```
==========================================
GraphRAG UI Backend Service Startup
==========================================
✓ 啟動 Python 虛擬環境...
✓ 驗證必要依賴...
✓ 環境變數設定：
  - GRAPHRAG_SETTINGS_PATH: ./settings.yaml
  - GRAPHRAG_DATA_DIR: ./output
✓ 啟動 FastAPI 服務於 http://0.0.0.0:8000 ...
✅ 後端服務健康檢查通過！

==========================================
後端服務已成功啟動並可用
API 文件: http://localhost:8000/docs
==========================================
```

## 總結

**修復項目**：
- ✅ 更新 `requirements.txt` 包含所有 GraphRAG 依賴
- ✅ 修復 `start_backend.sh` 自動安裝缺失依賴
- ✅ 修復 `run.sh` 支持 GraphRAG 本地安裝
- ✅ 新增 `install_dependencies.sh` 獨立安裝腳本
- ✅ 新增 `verify_setup.sh` 環境驗證腳本
- ✅ 新增 `README_SETUP.md` 詳細文檔

**修復狀態**：完成 ✅

**預期結果**：後端服務能成功啟動，無 `ModuleNotFoundError` 錯誤
