# 本地化 GraphRAG 方案設計

## 問題分析

### Microsoft GraphRAG 核心弱點
1. **索引成本高**：大量 LLM API 調用（實體提取、關係建構、社群摘要）
2. **模型選擇受限**：主要依賴 OpenAI/Azure OpenAI

## 本地化解決方案

### 架構設計
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LMstudio      │    │  Local GraphRAG │    │   Web UI        │
│   - LLM Server  │◄──►│   - 實體提取     │◄──►│   - 文檔管理     │
│   - 嵌入模型     │    │   - 關係建構     │    │   - 查詢介面     │
│   - API 相容     │    │   - 圖推理       │    │   - 結果視覺化   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心組件

#### 1. LMstudio 整合層
```python
# lmstudio_client.py
class LMStudioClient:
    def __init__(self, base_url="http://localhost:1234"):
        self.base_url = base_url
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
    
    def chat_completion(self, messages, model="local-model"):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1
        )
    
    def embedding(self, text, model="embedding-model"):
        return self.client.embeddings.create(
            model=model,
            input=text
        )
```

#### 2. 成本優化策略
```python
# cost_optimizer.py
class LocalGraphRAGOptimizer:
    def __init__(self):
        self.entity_cache = {}
        self.relationship_cache = {}
    
    def batch_entity_extraction(self, texts, batch_size=10):
        """批次處理降低 LLM 調用次數"""
        batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]
        results = []
        
        for batch in batches:
            combined_text = "\n---\n".join(batch)
            entities = self.extract_entities_batch(combined_text)
            results.extend(entities)
        
        return results
    
    def cached_relationship_extraction(self, entity_pairs):
        """關係提取快取機制"""
        cache_key = hash(tuple(sorted(entity_pairs)))
        if cache_key in self.relationship_cache:
            return self.relationship_cache[cache_key]
        
        relationships = self.extract_relationships(entity_pairs)
        self.relationship_cache[cache_key] = relationships
        return relationships
```

#### 3. 模型配置管理
```python
# model_config.py
LOCAL_MODELS = {
    "llm": {
        "model_name": "llama-3.1-8b-instruct",
        "context_length": 8192,
        "temperature": 0.1
    },
    "embedding": {
        "model_name": "bge-large-zh-v1.5",
        "dimension": 1024
    }
}

class ModelManager:
    def __init__(self, lmstudio_client):
        self.client = lmstudio_client
        self.models = LOCAL_MODELS
    
    def get_available_models(self):
        """獲取 LMstudio 可用模型"""
        return self.client.models.list()
    
    def switch_model(self, model_type, model_name):
        """動態切換模型"""
        self.models[model_type]["model_name"] = model_name
```

### 實作步驟

#### Phase 1: 基礎整合（1週）
```bash
# 1. 安裝依賴
pip install graphrag openai sentence-transformers

# 2. 配置 LMstudio
# - 下載 Llama 3.1 8B Instruct
# - 下載 BGE-Large-ZH 嵌入模型
# - 啟動 API 服務（端口 1234）

# 3. 修改 GraphRAG 配置
```

```yaml
# settings.yaml
models:
  - model: local-llm
    type: chat
    api_base: http://localhost:1234/v1
    api_key: lm-studio
    
  - model: local-embedding  
    type: embedding
    api_base: http://localhost:1234/v1
    api_key: lm-studio
```

#### Phase 2: 成本優化（1週）
```python
# local_graphrag.py
class LocalGraphRAG:
    def __init__(self):
        self.lm_client = LMStudioClient()
        self.optimizer = LocalGraphRAGOptimizer()
        
    def optimized_indexing(self, documents):
        """優化的索引流程"""
        # 1. 批次實體提取
        entities = self.optimizer.batch_entity_extraction(documents)
        
        # 2. 快取關係提取  
        relationships = self.optimizer.cached_relationship_extraction(entities)
        
        # 3. 增量社群檢測
        communities = self.incremental_community_detection(relationships)
        
        return {
            "entities": entities,
            "relationships": relationships, 
            "communities": communities
        }
```

#### Phase 3: UI 整合（1週）
```python
# app.py - Gradio UI
import gradio as gr
from local_graphrag import LocalGraphRAG

def create_ui():
    graphrag = LocalGraphRAG()
    
    with gr.Blocks(title="本地 GraphRAG") as app:
        gr.Markdown("# 🏠 本地化 GraphRAG 系統")
        
        with gr.Tab("文檔索引"):
            file_input = gr.File(label="上傳文檔", file_count="multiple")
            index_btn = gr.Button("開始索引", variant="primary")
            index_output = gr.Textbox(label="索引結果")
            
        with gr.Tab("智能查詢"):
            query_input = gr.Textbox(label="輸入問題")
            search_btn = gr.Button("搜尋", variant="primary") 
            result_output = gr.Textbox(label="查詢結果")
            
        with gr.Tab("模型管理"):
            model_dropdown = gr.Dropdown(label="選擇模型")
            model_info = gr.Textbox(label="模型資訊")
    
    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
```

### 效能優化策略

#### 1. 記憶體管理
```python
# memory_optimizer.py
class MemoryOptimizer:
    def __init__(self, max_cache_size=1000):
        self.max_cache_size = max_cache_size
        self.entity_cache = {}
        
    def smart_caching(self, key, value):
        """智能快取管理"""
        if len(self.entity_cache) >= self.max_cache_size:
            # LRU 淘汰策略
            oldest_key = next(iter(self.entity_cache))
            del self.entity_cache[oldest_key]
        
        self.entity_cache[key] = value
```

#### 2. 並行處理
```python
# parallel_processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def parallel_entity_extraction(self, text_chunks):
        """並行實體提取"""
        tasks = []
        for chunk in text_chunks:
            task = asyncio.create_task(self.extract_entities_async(chunk))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

### 部署配置

#### Docker 部署
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860

CMD ["python", "app.py"]
```

#### 資源需求
```yaml
# 最低配置
CPU: 8 核心
RAM: 16GB
GPU: RTX 4060 8GB (可選)
存儲: 50GB SSD

# 推薦配置  
CPU: 16 核心
RAM: 32GB
GPU: RTX 4090 24GB
存儲: 100GB NVMe SSD
```

## 預期效益

### 成本節省
- **LLM 調用成本**: 100% 節省（純本地）
- **索引時間**: 減少 60%（批次處理 + 快取）
- **硬體成本**: 一次性投資，長期使用

### 技術優勢
- ✅ **完全離線**: 無需網路連接
- ✅ **資料隱私**: 資料不離開本地
- ✅ **模型自由**: 支援任何 LMstudio 相容模型
- ✅ **成本可控**: 無 API 調用費用

---
*設計日期：2026-01-10*
*預計開發週期：3週*
