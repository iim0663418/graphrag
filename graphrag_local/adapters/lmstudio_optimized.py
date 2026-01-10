"""
Optimized LMstudio Adapters with Batch Processing and Caching.

This module provides Phase 3 optimized adapters that integrate intelligent
caching and batch processing to significantly reduce LLM API calls.

Phase 3: Performance Optimization
Target: 30%+ reduction in LLM calls through batching and caching
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

try:
    import lmstudio as lms  # type: ignore[import-untyped]
    LMSTUDIO_AVAILABLE = True
except ImportError:
    lms = None  # type: ignore
    LMSTUDIO_AVAILABLE = False

from .base import BaseLLMAdapter, BaseEmbeddingAdapter
from ..optimization.cache_manager import HashBasedCache, MultiLevelCache
from ..optimization.batch_processor import (
    BatchConfig,
    BatchProcessor,
    AdaptiveBatchProcessor,
    DedupBatchProcessor,
)

log = logging.getLogger(__name__)


class OptimizedLMStudioChatAdapter(BaseLLMAdapter):
    """
    Optimized LMstudio chat adapter with caching and batch processing.

    Features:
    - Multi-level caching (L1 memory + L2 disk)
    - Intelligent batch processing
    - Adaptive batch sizing based on performance
    - Deduplication within batches
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        enable_batching: bool = True,
        cache_dir: str = ".cache/graphrag_local/llm",
    ):
        """
        Initialize optimized LMstudio chat adapter.

        Args:
            model_name: Name/identifier of the model in LMstudio
            config: Optional configuration
            enable_cache: Enable caching layer
            enable_batching: Enable batch processing
            cache_dir: Directory for cache storage
        """
        super().__init__(model_name, config)

        if not LMSTUDIO_AVAILABLE:
            raise ImportError(
                "lmstudio SDK is not installed. "
                "Please install it with: pip install lmstudio"
            )

        # Model configuration
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.top_p = self.config.get("top_p", 1.0)

        # Initialize model
        try:
            self.model = lms.llm(model_name)
            log.info(f"✓ Loaded optimized LMstudio model: {model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {e}")

        # Initialize cache
        self.enable_cache = enable_cache
        if enable_cache:
            self.cache = MultiLevelCache(
                cache_dir=cache_dir,
                l1_max_entries=500,
                l2_max_size_mb=300,
                ttl_seconds=None,  # No expiration for deterministic LLM outputs
            )
            log.info("✓ Enabled multi-level caching")
        else:
            self.cache = None

        # Initialize batch processor
        self.enable_batching = enable_batching
        if enable_batching:
            batch_config = BatchConfig(
                min_batch_size=1,
                max_batch_size=self.config.get("batch_size", 16),
                max_wait_time_ms=self.config.get("batch_wait_ms", 100.0),
                adaptive_sizing=True,
                enable_cache_dedup=True,
            )
            self.batch_processor = AdaptiveBatchProcessor(
                config=batch_config,
                cache=self.cache,
            )
            log.info("✓ Enabled adaptive batch processing")
        else:
            self.batch_processor = None

        # Deduplication processor
        self.dedup_processor = DedupBatchProcessor()

    def _messages_to_prompt_hash(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert messages to a hashable string representation.

        Args:
            messages: List of message dicts

        Returns:
            String representation for caching
        """
        import json
        return json.dumps(messages, sort_keys=True)

    def _convert_messages_to_chat(self, messages: List[Dict[str, str]]) -> Any:
        """Convert OpenAI-style messages to LMstudio Chat object."""
        chat = lms.Chat()

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                try:
                    chat.add_system_message(content)
                except AttributeError:
                    chat.add_user_message(f"[SYSTEM]: {content}")
            elif role == "user":
                chat.add_user_message(content)
            elif role == "assistant":
                chat.add_assistant_message(content)
            else:
                chat.add_user_message(content)

        return chat

    async def acreate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Asynchronously generate response with caching and batching.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        # Convert messages to hashable format
        prompt_key = self._messages_to_prompt_hash(messages)

        # Prepare cache context
        cache_context = {
            "temperature": kwargs.get("temperature", self.temperature),
            "model": self.model_name,
        }

        # Check cache first
        if self.cache:
            cached = self.cache.get(prompt_key, cache_context)
            if cached is not None:
                log.debug("Cache hit for LLM request")
                return cached

        # Process through batch processor if enabled
        if self.batch_processor:
            # Define batch processing function
            def batch_fn(prompts: List[str]) -> List[str]:
                results = []
                for prompt in prompts:
                    # Deserialize messages
                    import json
                    msgs = json.loads(prompt)
                    result = self.create(msgs, **kwargs)
                    results.append(result)
                return results

            result = await self.batch_processor.process(
                prompt_key,
                batch_fn,
                cache_context if self.cache else None,
            )
            return result
        else:
            # Direct processing
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.create, messages, **kwargs)

            # Cache result
            if self.cache:
                cache_context = {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "model": self.model_name,
                }
                self.cache.set(prompt_key, result, cache_context)

            return result

    def create(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Synchronously generate response.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        try:
            # Convert messages to Chat format
            chat = self._convert_messages_to_chat(messages)

            # Merge configurations
            generation_config = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "top_p": kwargs.get("top_p", self.top_p),
            }

            # Call the model
            result = self.model.respond(chat, config=generation_config)

            # Extract text from result
            if hasattr(result, "content"):
                return result.content
            elif isinstance(result, str):
                return result
            else:
                return str(result)

        except Exception as e:
            raise Exception(f"LMstudio generation failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "model": self.model_name,
            "cache_enabled": self.enable_cache,
            "batching_enabled": self.enable_batching,
        }

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        if self.batch_processor:
            stats["batching"] = self.batch_processor.get_stats()

        stats["deduplication"] = self.dedup_processor.get_stats()

        return stats

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including optimization stats."""
        info = super().get_model_info()
        info.update({
            "sdk": "lmstudio",
            "optimized": True,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stats": self.get_stats(),
        })
        return info


class OptimizedLMStudioEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    Optimized LMstudio embedding adapter with caching and batching.

    Features:
    - Multi-level caching for embeddings
    - Efficient batch processing with deduplication
    - Adaptive batch sizing
    - Token-aware batching
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        enable_batching: bool = True,
        cache_dir: str = ".cache/graphrag_local/embeddings",
    ):
        """
        Initialize optimized embedding adapter.

        Args:
            model_name: Name/identifier of the embedding model
            config: Optional configuration
            enable_cache: Enable caching
            enable_batching: Enable batch processing
            cache_dir: Directory for cache storage
        """
        super().__init__(model_name, config)

        if not LMSTUDIO_AVAILABLE:
            raise ImportError(
                "lmstudio SDK is not installed. "
                "Please install it with: pip install lmstudio"
            )

        # Configuration
        self.batch_size = self.config.get("batch_size", 32)
        self.normalize = self.config.get("normalize", True)
        self._embedding_dimension = None

        # Initialize model
        try:
            self.model = lms.embedding_model(model_name)
            log.info(f"✓ Loaded optimized LMstudio embedding model: {model_name}")
            self._detect_embedding_dimension()
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model {model_name}: {e}")

        # Initialize cache
        self.enable_cache = enable_cache
        if enable_cache:
            self.cache = MultiLevelCache(
                cache_dir=cache_dir,
                l1_max_entries=1000,
                l2_max_size_mb=500,
                ttl_seconds=None,
            )
            log.info("✓ Enabled multi-level caching for embeddings")
        else:
            self.cache = None

        # Deduplication processor
        self.dedup_processor = DedupBatchProcessor()

        # Statistics
        self.stats = {
            "total_embeds": 0,
            "cache_hits": 0,
            "batch_calls": 0,
        }

    def _detect_embedding_dimension(self) -> None:
        """Detect embedding dimension."""
        try:
            test_embedding = self.model.embed("test")
            if isinstance(test_embedding, list):
                self._embedding_dimension = len(test_embedding)
                log.info(f"  Embedding dimension: {self._embedding_dimension}")
        except Exception:
            pass

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length."""
        import math
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            return [x / magnitude for x in vector]
        return vector

    async def aembed(self, text: str, **kwargs) -> List[float]:
        """
        Asynchronously generate embedding with caching.

        Args:
            text: Input text to embed
            **kwargs: Additional parameters

        Returns:
            Embedding vector
        """
        self.stats["total_embeds"] += 1

        # Check cache
        if self.cache:
            cached = self.cache.get(text)
            if cached is not None:
                self.stats["cache_hits"] += 1
                log.debug("Cache hit for embedding")
                return cached

        # Generate embedding
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self.embed, text, **kwargs)

        # Cache result
        if self.cache:
            self.cache.set(text, embedding)

        return embedding

    def embed(self, text: str, **kwargs) -> List[float]:
        """
        Synchronously generate embedding.

        Args:
            text: Input text to embed
            **kwargs: Additional parameters

        Returns:
            Embedding vector
        """
        try:
            embedding = self.model.embed(text)

            if not isinstance(embedding, list):
                embedding = list(embedding)

            if self.normalize and kwargs.get("normalize", True):
                embedding = self._normalize_vector(embedding)

            return embedding

        except Exception as e:
            raise Exception(f"LMstudio embedding generation failed: {e}")

    async def aembed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Asynchronously generate embeddings for batch with optimization.

        Args:
            texts: List of input texts
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        self.stats["total_embeds"] += len(texts)
        self.stats["batch_calls"] += 1

        # Process with deduplication
        def processor_fn(unique_texts: List[str]) -> List[List[float]]:
            # Check cache for each text
            results = []
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(unique_texts):
                if self.cache:
                    cached = self.cache.get(text)
                    if cached is not None:
                        results.append((i, cached))
                        self.stats["cache_hits"] += 1
                        continue

                uncached_texts.append(text)
                uncached_indices.append(i)

            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.embed_batch(uncached_texts, **kwargs)

                # Cache new embeddings
                for text, embedding in zip(uncached_texts, new_embeddings):
                    if self.cache:
                        self.cache.set(text, embedding)

                # Add to results
                for idx, embedding in zip(uncached_indices, new_embeddings):
                    results.append((idx, embedding))

            # Sort by original index and extract embeddings
            results.sort(key=lambda x: x[0])
            return [emb for _, emb in results]

        # Apply deduplication
        embeddings = await self.dedup_processor.process_batch(
            texts,
            processor_fn,
        )

        return embeddings

    def embed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Synchronously generate embeddings for batch.

        Args:
            texts: List of input texts
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        try:
            # Check if SDK supports native batch embedding
            if hasattr(self.model, "embed_batch"):
                # Process in batches
                batch_size = kwargs.get("batch_size", self.batch_size)
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_embeddings = self.model.embed_batch(batch)
                    embeddings.extend(batch_embeddings)
            else:
                # Fallback: process one by one
                for text in texts:
                    embedding = self.embed(text, **kwargs)
                    embeddings.append(embedding)

            return embeddings

        except Exception as e:
            raise Exception(f"LMstudio batch embedding failed: {e}")

    def get_embedding_dimension(self) -> Optional[int]:
        """Get embedding dimension."""
        return self._embedding_dimension

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            **self.stats,
            "model": self.model_name,
            "cache_enabled": self.enable_cache,
        }

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        stats["deduplication"] = self.dedup_processor.get_stats()

        # Calculate cache hit rate
        total = self.stats["total_embeds"]
        if total > 0:
            stats["cache_hit_rate"] = (self.stats["cache_hits"] / total * 100)
        else:
            stats["cache_hit_rate"] = 0.0

        return stats

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including optimization stats."""
        info = super().get_model_info()
        info.update({
            "sdk": "lmstudio",
            "optimized": True,
            "batch_size": self.batch_size,
            "normalize": self.normalize,
            "stats": self.get_stats(),
        })
        return info
