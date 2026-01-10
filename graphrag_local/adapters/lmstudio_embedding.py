"""
LMstudio Embedding Adapter for GraphRAG.

This adapter translates GraphRAG's embedding interface calls into LMstudio SDK calls,
allowing GraphRAG to use local embedding models running in LMstudio.

Phase 1: Prototype Implementation
"""

import asyncio
from typing import List, Dict, Any, Optional

try:
    import lmstudio as lms  # type: ignore[import-untyped]
    LMSTUDIO_AVAILABLE = True
except ImportError:
    lms = None  # type: ignore
    LMSTUDIO_AVAILABLE = False

from .base import BaseEmbeddingAdapter


class LMStudioEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    Adapter for LMstudio embedding models.

    This adapter allows GraphRAG to generate embeddings using local models
    running in LMstudio instead of calling external APIs.
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LMstudio embedding adapter.

        Args:
            model_name: Name/identifier of the embedding model in LMstudio
                       Examples: "nomic-embed-text-v1.5", "bge-m3", etc.
            config: Optional configuration including:
                - batch_size: int (default: 32) - for batch processing
                - normalize: bool (default: True) - normalize embeddings

        Raises:
            ImportError: If lmstudio SDK is not installed
            RuntimeError: If embedding model cannot be loaded
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

        # Initialize the embedding model
        if not LMSTUDIO_AVAILABLE or lms is None:
            raise RuntimeError("LMStudio SDK not available")
            
        try:
            self.model = lms.embedding_model(model_name)  # type: ignore
            print(f"✓ Loaded LMstudio embedding model: {model_name}")

            # Try to determine embedding dimension
            self._detect_embedding_dimension()

        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model {model_name}: {e}")

    def _detect_embedding_dimension(self) -> None:
        """
        Detect the embedding dimension by generating a test embedding.

        This is called during initialization to cache the dimension size.
        """
        try:
            test_embedding = self.model.embed("test")
            if isinstance(test_embedding, list):
                self._embedding_dimension = len(test_embedding)
                print(f"  Embedding dimension: {self._embedding_dimension}")
        except Exception:
            # If detection fails, leave as None
            pass

    async def aembed(self, text: str, **kwargs) -> List[float]:
        """
        Asynchronously generate embedding for a single text.

        Args:
            text: Input text to embed
            **kwargs: Additional parameters (currently unused)

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed, text, **kwargs)

    def embed(self, text: str, **kwargs) -> List[float]:
        """
        Synchronously generate embedding for a single text.

        Args:
            text: Input text to embed
            **kwargs: Additional parameters

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Generate embedding
            embedding = self.model.embed(text)

            # Ensure it's a list of floats
            if not isinstance(embedding, list):
                embedding = list(embedding)

            # Optional normalization
            if self.normalize and kwargs.get("normalize", True):
                embedding = self._normalize_vector(embedding)

            return embedding

        except Exception as e:
            raise Exception(f"LMstudio embedding generation failed for text: {e}")

    async def aembed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Asynchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed
            **kwargs: Additional parameters including:
                - batch_size: Override default batch size

        Returns:
            List of embedding vectors

        Raises:
            Exception: If batch embedding fails
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_batch, texts, **kwargs)

    def embed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Synchronously generate embeddings for multiple texts.

        This method processes texts in batches for efficiency.

        Args:
            texts: List of input texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors, one per input text

        Raises:
            Exception: If batch embedding fails
        """
        if not texts:
            return []

        batch_size = kwargs.get("batch_size", self.batch_size)
        embeddings = []

        try:
            # Check if SDK supports native batch embedding
            if hasattr(self.model, "embed_batch"):
                # Use native batch method if available
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

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normalize a vector to unit length.

        Args:
            vector: Input vector

        Returns:
            Normalized vector
        """
        import math

        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            return [x / magnitude for x in vector]
        return vector

    def get_embedding_dimension(self) -> Optional[int]:
        """
        Get the dimension of the embedding vectors.

        Returns:
            Integer dimension size, or None if unknown
        """
        return self._embedding_dimension

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded embedding model.

        Returns:
            Dictionary with model metadata
        """
        info = super().get_model_info()
        info.update({
            "sdk": "lmstudio",
            "batch_size": self.batch_size,
            "normalize": self.normalize,
        })
        return info


class LMStudioBatchEmbeddingAdapter(LMStudioEmbeddingAdapter):
    """
    Optimized batch embedding adapter with caching support.

    This adapter extends the base embedding adapter with additional
    optimizations for batch processing, which is critical for GraphRAG's
    indexing pipeline.
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the batch embedding adapter.

        Args:
            model_name: Name of the embedding model
            config: Configuration including batch_size and cache settings
        """
        super().__init__(model_name, config)

        # Batch optimization settings
        self.min_batch_size = self.config.get("min_batch_size", 8)
        self.max_batch_size = self.config.get("max_batch_size", 64)
        self.adaptive_batching = self.config.get("adaptive_batching", True)

        # Simple in-memory cache for embeddings
        # In production, this should use a persistent cache (see cache_manager.py)
        self.use_cache = self.config.get("use_cache", False)
        self._cache: Dict[str, List[float]] = {}

    def embed(self, text: str, **kwargs) -> List[float]:
        """
        Generate embedding with optional caching.

        Args:
            text: Input text to embed
            **kwargs: Additional parameters

        Returns:
            Embedding vector
        """
        # Check cache first
        if self.use_cache and text in self._cache:
            return self._cache[text]

        # Generate embedding
        embedding = super().embed(text, **kwargs)

        # Cache result
        if self.use_cache:
            self._cache[text] = embedding

        return embedding

    def embed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Optimized batch embedding with caching.

        Args:
            texts: List of input texts
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Split into cached and uncached
        embeddings_map: Dict[int, List[float]] = {}
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, text in enumerate(texts):
            if self.use_cache and text in self._cache:
                embeddings_map[i] = self._cache[text]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = super().embed_batch(uncached_texts, **kwargs)

            # Cache and map new embeddings
            for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                embedding = new_embeddings[i]
                embeddings_map[idx] = embedding

                if self.use_cache:
                    self._cache[text] = embedding

        # Reconstruct in original order
        return [embeddings_map[i] for i in range(len(texts))]

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._cache)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information including cache stats."""
        info = super().get_model_info()
        info.update({
            "use_cache": self.use_cache,
            "cache_size": self.get_cache_size(),
            "adaptive_batching": self.adaptive_batching,
        })
        return info
