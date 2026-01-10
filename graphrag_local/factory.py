"""
LMStudio LLM Factory - Phase 2 Core Integration.

This module provides factory functions to create LMStudio-based LLM and embedding
instances that are compatible with GraphRAG's configuration system.
"""

import logging
from typing import Any

from graphrag.llm.base import BaseLLM, CachingLLM, RateLimitingLLM
from graphrag.llm.limiting import LLMLimiter
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
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
) -> BaseLLM[CompletionInput, CompletionOutput]:
    """Create a LMStudio-based chat LLM with optional caching and rate limiting."""
    from graphrag.llm.types import LLMConfig
    
    llm_config = LMStudioConfiguration(config)
    result: BaseLLM[CompletionInput, CompletionOutput] = LMStudioChatLLM(llm_config)
    
    # Apply rate limiting if provided
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio chat LLM")
        # Create proper LLMConfig for rate limiting
        rate_config = LLMConfig(
            max_retries=3,
            max_retry_wait=10.0,
            sleep_on_rate_limit_recommendation=True,
        )
        result = RateLimitingLLM(
            delegate=result,
            config=rate_config,
            operation="chat_completion",
            retryable_errors=[],
            rate_limit_errors=[],
        )
    
    # Apply caching if provided
    if cache is not None:
        log.info("Applying caching to LMStudio chat LLM")
        result = CachingLLM(
            delegate=result,
            llm_parameters={},
            operation="chat_completion",
            cache=cache,
        )
    
    return result


def create_lmstudio_embedding_llm(
    config: dict[str, Any],
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
) -> BaseLLM[EmbeddingInput, EmbeddingOutput]:
    """Create a LMStudio-based embedding LLM with optional caching and rate limiting."""
    from graphrag.llm.types import LLMConfig
    
    embed_config = LMStudioEmbeddingConfiguration(config)
    result: BaseLLM[EmbeddingInput, EmbeddingOutput] = LMStudioEmbeddingsLLM(embed_config)
    
    # Apply rate limiting if provided
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio embedding LLM")
        # Create proper LLMConfig for rate limiting
        rate_config = LLMConfig(
            max_retries=3,
            max_retry_wait=10.0,
            sleep_on_rate_limit_recommendation=True,
        )
        result = RateLimitingLLM(
            delegate=result,
            config=rate_config,
            operation="embedding",
            retryable_errors=[],
            rate_limit_errors=[],
        )
    
    # Apply caching if provided
    if cache is not None:
        log.info("Applying caching to LMStudio embedding LLM")
        result = CachingLLM(
            delegate=result,
            llm_parameters={},
            operation="embedding",
            cache=cache,
        )
    
    return result
