"""
Adapters for integrating LMstudio SDK with GraphRAG interfaces.

Includes both basic adapters (Phase 1-2) and optimized adapters (Phase 3)
with intelligent caching and batch processing.
"""

from .base import BaseLLMAdapter, BaseEmbeddingAdapter
from .lmstudio_llm import LMStudioChatAdapter, LMStudioCompletionAdapter
from .lmstudio_embedding import LMStudioEmbeddingAdapter, LMStudioBatchEmbeddingAdapter

# Phase 3: Optimized adapters with caching and batching
from .lmstudio_optimized import (
    OptimizedLMStudioChatAdapter,
    OptimizedLMStudioEmbeddingAdapter,
)

__all__ = [
    # Base adapters
    "BaseLLMAdapter",
    "BaseEmbeddingAdapter",
    # Phase 1-2 adapters
    "LMStudioChatAdapter",
    "LMStudioCompletionAdapter",
    "LMStudioEmbeddingAdapter",
    "LMStudioBatchEmbeddingAdapter",
    # Phase 3 optimized adapters
    "OptimizedLMStudioChatAdapter",
    "OptimizedLMStudioEmbeddingAdapter",
]
