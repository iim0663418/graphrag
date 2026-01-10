# GraphRAG 配置參考手冊

## 📋 配置檔案結構

GraphRAG 使用 YAML 格式的配置檔案，主要配置項目如下：

### 🧠 LLM 配置 (llm)

#### OpenAI 配置
```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat
  model: gpt-4
  max_tokens: 4000
  temperature: 0.0
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0
  max_retries: 5
  retry_delay: 2.0
```

#### Azure OpenAI 配置
```yaml
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_chat
  model: gpt-4
  api_base: ${GRAPHRAG_API_BASE}
  api_version: "2024-02-15-preview"
  deployment_name: ${GRAPHRAG_LLM_DEPLOYMENT_NAME}
  max_tokens: 4000
  temperature: 0.0
  max_retries: 5
  retry_delay: 2.0
```

### 🔤 嵌入模型配置 (embeddings)

#### OpenAI Embeddings
```yaml
embeddings:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_embedding
  model: text-embedding-ada-002
  max_retries: 5
  retry_delay: 2.0
```

#### Azure OpenAI Embeddings
```yaml
embeddings:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_embedding
  model: text-embedding-ada-002
  api_base: ${GRAPHRAG_API_BASE}
  api_version: "2024-02-15-preview"
  deployment_name: ${GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME}
```

### 🗄️ 向量儲存配置 (vector_store)

#### Azure AI Search
```yaml
vector_store:
  type: azure_ai_search
  url: ${AZURE_AI_SEARCH_URL_ENDPOINT}
  api_key: ${AZURE_AI_SEARCH_API_KEY}
  index_name: "graphrag-index"
  semantic_configuration_name: "default"
```

#### LanceDB
```yaml
vector_store:
  type: lancedb
  db_uri: "./lancedb"
  table_name: "vectors"
  metric: "cosine"
```

### 📁 輸入配置 (input)

#### 檔案輸入
```yaml
input:
  type: file
  file_type: text
  base_dir: "input"
  file_encoding: utf-8
  file_pattern: ".*\\.txt$"
```

#### CSV 輸入
```yaml
input:
  type: file
  file_type: csv
  base_dir: "input"
  source_column: "text"
  timestamp_column: "date"
  title_column: "title"
```

### 💾 儲存配置 (storage)

#### 本地檔案儲存
```yaml
storage:
  type: file
  base_dir: "output"
```

#### Azure Blob Storage
```yaml
storage:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-output"
  base_dir: "output"
```

### 🧩 文字分割配置 (chunks)

```yaml
chunks:
  size: 1200
  overlap: 100
  group_by_columns: ["id"]
  strategy: "tokens"
```

### 🔍 實體抽取配置 (entity_extraction)

```yaml
entity_extraction:
  prompt: "prompts/entity_extraction.txt"
  entity_types: ["person", "organization", "location"]
  max_gleanings: 1
  strategy:
    type: "graph_intelligence"
```

### 🔗 關係抽取配置 (relationship_extraction)

```yaml
relationship_extraction:
  prompt: "prompts/relationship_extraction.txt"
  max_gleanings: 1
  strategy:
    type: "graph_intelligence"
```

### 👥 社群檢測配置 (community_detection)

```yaml
community_detection:
  max_cluster_size: 10
  strategy:
    type: "leiden"
    max_cluster_size: 10
    use_lcc: true
    resolution: 1.0
    randomness: 0.1
```

### 📝 摘要生成配置 (summarize_descriptions)

```yaml
summarize_descriptions:
  prompt: "prompts/summarize_descriptions.txt"
  max_length: 500
  strategy:
    type: "graph_intelligence"
```

### ⚡ 並行處理配置 (parallelization)

```yaml
parallelization:
  stagger: 0.3
  num_threads: 4
```

### 🗂️ 快取配置 (cache)

#### 檔案快取
```yaml
cache:
  type: file
  base_dir: "cache"
```

#### Azure Blob 快取
```yaml
cache:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-cache"
```

### 📊 報告配置 (reporting)

```yaml
reporting:
  type: file
  base_dir: "reports"
```

## 🌍 環境變數參考

### 必要環境變數

```bash
# LLM API 配置
export GRAPHRAG_API_KEY="your-api-key"
export GRAPHRAG_API_BASE="https://your-resource.openai.azure.com"
export GRAPHRAG_API_VERSION="2024-02-15-preview"

# 部署名稱 (Azure OpenAI)
export GRAPHRAG_LLM_DEPLOYMENT_NAME="gpt-4"
export GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002"

# 向量儲存 (Azure AI Search)
export AZURE_AI_SEARCH_URL_ENDPOINT="https://your-search.search.windows.net"
export AZURE_AI_SEARCH_API_KEY="your-search-key"

# 儲存 (Azure Blob)
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."
```

### 可選環境變數

```bash
# 效能調優
export GRAPHRAG_LLM_TPM=60000          # Tokens per minute
export GRAPHRAG_LLM_RPM=1000           # Requests per minute
export GRAPHRAG_EMBEDDING_TPM=150000   # Embedding tokens per minute
export GRAPHRAG_EMBEDDING_RPM=3000     # Embedding requests per minute

# 文字處理
export GRAPHRAG_CHUNK_SIZE=1200
export GRAPHRAG_CHUNK_OVERLAP=100

# 日誌設定
export GRAPHRAG_LOG_LEVEL=INFO
export GRAPHRAG_LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 快取設定
export GRAPHRAG_CACHE_TYPE=file
export GRAPHRAG_CACHE_BASE_DIR=cache
```

## 📝 完整配置範例

### 基本配置 (settings.yaml)
```yaml
# GraphRAG 基本配置
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_chat
  model: gpt-4
  api_base: ${GRAPHRAG_API_BASE}
  api_version: ${GRAPHRAG_API_VERSION}
  deployment_name: ${GRAPHRAG_LLM_DEPLOYMENT_NAME}
  max_tokens: 4000
  temperature: 0.0

embeddings:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_embedding
  model: text-embedding-ada-002
  api_base: ${GRAPHRAG_API_BASE}
  api_version: ${GRAPHRAG_API_VERSION}
  deployment_name: ${GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME}

vector_store:
  type: azure_ai_search
  url: ${AZURE_AI_SEARCH_URL_ENDPOINT}
  api_key: ${AZURE_AI_SEARCH_API_KEY}

input:
  type: file
  file_type: text
  base_dir: "input"
  file_encoding: utf-8

storage:
  type: file
  base_dir: "output"

cache:
  type: file
  base_dir: "cache"

chunks:
  size: ${GRAPHRAG_CHUNK_SIZE:1200}
  overlap: ${GRAPHRAG_CHUNK_OVERLAP:100}

parallelization:
  stagger: 0.3
  num_threads: 4

entity_extraction:
  max_gleanings: 1

relationship_extraction:
  max_gleanings: 1

community_detection:
  max_cluster_size: 10

reporting:
  type: file
  base_dir: "reports"
```

### 進階配置範例
```yaml
# 進階 GraphRAG 配置
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_chat
  model: gpt-4
  api_base: ${GRAPHRAG_API_BASE}
  api_version: ${GRAPHRAG_API_VERSION}
  deployment_name: ${GRAPHRAG_LLM_DEPLOYMENT_NAME}
  max_tokens: 4000
  temperature: 0.0
  max_retries: 10
  retry_delay: 2.0
  concurrent_requests: 5

embeddings:
  api_key: ${GRAPHRAG_API_KEY}
  type: azure_openai_embedding
  model: text-embedding-ada-002
  api_base: ${GRAPHRAG_API_BASE}
  api_version: ${GRAPHRAG_API_VERSION}
  deployment_name: ${GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME}
  batch_size: 16
  max_retries: 10

vector_store:
  type: azure_ai_search
  url: ${AZURE_AI_SEARCH_URL_ENDPOINT}
  api_key: ${AZURE_AI_SEARCH_API_KEY}
  index_name: "graphrag-vectors"
  semantic_configuration_name: "semantic-config"

input:
  type: file
  file_type: text
  base_dir: "input"
  file_encoding: utf-8
  file_pattern: ".*\\.(txt|md|pdf)$"

storage:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-data"
  base_dir: "output"

cache:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-cache"

chunks:
  size: 1500
  overlap: 150
  group_by_columns: ["source", "title"]
  strategy: "tokens"

parallelization:
  stagger: 0.5
  num_threads: 8

entity_extraction:
  prompt: "prompts/custom_entity_extraction.txt"
  entity_types: ["PERSON", "ORGANIZATION", "LOCATION", "EVENT", "CONCEPT"]
  max_gleanings: 2
  strategy:
    type: "graph_intelligence"
    llm:
      max_tokens: 2000

relationship_extraction:
  prompt: "prompts/custom_relationship_extraction.txt"
  max_gleanings: 2
  strategy:
    type: "graph_intelligence"

community_detection:
  max_cluster_size: 15
  strategy:
    type: "leiden"
    max_cluster_size: 15
    use_lcc: true
    resolution: 1.2
    randomness: 0.1

summarize_descriptions:
  prompt: "prompts/custom_summarize.txt"
  max_length: 800
  strategy:
    type: "graph_intelligence"

reporting:
  type: blob
  connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  container_name: "graphrag-reports"
```

## 🔧 配置驗證

### 驗證配置檔案
```bash
# 驗證配置語法
graphrag config validate --config settings.yaml

# 測試 API 連線
graphrag config test --config settings.yaml
```

### 配置檔案除錯
```bash
# 顯示解析後的配置
graphrag config show --config settings.yaml

# 檢查環境變數
graphrag config env --config settings.yaml
```

這份配置參考手冊提供了 GraphRAG 所有主要配置選項的詳細說明和範例，幫助使用者根據需求進行客製化配置。
