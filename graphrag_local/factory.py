"""
LMStudio LLM Factory - Simplified Version.

This module provides factory functions to create LMStudio-based LLM and embedding
instances that are compatible with GraphRAG's configuration system.
"""

import logging
from typing import Any

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    EmbeddingInput,
    EmbeddingOutput,
    LLMCache,
)

from .adapters.lmstudio_chat_llm import (
    LMStudioChatLLM,
    LMStudioConfiguration,
)
from .adapters.lmstudio_embeddings_llm import (
    LMStudioEmbeddingsLLM,
    LMStudioEmbeddingConfiguration,
)

log = logging.getLogger(__name__)


def create_lmstudio_chat_llm(
    config: dict[str, Any],
    cache: Any = None,
    limiter: Any = None,
) -> Any:  # Simplified return type
    """Create a LMStudio-based chat LLM."""
    llm_config = LMStudioConfiguration(config)
    result = LMStudioChatLLM(llm_config)
    
    # Apply wrappers if provided (simplified)
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio chat LLM")
        from graphrag.llm.base import RateLimitingLLM
        result = RateLimitingLLM(result, limiter)  # type: ignore
    
    if cache is not None:
        log.info("Applying caching to LMStudio chat LLM")
        from graphrag.llm.base import CachingLLM
        result = CachingLLM(result, cache)  # type: ignore
    
    return result


def create_lmstudio_embedding_llm(
    config: dict[str, Any],
    cache: Any = None,
    limiter: Any = None,
) -> Any:  # Simplified return type
    """Create a LMStudio-based embedding LLM."""
    embed_config = LMStudioEmbeddingConfiguration(config)
    result = LMStudioEmbeddingsLLM(embed_config)
    
    # Apply wrappers if provided (simplified)
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio embedding LLM")
        from graphrag.llm.base import RateLimitingLLM
        result = RateLimitingLLM(result, limiter)  # type: ignore
    
    if cache is not None:
        log.info("Applying caching to LMStudio embedding LLM")
        from graphrag.llm.base import CachingLLM
        result = CachingLLM(result, cache)  # type: ignore
    
    return result
