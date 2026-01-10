# GraphRAG 故障排除指南

## 🚨 常見問題與解決方案

### 1. 安裝相關問題

#### 問題：Poetry 安裝失敗
```bash
# 錯誤訊息
ERROR: Could not find a version that satisfies the requirement graphrag

# 解決方案
# 1. 更新 pip 和 poetry
pip install --upgrade pip
poetry self update

# 2. 清除快取
poetry cache clear pypi --all
pip cache purge

# 3. 使用特定 Python 版本
poetry env use python3.10
```

#### 問題：依賴衝突
```bash
# 錯誤訊息
The current project's Python requirement (>=3.10,<3.13) is not compatible

# 解決方案
# 1. 檢查 Python 版本
python --version

# 2. 建立虛擬環境
python3.10 -m venv graphrag-env
source graphrag-env/bin/activate  # Linux/Mac
# 或
graphrag-env\Scripts\activate     # Windows

# 3. 重新安裝
pip install graphrag
```

### 2. 配置相關問題

#### 問題：API 金鑰無效
```bash
# 錯誤訊息
AuthenticationError: Invalid API key provided

# 解決方案
# 1. 檢查環境變數
echo $GRAPHRAG_API_KEY

# 2. 驗證 API 金鑰格式
# OpenAI: sk-...
# Azure: 32 字元的十六進位字串

# 3. 測試 API 連線
curl -H "Authorization: Bearer $GRAPHRAG_API_KEY" \
     https://api.openai.com/v1/models
```

#### 問題：Azure OpenAI 配置錯誤
```bash
# 錯誤訊息
InvalidRequestError: The API deployment for this resource does not exist

# 解決方案
# 1. 檢查部署名稱
az cognitiveservices account deployment list \
   --name your-openai-resource \
   --resource-group your-rg

# 2. 驗證 API 版本
export GRAPHRAG_API_VERSION="2024-02-15-preview"

# 3. 檢查端點格式
export GRAPHRAG_API_BASE="https://your-resource.openai.azure.com"
```

#### 問題：向量儲存連線失敗
```bash
# 錯誤訊息 (Azure AI Search)
ServiceRequestError: The request failed due to a client error

# 解決方案
# 1. 檢查搜尋服務狀態
az search service show --name your-search-service --resource-group your-rg

# 2. 驗證 API 金鑰
curl -H "api-key: $AZURE_AI_SEARCH_API_KEY" \
     "$AZURE_AI_SEARCH_URL_ENDPOINT/indexes?api-version=2023-11-01"

# 3. 檢查防火牆設定
# 確保允許來自執行環境的 IP 存取
```

### 3. 索引建立問題

#### 問題：記憶體不足
```bash
# 錯誤訊息
MemoryError: Unable to allocate array

# 解決方案
# 1. 減少並行處理
# settings.yaml
parallelization:
  num_threads: 2
  stagger: 1.0

# 2. 減少區塊大小
chunks:
  size: 800
  overlap: 50

# 3. 使用分批處理
# 將大檔案分割成小檔案處理
```

#### 問題：API 配額超限
```bash
# 錯誤訊息
RateLimitError: Rate limit reached for requests

# 解決方案
# 1. 調整速率限制
export GRAPHRAG_LLM_TPM=30000    # 降低 TPM
export GRAPHRAG_LLM_RPM=500      # 降低 RPM

# 2. 增加延遲
# settings.yaml
parallelization:
  stagger: 2.0  # 增加延遲時間

# 3. 減少並行請求
llm:
  concurrent_requests: 2
```

#### 問題：文件編碼錯誤
```bash
# 錯誤訊息
UnicodeDecodeError: 'utf-8' codec can't decode byte

# 解決方案
# 1. 檢查檔案編碼
file -I input/*.txt

# 2. 轉換編碼
iconv -f big5 -t utf-8 input/file.txt > input/file_utf8.txt

# 3. 設定正確編碼
# settings.yaml
input:
  file_encoding: "big5"  # 或其他編碼
```

### 4. 查詢相關問題

#### 問題：查詢結果為空
```bash
# 可能原因與解決方案

# 1. 檢查索引是否完成
ls -la output/
# 應該看到 entities.parquet, relationships.parquet 等檔案

# 2. 檢查向量儲存
# Azure AI Search
curl -H "api-key: $AZURE_AI_SEARCH_API_KEY" \
     "$AZURE_AI_SEARCH_URL_ENDPOINT/indexes/graphrag-index/docs/\$count?api-version=2023-11-01"

# 3. 調整查詢參數
graphrag query --root . --method global \
  --community-level 2 \
  --response-type "Multiple Paragraphs" \
  "your question"
```

#### 問題：查詢回應品質差
```bash
# 解決方案

# 1. 調整社群層級
graphrag query --root . --method global \
  --community-level 1  # 嘗試不同層級 0-3

# 2. 使用局部搜尋
graphrag query --root . --method local \
  "specific entity or topic"

# 3. 優化提示詞
graphrag prompt-tune --root . --config settings.yaml
# 編輯生成的提示詞檔案
```

### 5. 效能問題

#### 問題：索引建立太慢
```bash
# 優化方案

# 1. 增加並行處理
# settings.yaml
parallelization:
  num_threads: 8  # 根據 CPU 核心數調整

# 2. 使用更快的 LLM
llm:
  model: gpt-3.5-turbo  # 比 gpt-4 更快

# 3. 啟用快取
cache:
  type: file
  base_dir: "cache"
```

#### 問題：查詢回應太慢
```bash
# 優化方案

# 1. 使用本地向量儲存
vector_store:
  type: lancedb
  db_uri: "./lancedb"

# 2. 調整搜尋參數
# 減少檢索的文件數量

# 3. 使用更快的嵌入模型
embeddings:
  model: text-embedding-3-small  # 更快的模型
```

### 6. 儲存相關問題

#### 問題：Azure Blob Storage 存取錯誤
```bash
# 錯誤訊息
BlobServiceError: The specified container does not exist

# 解決方案
# 1. 建立容器
az storage container create \
  --name graphrag-output \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING"

# 2. 檢查權限
az storage container show \
  --name graphrag-output \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING"

# 3. 驗證連線字串格式
echo $AZURE_STORAGE_CONNECTION_STRING
```

#### 問題：本地檔案權限錯誤
```bash
# 錯誤訊息
PermissionError: [Errno 13] Permission denied

# 解決方案
# 1. 檢查目錄權限
ls -la output/

# 2. 修正權限
chmod 755 output/
chmod 644 output/*

# 3. 檢查磁碟空間
df -h .
```

### 7. 除錯工具與技巧

#### 啟用詳細日誌
```bash
# 設定日誌等級
export GRAPHRAG_LOG_LEVEL=DEBUG

# 查看即時日誌
tail -f output/indexing-engine.log

# 搜尋特定錯誤
grep -i error output/indexing-engine.log
```

#### 配置驗證
```bash
# 驗證配置檔案
python -c "
import yaml
with open('settings.yaml') as f:
    config = yaml.safe_load(f)
    print('配置檔案語法正確')
"

# 測試環境變數
python -c "
import os
print('API Key:', os.getenv('GRAPHRAG_API_KEY', 'Not Set'))
print('API Base:', os.getenv('GRAPHRAG_API_BASE', 'Not Set'))
"
```

#### 分步除錯
```bash
# 1. 測試 LLM 連線
python -c "
from graphrag.llm.openai import create_openai_chat_llm
llm = create_openai_chat_llm(api_key='your-key')
print('LLM 連線成功')
"

# 2. 測試向量儲存
python -c "
from graphrag.vector_stores import VectorStoreFactory
vs = VectorStoreFactory.create_vector_store(config)
print('向量儲存連線成功')
"

# 3. 測試檔案讀取
python -c "
import os
files = os.listdir('input/')
print(f'找到 {len(files)} 個輸入檔案')
"
```

### 8. 效能監控

#### 監控資源使用
```bash
# CPU 和記憶體監控
top -p $(pgrep -f graphrag)

# 磁碟 I/O 監控
iotop -p $(pgrep -f graphrag)

# 網路監控
netstat -i
```

#### 監控 API 使用
```bash
# 記錄 API 呼叫
export GRAPHRAG_LOG_LEVEL=DEBUG
grep -i "api" output/indexing-engine.log | wc -l

# 計算成本
python -c "
import re
with open('output/indexing-engine.log') as f:
    content = f.read()
    tokens = re.findall(r'tokens: (\d+)', content)
    total = sum(int(t) for t in tokens)
    print(f'總 Token 使用量: {total:,}')
"
```

這份故障排除指南涵蓋了 GraphRAG 使用過程中最常見的問題和解決方案，幫助使用者快速診斷和解決問題。
