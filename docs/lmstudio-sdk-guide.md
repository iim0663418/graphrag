# LMstudio Python SDK 完整指南

## 安裝與基本設置

### 安裝
```bash
pip install lmstudio
```

### 基本導入
```python
import lmstudio as lms
```

## 核心功能概覽

### 🎯 **主要能力**
- **LLM 對話**：多輪聊天、文本完成
- **嵌入模型**：文本向量化
- **模型管理**：載入、卸載、列表管理
- **代理流程**：工具調用、自主代理
- **流式處理**：實時響應流

### 🔧 **API 架構**
```python
# 三種 API 模式
# 1. 便利 API (Interactive)
model = lms.llm()

# 2. 作用域資源 API (Scoped Resource)  
with lms.Client() as client:
    model = client.llm.model()

# 3. 異步 API (Asynchronous)
async with lms.AsyncClient() as client:
    model = await client.llm.model()
```

## LLM 對話功能

### 基本對話
```python
# 快速響應
model = lms.llm("qwen/qwen3-4b-2507")
result = model.respond("What is the meaning of life?")
print(result)

# 流式響應
for fragment in model.respond_stream("Tell me a story"):
    print(fragment.content, end="", flush=True)
```

### 多輪對話管理
```python
# 創建聊天上下文
chat = lms.Chat("You are a helpful AI assistant")

# 添加消息
chat.add_user_message("Hello!")
chat.add_assistant_message("Hi there!")

# 生成響應
result = model.respond(chat)
```

### 配置參數
```python
result = model.respond(chat, config={
    "temperature": 0.7,
    "maxTokens": 100,
    "topP": 0.9
})
```

## 嵌入模型功能

### 文本嵌入
```python
# 獲取嵌入模型
embedding_model = lms.embedding_model("nomic-embed-text-v1.5")

# 生成嵌入向量
embedding = embedding_model.embed("Hello, world!")
print(f"Embedding dimension: {len(embedding)}")
```

## 模型管理

### 列出模型
```python
# 列出已下載的模型
downloaded = lms.list_downloaded_models()

# 列出已載入的模型  
loaded = lms.list_loaded_models()
```

### 載入與卸載
```python
# 載入模型（如果未載入）
model = lms.llm("qwen/qwen3-4b-2507")

# 強制載入新實例
client = lms.get_default_client()
new_instance = client.llm.load_new_instance("qwen/qwen3-4b-2507")

# 卸載模型
model.unload()
```

### 模型配置
```python
# 設置 TTL（空閒自動卸載時間）
model = lms.llm("qwen/qwen3-4b-2507", ttl=3600)  # 1小時

# 自定義載入配置
model = client.llm.load_new_instance(
    "qwen/qwen3-4b-2507",
    config={
        "contextLength": 8192,
        "gpuOffload": 0.8
    }
)
```

## 進階功能

### 進度回調
```python
response = model.respond(
    "Complex question",
    on_prompt_processing_progress=lambda p: print(f"{p*100:.1f}% processed"),
    on_first_token=lambda: print("First token received!"),
    on_prediction_fragment=lambda f: print(f.content, end=""),
    on_message=chat.append  # 自動添加到聊天歷史
)
```

### 預測統計
```python
result = model.respond("Hello")

print(f"Model: {result.model_info.display_name}")
print(f"Tokens: {result.stats.predicted_tokens_count}")
print(f"Time to first token: {result.stats.time_to_first_token_sec}s")
print(f"Stop reason: {result.stats.stop_reason}")
```

### 取消預測
```python
import threading
import time

# 啟動預測
prediction_stream = model.respond_stream("Long response...")

# 在另一個線程中取消
def cancel_after_delay():
    time.sleep(2)
    prediction_stream.cancel()

threading.Thread(target=cancel_after_delay).start()

# 處理流
try:
    for fragment in prediction_stream:
        print(fragment.content, end="")
except Exception as e:
    print(f"Prediction cancelled: {e}")
```

## 實用示例

### 多輪聊天機器人
```python
def create_chatbot():
    model = lms.llm()
    chat = lms.Chat("You are a helpful assistant")
    
    while True:
        try:
            user_input = input("You: ")
            if not user_input:
                break
                
            chat.add_user_message(user_input)
            
            print("Bot: ", end="", flush=True)
            prediction_stream = model.respond_stream(
                chat,
                on_message=chat.append
            )
            
            for fragment in prediction_stream:
                print(fragment.content, end="", flush=True)
            print()
            
        except EOFError:
            break

if __name__ == "__main__":
    create_chatbot()
```

### 批量嵌入處理
```python
def batch_embeddings(texts, model_name="nomic-embed-text-v1.5"):
    embedding_model = lms.embedding_model(model_name)
    embeddings = []
    
    for text in texts:
        embedding = embedding_model.embed(text)
        embeddings.append(embedding)
    
    return embeddings

# 使用示例
texts = ["Hello world", "How are you?", "Goodbye"]
embeddings = batch_embeddings(texts)
```

### 模型性能監控
```python
class ModelMonitor:
    def __init__(self, model_name):
        self.model = lms.llm(model_name)
        self.stats = []
    
    def monitored_respond(self, prompt):
        result = self.model.respond(prompt)
        
        self.stats.append({
            "tokens": result.stats.predicted_tokens_count,
            "ttft": result.stats.time_to_first_token_sec,
            "total_time": result.stats.total_time_sec,
            "stop_reason": result.stats.stop_reason
        })
        
        return result
    
    def get_average_stats(self):
        if not self.stats:
            return None
            
        return {
            "avg_tokens": sum(s["tokens"] for s in self.stats) / len(self.stats),
            "avg_ttft": sum(s["ttft"] for s in self.stats) / len(self.stats),
            "avg_total_time": sum(s["total_time"] for s in self.stats) / len(self.stats)
        }
```

## 錯誤處理

### 常見異常
```python
try:
    model = lms.llm("non-existent-model")
except Exception as e:
    print(f"Model loading failed: {e}")

try:
    result = model.respond("Hello", config={"maxTokens": -1})
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

### 超時設置
```python
# 設置同步 API 超時（60秒默認）
lms.set_sync_api_timeout(120)  # 2分鐘

# 查詢當前超時設置
timeout = lms.get_sync_api_timeout()
print(f"Current timeout: {timeout} seconds")

# 禁用超時
lms.set_sync_api_timeout(None)
```

## 與 GraphRAG 整合要點

### 關鍵整合點
1. **LLM 調用**：使用 `model.respond()` 替代 OpenAI API
2. **嵌入生成**：使用 `embedding_model.embed()` 
3. **模型管理**：動態載入/卸載節省記憶體
4. **批量處理**：利用本地模型優勢進行批量操作

### 性能優化建議
- 使用 TTL 自動管理模型記憶體
- 批量處理減少模型載入次數
- 監控統計數據優化參數
- 合理設置上下文長度

---
*更新日期：2026-01-10*
*SDK 版本：1.5.0+*
