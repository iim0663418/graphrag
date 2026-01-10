# Phase 3 效能優化指南

## 概述

Phase 3 實作了智能快取機制、批次處理和效能監控，目標是將 LLM 調用次數減少 30% 以上，並大幅提升索引速度。

## 核心功能

### 1. 智能快取系統 (cache_manager.py)

#### HashBasedCache - 基於雜湊的快取
```python
from graphrag_local.optimization import HashBasedCache

# 初始化快取
cache = HashBasedCache(
    cache_dir=".cache/graphrag_local",
    ttl_seconds=None,  # None = 永不過期
    max_size_mb=500,
    enable_persistence=True
)

# 使用快取
result = cache.get(text, context={"model": "llama3"})
if result is None:
    result = llm_process(text)
    cache.set(text, result, context={"model": "llama3"})
```

**特點**:
- SHA256 內容雜湊防止重複處理
- SQLite 持久化存儲
- TTL 過期機制
- 自動大小管理和淘汰策略

#### MultiLevelCache - 多層快取
```python
from graphrag_local.optimization import MultiLevelCache

cache = MultiLevelCache(
    cache_dir=".cache/graphrag_local/multilevel",
    l1_max_entries=1000,   # L1 記憶體快取
    l2_max_size_mb=500,    # L2 磁碟快取
)

# L1 快取未命中時自動查詢 L2
result = cache.get(text)
```

**特點**:
- L1: 快速記憶體快取 (LRU 淘汰)
- L2: 大容量磁碟快取
- 自動提升熱數據到 L1
- 統一的存取介面

#### EntityRelationshipCache - 實體關係專用快取
```python
from graphrag_local.optimization import EntityRelationshipCache

er_cache = EntityRelationshipCache(
    cache_dir=".cache/graphrag_local/entities",
    ttl_seconds=None
)

# 快取實體提取結果
entities = er_cache.get_entities(text, extraction_prompt)
if entities is None:
    entities = extract_entities(text)
    er_cache.set_entities(text, entities, extraction_prompt)
```

### 2. 批次處理系統 (batch_processor.py)

#### BatchProcessor - 基礎批次處理器
```python
from graphrag_local.optimization import BatchProcessor, BatchConfig

config = BatchConfig(
    min_batch_size=1,
    max_batch_size=32,
    max_wait_time_ms=100.0,
    adaptive_sizing=True,
    enable_cache_dedup=True
)

processor = BatchProcessor(config=config, cache=cache)

# 處理單個項目（自動批次化）
async def process_item(text):
    result = await processor.process(
        text,
        batch_fn=llm_batch_process,
        context={"model": "llama3"}
    )
    return result
```

**特點**:
- 自動累積請求成批次
- 可配置批次大小和等待時間
- 與快取系統整合
- 非同步處理

#### AdaptiveBatchProcessor - 自適應批次處理器
```python
from graphrag_local.optimization import AdaptiveBatchProcessor

processor = AdaptiveBatchProcessor(config=config, cache=cache)

# 自動調整批次大小以獲得最佳性能
# 基於處理時間動態優化
```

**特點**:
- 動態調整批次大小
- 基於性能指標自動優化
- 避免批次過大或過小

#### DedupBatchProcessor - 去重批次處理器
```python
from graphrag_local.optimization import DedupBatchProcessor

dedup = DedupBatchProcessor()

# 自動識別並去除批次內的重複項
results = await dedup.process_batch(texts, processor_fn)
```

**特點**:
- 批次內去重，每個唯一輸入只處理一次
- 結果自動映射回原始位置
- 顯著減少重複處理

#### TextChunkBatcher - 文本分塊批次處理器
```python
from graphrag_local.optimization import TextChunkBatcher

batcher = TextChunkBatcher(
    max_batch_tokens=8000,
    max_batch_size=32,
)

# 創建優化的批次（考慮 token 限制）
batches = batcher.create_batches(text_chunks)
```

**特點**:
- Token 感知的批次創建
- 最大化批次大小同時遵守限制
- 適用於有 token 限制的模型

### 3. 效能監控系統 (performance_monitor.py)

#### PerformanceMonitor - 效能監控器
```python
from graphrag_local.optimization import PerformanceMonitor

monitor = PerformanceMonitor(
    enable_memory_tracking=True,
    enable_detailed_logging=True
)

# 使用上下文管理器追蹤操作
with monitor.track("entity_extraction"):
    entities = extract_entities(text)

# 記錄 LLM 調用
monitor.record_llm_call(
    duration_s=0.5,
    cached=False,
    tokens_in=100,
    tokens_out=50
)

# 記錄批次操作
monitor.record_batch(batch_size=16)

# 計算效率指標
monitor.calculate_efficiency(
    total_items=1000,
    baseline_llm_calls=1000
)

# 導出指標
monitor.export_metrics("metrics.json")
monitor.print_summary()
```

**輸出範例**:
```
======================================================================
PERFORMANCE SUMMARY
======================================================================

Timing:
  Total Duration: 45.23s
  LLM Calls: 30.15s
  Embeddings: 12.08s
  Cache Lookups: 0.52s

Calls:
  Total LLM Calls: 700
  Cached LLM Hits: 300
  Total Embeddings: 1000
  Cached Embedding Hits: 450

Batching:
  Total Batches: 50
  Avg Batch Size: 14.5
  Max Batch Size: 32

Cache:
  Size: 125.50 MB
  Hit Rate: 42.5%

Efficiency:
  LLM Call Reduction: 30.0%
  Throughput: 22.10 items/sec

Memory:
  Peak: 856.23 MB
  Average: 645.10 MB
======================================================================
```

## 整合到 LMStudio 適配器

### 優化的 LLM 適配器

```python
from graphrag_local.adapters.lmstudio_optimized import OptimizedLMStudioChatAdapter

adapter = OptimizedLMStudioChatAdapter(
    model_name="qwen/qwen3-4b",
    config={
        "temperature": 0.7,
        "max_tokens": 2048,
        "batch_size": 16,
        "batch_wait_ms": 100.0,
    },
    enable_cache=True,
    enable_batching=True,
    cache_dir=".cache/graphrag_local/llm"
)

# 使用與標準適配器相同
response = await adapter.acreate(messages)

# 查看優化統計
stats = adapter.get_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']:.1f}%")
print(f"Avg batch size: {stats['batching']['avg_batch_size']:.1f}")
```

### 優化的 Embedding 適配器

```python
from graphrag_local.adapters.lmstudio_optimized import OptimizedLMStudioEmbeddingAdapter

adapter = OptimizedLMStudioEmbeddingAdapter(
    model_name="nomic-embed-text-v1.5",
    config={
        "batch_size": 32,
        "normalize": True,
    },
    enable_cache=True,
    enable_batching=True,
    cache_dir=".cache/graphrag_local/embeddings"
)

# 批次嵌入（自動去重和快取）
embeddings = await adapter.aembed_batch(texts)

# 查看統計
stats = adapter.get_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
```

## 配置文件設定

### settings.yaml 配置範例

```yaml
llm:
  type: lmstudio-chat
  model: "qwen/qwen3-4b-2507"
  temperature: 0.0
  max_tokens: 4000

  # Phase 3 優化設定
  enable_cache: true
  enable_batching: true
  batch_size: 16
  batch_wait_ms: 100.0
  cache_dir: ".cache/graphrag_local/llm"
  cache_ttl_seconds: null  # 永不過期
  cache_max_size_mb: 500

embeddings:
  llm:
    type: lmstudio-embedding
    model: "nomic-embed-text-v1.5"

    # Phase 3 優化設定
    enable_cache: true
    enable_batching: true
    batch_size: 32
    cache_dir: ".cache/graphrag_local/embeddings"
    cache_max_size_mb: 1000

# 效能監控
performance:
  enable_monitoring: true
  enable_memory_tracking: true
  export_metrics: true
  metrics_dir: ".metrics"
```

## 基準測試

### 運行基準測試

```bash
# 運行 Phase 3 基準測試
python graphrag_local/tests/benchmark_phase3.py

# 指定輸出目錄
python graphrag_local/tests/benchmark_phase3.py --output-dir ./benchmark_results

# 指定測試大小
python graphrag_local/tests/benchmark_phase3.py --test-size 2000
```

### 基準測試結果範例

```
======================================================================
BENCHMARK SUMMARY
======================================================================

📊 Cache Performance:
  Hash Cache Hit Rate: 80.0%
  Write Time: 0.45s
  Read Time: 0.12s

  Multi-Level Cache:
    L1 Hits: 450
    L2 Hits: 350
    Total Hit Rate: 80.0%

🚀 Batch Processing:
  Static Batching Speedup: 2.3x
  Adaptive Batching Speedup: 2.8x
  Deduplication Speedup: 3.1x
  Optimal Batch Size: 24

⚡ Integrated Optimization:
  Cache Hit Rate: 42.5%
  Avg Batch Size: 16.2
  Throughput: 25.50 items/sec

🎯 Phase 3 Target Status:
  ✓ ACHIEVED: ~35.5% reduction (target: 30%)
======================================================================
```

## 效能優化最佳實踐

### 1. 快取策略

**DO**:
- 對確定性 LLM 輸出啟用持久化快取
- 使用多層快取平衡速度和容量
- 定期監控快取命中率
- 為不同任務使用不同的快取實例

**DON'T**:
- 不要快取非確定性輸出（temperature > 0.5）
- 不要設置過小的快取大小
- 不要忽略快取清理和維護

### 2. 批次處理策略

**DO**:
- 啟用自適應批次大小
- 根據模型性能調整批次大小
- 使用去重處理器處理重複數據
- 監控批次處理統計

**DON'T**:
- 不要設置過大的批次大小（可能導致 OOM）
- 不要設置過長的等待時間
- 不要在低並發場景使用批次處理

### 3. 效能監控

**DO**:
- 始終啟用效能監控
- 定期導出和分析指標
- 比較優化前後的性能
- 根據指標調整配置

**DON'T**:
- 不要忽略內存使用情況
- 不要只關注速度而忽略準確性
- 不要在生產環境禁用監控

## 故障排除

### 快取未生效

**症狀**: 快取命中率為 0%

**解決方案**:
1. 檢查 `enable_persistence=True`
2. 確認快取目錄有寫權限
3. 檢查 TTL 設置是否過短
4. 驗證快取鍵是否一致（包括 context）

### 批次處理慢

**症狀**: 批次處理比單個處理慢

**解決方案**:
1. 減小批次大小
2. 減少等待時間
3. 檢查是否有 I/O 瓶頸
4. 啟用自適應批次大小

### 內存使用過高

**症狀**: 進程內存持續增長

**解決方案**:
1. 減小 L1 快取大小
2. 減小批次大小
3. 啟用快取淘汰
4. 定期清理快取

## 下一步

- 查看 [integration_plan.md](../.specify/specs/integration_plan.md) 了解整體架構
- 運行 [benchmark_phase3.py](../graphrag_local/tests/benchmark_phase3.py) 測試性能
- 閱讀 API 文檔了解詳細參數

## 支援

如有問題或建議，請提交 issue 或參考:
- [GraphRAG 官方文檔](https://github.com/microsoft/graphrag)
- [LMStudio 文檔](https://lmstudio.ai/docs)
