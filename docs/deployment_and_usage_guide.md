# GraphRAG 部署模式與使用說明

## 📦 部署模式概覽

GraphRAG 採用 **套件分發模式**，而非傳統的 SaaS 或容器化部署。使用者需要自行安裝套件並配置相關服務。

## 🔄 完整使用流程

### 階段 1: 安裝套件

#### 使用 pip 安裝
```bash
pip install graphrag
```

#### 使用 Poetry 安裝
```bash
poetry add graphrag
```

#### 驗證安裝
```bash
graphrag --help
```

### 階段 2: 環境準備

#### 2.1 準備 LLM 服務
選擇以下其中一種：

**選項 A: OpenAI API**
```bash
export GRAPHRAG_API_KEY="your-openai-api-key"
export GRAPHRAG_LLM_TYPE="openai_chat"
export GRAPHRAG_EMBEDDING_TYPE="openai_embedding"
```

**選項 B: Azure OpenAI**
```bash
export GRAPHRAG_API_KEY="your-azure-openai-key"
export GRAPHRAG_API_BASE="https://your-resource.openai.azure.com"
export GRAPHRAG_API_VERSION="2024-02-15-preview"
export GRAPHRAG_LLM_TYPE="azure_openai_chat"
export GRAPHRAG_EMBEDDING_TYPE="azure_openai_embedding"
```

#### 2.2 準備向量儲存
選擇以下其中一種：

**選項 A: Azure AI Search**
```bash
export AZURE_AI_SEARCH_URL_ENDPOINT="https://your-search-service.search.windows.net"
export AZURE_AI_SEARCH_API_KEY="your-search-api-key"
```

**選項 B: LanceDB (本地)**
```bash
# 無需額外配置，會自動使用本地檔案
```

### 階段 3: 專案初始化

#### 3.1 建立專案目錄
```bash
mkdir my-graphrag-project
cd my-graphrag-project
```

#### 3.2 初始化 GraphRAG
```bash
graphrag init --root .
```

這會建立以下結構：
```
my-graphrag-project/
├── settings.yaml          # 主要配置檔
├── .env                   # 環境變數
├── input/                 # 輸入文件目錄
├── output/                # 輸出結果目錄
└── prompts/              # 自定義提示詞
```

#### 3.3 配置 settings.yaml
```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_chat
  model: gpt-4
  api_base: ${GRAPHRAG_API_BASE}
  api_version: ${GRAPHRAG_API_VERSION}

embeddings:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_embedding
  model: text-embedding-ada-002
  api_base: ${GRAPHRAG_API_BASE}

vector_store:
  type: azure_ai_search
  url: ${AZURE_AI_SEARCH_URL_ENDPOINT}
  api_key: ${AZURE_AI_SEARCH_API_KEY}

input:
  type: file
  file_type: text
  base_dir: "input"

storage:
  type: file
  base_dir: "output"
```

### 階段 4: 資料處理

#### 4.1 準備輸入資料
將文件放入 `input/` 目錄：
```bash
cp your-documents.txt input/
```

#### 4.2 執行索引建立
```bash
graphrag index --root .
```

這個過程會：
- 分析文件內容
- 抽取實體和關係
- 建立知識圖譜
- 生成向量嵌入
- 儲存到指定的向量資料庫

#### 4.3 監控進度
```bash
# 查看輸出目錄
ls -la output/

# 查看日誌
tail -f output/indexing-engine.log
```

### 階段 5: 查詢使用

#### 5.1 全域查詢 (Global Search)
```bash
graphrag query --root . --method global "什麼是這些文件的主要主題？"
```

#### 5.2 局部查詢 (Local Search)
```bash
graphrag query --root . --method local "找出與特定實體相關的資訊"
```

#### 5.3 程式化使用
```python
from graphrag.query.factories import get_global_search_engine

# 載入配置
config = load_config("./settings.yaml")

# 建立搜尋引擎
search_engine = get_global_search_engine(config)

# 執行查詢
result = search_engine.search("你的問題")
print(result.response)
```

## 🔧 進階配置

### 自定義提示詞
```bash
# 生成提示詞模板
graphrag prompt-tune --root . --config settings.yaml

# 編輯生成的提示詞
vim prompts/entity_extraction.txt
```

### 效能調優
```yaml
# settings.yaml 中的效能設定
parallelization:
  stagger: 0.3
  num_threads: 4

chunk_size: 1200
chunk_overlap: 100

llm:
  max_tokens: 4000
  temperature: 0.0
```

### 快取配置
```yaml
cache:
  type: file
  base_dir: "cache"
  
# 或使用 Azure Blob Storage
cache:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-cache"
```

## 🚨 常見問題與解決方案

### 問題 1: API 配額限制
```bash
# 調整速率限制
export GRAPHRAG_LLM_TPM=60000  # Tokens per minute
export GRAPHRAG_LLM_RPM=1000   # Requests per minute
```

### 問題 2: 記憶體不足
```yaml
# 減少並行處理
parallelization:
  num_threads: 2
  
# 減少區塊大小
chunk_size: 800
```

### 問題 3: 網路連線問題
```yaml
# 增加重試設定
llm:
  max_retries: 5
  retry_delay: 2.0
```

## 📊 成本估算

### OpenAI API 成本 (估算)
- **GPT-4**: ~$0.03/1K tokens
- **Embedding**: ~$0.0001/1K tokens
- **1MB 文件**: 約 $5-15 USD

### Azure 服務成本
- **Azure OpenAI**: 按使用量計費
- **Azure AI Search**: 基本層 ~$250/月
- **Azure Storage**: ~$0.02/GB/月

## 🔒 安全性建議

### API 金鑰管理
```bash
# 使用 .env 檔案
echo "GRAPHRAG_API_KEY=your-key" >> .env
echo ".env" >> .gitignore
```

### 資料隱私
- 敏感資料建議使用本地 LanceDB
- 考慮使用 Azure Private Endpoints
- 定期清理快取和暫存檔案

### 存取控制
```yaml
# 限制檔案存取權限
chmod 600 .env
chmod 600 settings.yaml
```

## 📈 監控與維運

### 日誌監控
```bash
# 啟用詳細日誌
export GRAPHRAG_LOG_LEVEL=DEBUG

# 查看即時日誌
tail -f output/indexing-engine.log
```

### 效能監控
```python
import time
from graphrag.index.api import build_index

start_time = time.time()
build_index(config)
print(f"索引建立耗時: {time.time() - start_time:.2f} 秒")
```

### 定期維護
```bash
# 清理舊快取
find cache/ -type f -mtime +7 -delete

# 備份重要配置
cp settings.yaml settings.yaml.backup
```

這份文件提供了 GraphRAG 從安裝到使用的完整指南，幫助使用者理解套件分發模式的特點和使用方式。
