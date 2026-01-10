"""
LMStudio LLM Factory - Phase 2 Core Integration.

This module provides factory functions to create LMStudio-based LLM and embedding
instances that are compatible with GraphRAG's configuration system.

This is the main entry point for integrating LMStudio with GraphRAG.
"""

import logging
from typing import Any

from graphrag.llm.base import BaseLLM, CachingLLM, RateLimitingLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    EmbeddingInput,
    EmbeddingOutput,
    LLMCache,
    LLMLimiter,
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
    """Create a LMStudio chat LLM with optional caching and rate limiting.

    This factory function creates a fully-configured LMStudio chat LLM that is
    compatible with GraphRAG's pipeline. It applies the same decorator pattern
    used by OpenAI LLMs (caching, rate limiting).

    Args:
        config: Configuration dictionary containing:
            - model: Model identifier (e.g., "qwen/qwen3-4b-2507")
            - temperature: Sampling temperature (optional)
            - max_tokens: Maximum tokens to generate (optional)
            - top_p: Nucleus sampling parameter (optional)
            - model_supports_json: Whether model supports native JSON mode (optional)
        cache: Optional LLM cache for response caching
        limiter: Optional rate limiter for request throttling

    Returns:
        Configured LMStudio chat LLM, potentially wrapped with caching and rate limiting

    Example:
        >>> config = {
        ...     "model": "qwen/qwen3-4b-2507",
        ...     "temperature": 0.0,
        ...     "max_tokens": 4000,
        ...     "model_supports_json": True
        ... }
        >>> llm = create_lmstudio_chat_llm(config)
        >>> result = await llm("Hello!", name="greeting")
    """
    # Create configuration
    llm_config = LMStudioConfiguration(config)

    # Create base LLM
    result: BaseLLM[CompletionInput, CompletionOutput] = LMStudioChatLLM(llm_config)

    # Apply rate limiting if provided
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio chat LLM")
        result = RateLimitingLLM(result, limiter)

    # Apply caching if provided
    if cache is not None:
        log.info("Applying caching to LMStudio chat LLM")
        result = CachingLLM(result, cache)

    return result


def create_lmstudio_embedding_llm(
    config: dict[str, Any],
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
) -> BaseLLM[EmbeddingInput, EmbeddingOutput]:
    """Create a LMStudio embedding LLM with optional caching and rate limiting.

    This factory function creates a fully-configured LMStudio embedding LLM that is
    compatible with GraphRAG's pipeline.

    Args:
        config: Configuration dictionary containing:
            - model: Model identifier (e.g., "nomic-embed-text-v1.5")
        cache: Optional LLM cache for embedding caching
        limiter: Optional rate limiter for request throttling

    Returns:
        Configured LMStudio embedding LLM, potentially wrapped with caching and rate limiting

    Example:
        >>> config = {"model": "nomic-embed-text-v1.5"}
        >>> embedder = create_lmstudio_embedding_llm(config)
        >>> result = await embedder("Hello, world!", name="embed_test")
        >>> embeddings = result.output  # [[float, ...]]
    """
    # Create configuration
    embed_config = LMStudioEmbeddingConfiguration(config)

    # Create base embedding LLM
    result: BaseLLM[EmbeddingInput, EmbeddingOutput] = LMStudioEmbeddingsLLM(embed_config)

    # Apply rate limiting if provided
    if limiter is not None:
        log.info("Applying rate limiting to LMStudio embedding LLM")
        result = RateLimitingLLM(result, limiter)

    # Apply caching if provided
    if cache is not None:
        log.info("Applying caching to LMStudio embedding LLM")
        result = CachingLLM(result, cache)

    return result


def create_lmstudio_llm_from_graphrag_config(
    graphrag_config: Any,  # GraphRagConfig
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
) -> BaseLLM[CompletionInput, CompletionOutput]:
    """Create LMStudio chat LLM from GraphRAG configuration object.

    This is a convenience function that extracts LLM configuration from a
    GraphRAG config object and creates the appropriate LMStudio LLM.

    Args:
        graphrag_config: GraphRAG configuration object
        cache: Optional LLM cache
        limiter: Optional rate limiter

    Returns:
        Configured LMStudio chat LLM

    Example:
        >>> from graphrag.config import create_graphrag_config
        >>> config = create_graphrag_config(values={"llm": {"type": "lmstudio_chat", "model": "qwen/qwen3-4b-2507"}})
        >>> llm = create_lmstudio_llm_from_graphrag_config(config)
    """
    llm_params = graphrag_config.llm

    config = {
        "model": llm_params.model,
        "temperature": llm_params.temperature,
        "max_tokens": llm_params.max_tokens,
        "top_p": llm_params.top_p,
        "model_supports_json": getattr(llm_params, "model_supports_json", False),
    }

    return create_lmstudio_chat_llm(config, cache=cache, limiter=limiter)


def create_lmstudio_embedding_from_graphrag_config(
    graphrag_config: Any,  # GraphRagConfig
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
) -> BaseLLM[EmbeddingInput, EmbeddingOutput]:
    """Create LMStudio embedding LLM from GraphRAG configuration object.

    This is a convenience function that extracts embedding configuration from a
    GraphRAG config object and creates the appropriate LMStudio embedding LLM.

    Args:
        graphrag_config: GraphRAG configuration object
        cache: Optional LLM cache
        limiter: Optional rate limiter

    Returns:
        Configured LMStudio embedding LLM

    Example:
        >>> from graphrag.config import create_graphrag_config
        >>> config = create_graphrag_config(values={"embeddings": {"llm": {"type": "lmstudio_embedding", "model": "nomic-embed-text-v1.5"}}})
        >>> embedder = create_lmstudio_embedding_from_graphrag_config(config)
    """
    embed_params = graphrag_config.embeddings.llm

    config = {
        "model": embed_params.model,
    }

    return create_lmstudio_embedding_llm(config, cache=cache, limiter=limiter)
