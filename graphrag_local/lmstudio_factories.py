"""
Factory functions for creating LMStudio LLMs compatible with GraphRAG.

This module provides factory functions that create LMStudio LLM instances
with the same decorator pattern used by OpenAI (caching, rate limiting, etc.).
"""

import asyncio
import logging

from graphrag.llm.base import CachingLLM, RateLimitingLLM
from graphrag.llm.limiting import LLMLimiter
from graphrag.llm.types import (
    LLM,
    CompletionLLM,
    EmbeddingLLM,
    ErrorHandlerFn,
    LLMCache,
    LLMInvocationFn,
    OnCacheActionFn,
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


# LMStudio doesn't have the same error types as OpenAI, but we can define some
LMSTUDIO_RETRYABLE_ERRORS = [
    "Connection error",
    "Timeout",
    "Model not loaded",
]

LMSTUDIO_RATE_LIMIT_ERRORS = [
    "Rate limit exceeded",
]


def create_lmstudio_chat_llm(
    config: dict,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> CompletionLLM:
    """Create a LMStudio chat LLM with GraphRAG decorators.

    Args:
        config: Configuration dictionary for LMStudio
        cache: Optional LLM cache
        limiter: Optional rate limiter
        semaphore: Optional semaphore for concurrency control
        on_invoke: Optional callback for invocations
        on_error: Optional error handler
        on_cache_hit: Optional cache hit callback
        on_cache_miss: Optional cache miss callback

    Returns:
        Configured LMStudio chat LLM with decorators applied
    """
    operation = "chat"
    llm_config = LMStudioConfiguration(config)
    result = LMStudioChatLLM(llm_config)
    result.on_error(on_error)

    # Apply rate limiting if provided
    if limiter is not None or semaphore is not None:
        result = _rate_limited(
            result, llm_config, operation, limiter, semaphore, on_invoke
        )

    # Apply caching if provided
    if cache is not None:
        result = _cached(
            result, llm_config, operation, cache, on_cache_hit, on_cache_miss
        )

    return result


def create_lmstudio_embedding_llm(
    config: dict,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> EmbeddingLLM:
    """Create a LMStudio embedding LLM with GraphRAG decorators.

    Args:
        config: Configuration dictionary for LMStudio
        cache: Optional LLM cache
        limiter: Optional rate limiter
        semaphore: Optional semaphore for concurrency control
        on_invoke: Optional callback for invocations
        on_error: Optional error handler
        on_cache_hit: Optional cache hit callback
        on_cache_miss: Optional cache miss callback

    Returns:
        Configured LMStudio embedding LLM with decorators applied
    """
    operation = "embedding"
    embed_config = LMStudioEmbeddingConfiguration(config)
    result = LMStudioEmbeddingsLLM(embed_config)
    result.on_error(on_error)

    # Apply rate limiting if provided
    if limiter is not None or semaphore is not None:
        result = _rate_limited(
            result, embed_config, operation, limiter, semaphore, on_invoke
        )

    # Apply caching if provided
    if cache is not None:
        result = _cached(
            result, embed_config, operation, cache, on_cache_hit, on_cache_miss
        )

    return result


def _rate_limited(
    delegate: LLM,
    config: LMStudioConfiguration | LMStudioEmbeddingConfiguration,
    operation: str,
    limiter: LLMLimiter | None,
    semaphore: asyncio.Semaphore | None,
    on_invoke: LLMInvocationFn | None,
):
    """Apply rate limiting to a LMStudio LLM.

    Args:
        delegate: The base LLM to wrap
        config: LMStudio configuration
        operation: Operation name (e.g., "chat", "embedding")
        limiter: Optional rate limiter
        semaphore: Optional semaphore
        on_invoke: Optional invocation callback

    Returns:
        Rate-limited LLM
    """
    # For LMStudio, we use a simpler rate limiting without token counting
    # since local models don't have the same rate limit concerns
    result = RateLimitingLLM(
        delegate,
        config,
        operation,
        LMSTUDIO_RETRYABLE_ERRORS,
        LMSTUDIO_RATE_LIMIT_ERRORS,
        limiter,
        semaphore,
        None,  # No token counter for local models
        None,  # No sleep time extractor
    )
    result.on_invoke(on_invoke)
    return result


def _cached(
    delegate: LLM,
    config: LMStudioConfiguration | LMStudioEmbeddingConfiguration,
    operation: str,
    cache: LLMCache,
    on_cache_hit: OnCacheActionFn | None,
    on_cache_miss: OnCacheActionFn | None,
):
    """Apply caching to a LMStudio LLM.

    Args:
        delegate: The base LLM to wrap
        config: LMStudio configuration
        operation: Operation name
        cache: LLM cache instance
        on_cache_hit: Optional cache hit callback
        on_cache_miss: Optional cache miss callback

    Returns:
        Cached LLM
    """
    # Create cache args based on config
    cache_args = {
        "model": config.model,
    }

    # Add temperature and other params if they exist
    if hasattr(config, "temperature") and config.temperature is not None:
        cache_args["temperature"] = config.temperature
    if hasattr(config, "max_tokens") and config.max_tokens is not None:
        cache_args["max_tokens"] = config.max_tokens
    if hasattr(config, "top_p") and config.top_p is not None:
        cache_args["top_p"] = config.top_p

    result = CachingLLM(delegate, cache_args, operation, cache)
    result.on_cache_hit(on_cache_hit)
    result.on_cache_miss(on_cache_miss)
    return result
