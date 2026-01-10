# Phase 3: 效能優化模組

## 總覽

Phase 3 優化模組提供智能快取、批次處理和效能監控功能，旨在將 GraphRAG 索引過程中的 LLM 調用次數減少 30% 以上，並大幅提升處理效率。

## 模組結構

```
optimization/
├── __init__.py                  # 模組導出
├── cache_manager.py            # 智能快取系統
├── batch_processor.py          # 批次處理邏輯
├── performance_monitor.py      # 效能監控工具
└── README.md                   # 本文檔
```

## 核心組件

### 1. cache_manager.py - 智能快取系統

提供三種快取實現：

#### HashBasedCache
- **用途**: 基於內容雜湊的通用快取
- **特點**: SQLite 持久化、TTL 支持、自動淘汰
- **適用**: 通用 LLM 結果快取

```python
cache = HashBasedCache(
    cache_dir=".cache/graphrag",
    ttl_seconds=None,      # 永不過期
    max_size_mb=500,       # 最大 500MB
)
```

#### MultiLevelCache
- **用途**: 雙層快取（記憶體 + 磁碟）
- **特點**: L1 LRU 記憶體快取 + L2 持久化快取
- **適用**: 高頻訪問場景

```python
cache = MultiLevelCache(
    l1_max_entries=1000,   # L1 記憶體容量
    l2_max_size_mb=500,    # L2 磁碟容量
)
```

#### EntityRelationshipCache
- **用途**: 實體關係提取專用快取
- **特點**: 針對 GraphRAG 實體提取優化
- **適用**: 實體和關係提取任務

```python
er_cache = EntityRelationshipCache(
    cache_dir=".cache/entities"
)
entities = er_cache.get_entities(text, prompt)
```

### 2. batch_processor.py - 批次處理邏輯

提供多種批次處理策略：

#### BatchProcessor
- **基礎批次處理器**
- 累積請求並批次處理
- 可配置批次大小和等待時間

#### AdaptiveBatchProcessor
- **自適應批次處理器**
- 基於性能動態調整批次大小
- 自動優化吞吐量

#### DedupBatchProcessor
- **去重批次處理器**
- 識別並去除批次內重複項
- 每個唯一輸入只處理一次

#### TextChunkBatcher
- **文本分塊批次處理器**
- Token 感知的批次創建
- 遵守模型 token 限制

### 3. performance_monitor.py - 效能監控工具

#### PerformanceMonitor
- **全面效能追蹤**
- 記錄時間、調用次數、快取命中率
- 計算效率指標
- 導出詳細報告

```python
monitor = PerformanceMonitor()

with monitor.track("entity_extraction"):
    extract_entities(text)

monitor.record_llm_call(duration_s=0.5, cached=False)
monitor.print_summary()
```

#### ComparisonAnalyzer
- **性能對比分析**
- 比較優化前後的指標
- 驗證優化效果

## 性能目標

| 指標 | 目標 | 實現方式 |
|------|------|----------|
| LLM 調用減少 | 30%+ | 快取 + 去重 |
| 索引速度提升 | 20%+ | 批次處理 + 並行 |
| 快取命中率 | 40%+ | 智能雜湊 + 多層快取 |
| 記憶體使用 | 穩定 | LRU 淘汰 + 大小限制 |

## 使用範例

### 基本使用

```python
from graphrag_local.optimization import (
    MultiLevelCache,
    AdaptiveBatchProcessor,
    PerformanceMonitor,
)

# 初始化
cache = MultiLevelCache()
processor = AdaptiveBatchProcessor(cache=cache)
monitor = PerformanceMonitor()

# 處理
async def process_texts(texts):
    with monitor.track("processing"):
        tasks = [
            processor.process(text, llm_batch_fn)
            for text in texts
        ]
        results = await asyncio.gather(*tasks)
        await processor.flush(llm_batch_fn)

    return results

# 查看統計
print(cache.get_stats())
print(processor.get_stats())
monitor.print_summary()
```

### 整合到適配器

```python
from graphrag_local.adapters import OptimizedLMStudioChatAdapter

adapter = OptimizedLMStudioChatAdapter(
    model_name="qwen/qwen3-4b",
    enable_cache=True,
    enable_batching=True,
)

# 使用與標準適配器相同
response = await adapter.acreate(messages)

# 查看優化效果
stats = adapter.get_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']:.1f}%")
```

## 配置指南

### 快取配置

```yaml
cache:
  type: multilevel
  l1_max_entries: 1000
  l2_max_size_mb: 500
  ttl_seconds: null  # 永不過期
  cache_dir: .cache/graphrag
```

**調優建議**:
- 開發環境: 小快取 (100MB)
- 生產環境: 大快取 (1GB+)
- 確定性輸出: 無 TTL
- 非確定性輸出: 設置 TTL

### 批次配置

```yaml
batching:
  min_batch_size: 1
  max_batch_size: 32
  max_wait_time_ms: 100.0
  adaptive_sizing: true
  enable_cache_dedup: true
```

**調優建議**:
- 高並發: 大批次 (32+)
- 低並發: 小批次 (8-16)
- 快速響應: 短等待時間 (50ms)
- 高吞吐: 長等待時間 (100ms+)

## 基準測試

運行完整基準測試:

```bash
python graphrag_local/tests/benchmark_phase3.py
```

預期結果:
```
📊 Cache Performance:
  Hit Rate: 80%+
  Read Time: < 1ms per item

🚀 Batch Processing:
  Adaptive Batching Speedup: 2.5x+
  Deduplication Savings: 20%+

⚡ Integrated Optimization:
  LLM Call Reduction: 30%+
  Throughput Improvement: 25%+
```

## 故障排除

### 快取未生效
- 檢查 `enable_persistence=True`
- 確認目錄寫權限
- 驗證快取鍵一致性

### 批次處理慢
- 減小批次大小
- 啟用自適應大小
- 檢查 I/O 瓶頸

### 內存使用高
- 減小 L1 快取大小
- 啟用快取淘汰
- 定期清理快取

## API 參考

詳細 API 文檔請參考各模組的 docstring:

```python
help(HashBasedCache)
help(AdaptiveBatchProcessor)
help(PerformanceMonitor)
```

## 下一步

1. 閱讀 [phase3_optimization_guide.md](../../docs/phase3_optimization_guide.md) 獲取完整指南
2. 運行基準測試驗證性能
3. 整合到現有 GraphRAG 工作流程
4. 監控和調優配置

## 貢獻

歡迎提交 issue 和 PR 改進優化模組！

## 授權

與 GraphRAG 主項目相同的授權條款。
