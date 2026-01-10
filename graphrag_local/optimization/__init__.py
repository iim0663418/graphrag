"""
GraphRAG Local Optimization Module.

Phase 3: Performance Optimization

This module provides intelligent caching, batch processing, and performance
monitoring to significantly reduce LLM API calls and improve indexing speed.

Key Features:
- Hash-based caching with TTL support
- Multi-level cache (L1 memory + L2 disk)
- Intelligent batch processing with adaptive sizing
- Deduplication within batches
- Comprehensive performance monitoring

Target: 30%+ reduction in LLM calls and improved throughput
"""

from .cache_manager import (
    HashBasedCache,
    EntityRelationshipCache,
    MultiLevelCache,
    CacheStats,
)

from .batch_processor import (
    BatchConfig,
    BatchProcessor,
    AdaptiveBatchProcessor,
    TextChunkBatcher,
    DedupBatchProcessor,
    BatchStats,
)

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    ComparisonAnalyzer,
)

__all__ = [
    # Cache classes
    "HashBasedCache",
    "EntityRelationshipCache",
    "MultiLevelCache",
    "CacheStats",
    # Batch processing classes
    "BatchConfig",
    "BatchProcessor",
    "AdaptiveBatchProcessor",
    "TextChunkBatcher",
    "DedupBatchProcessor",
    "BatchStats",
    # Performance monitoring
    "PerformanceMonitor",
    "PerformanceMetrics",
    "ComparisonAnalyzer",
]
