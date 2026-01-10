"""
LMStudio Embeddings LLM Adapter - Phase 2 Core Integration.

This module provides a full GraphRAG-compatible embedding implementation using LMStudio,
replacing OpenAI embedding API calls with local model inference.
"""

import logging
from typing import Any

from typing_extensions import Unpack

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    EmbeddingInput,
    EmbeddingOutput,
    LLMInput,
)

try:
    import lmstudio as lms
    LMSTUDIO_AVAILABLE = True
except ImportError:
    LMSTUDIO_AVAILABLE = False
    lms = None

log = logging.getLogger(__name__)


class LMStudioEmbeddingConfiguration:
    """Configuration for LMStudio Embedding adapter."""

    def __init__(self, config: dict[str, Any]):
        """Initialize LMStudio Embedding configuration.

        Args:
            config: Configuration dictionary containing model settings
        """
        self.model = config.get("model", "")

        # Store any additional config parameters
        self._extra_config = {
            k: v for k, v in config.items()
            if k not in ["model"]
        }

    def get_embedding_config(self, **overrides: Any) -> dict[str, Any]:
        """Get embedding configuration with optional overrides.

        Args:
            **overrides: Optional parameter overrides

        Returns:
            Dictionary of embedding parameters
        """
        config = {**self._extra_config}
        config.update(overrides)
        return config


class LMStudioEmbeddingsLLM(BaseLLM[EmbeddingInput, EmbeddingOutput]):
    """LMStudio Embeddings LLM adapter for GraphRAG.

    This adapter implements the GraphRAG embedding interface using LMStudio's
    Python SDK, allowing GraphRAG to use locally-hosted embedding models
    instead of OpenAI embedding API.

    This is the Phase 2 implementation that fully integrates with GraphRAG's
    configuration system.

    Example:
        >>> config = {"model": "nomic-embed-text-v1.5"}
        >>> embed_config = LMStudioEmbeddingConfiguration(config)
        >>> embedder = LMStudioEmbeddingsLLM(embed_config)
        >>> result = await embedder("Hello, world!", name="test_embed")
        >>> embeddings = result.output  # List[List[float]]
    """

    _client: Any  # lms.EmbeddingModel instance
    _configuration: LMStudioEmbeddingConfiguration

    def __init__(self, configuration: LMStudioEmbeddingConfiguration):
        """Initialize LMStudio Embeddings LLM.

        Args:
            configuration: LMStudio embedding configuration object

        Raises:
            ImportError: If lmstudio package is not installed
            RuntimeError: If embedding model cannot be loaded
        """
        if not LMSTUDIO_AVAILABLE:
            msg = (
                "LMStudio SDK is not installed. "
                "Please install it with: pip install lmstudio"
            )
            raise ImportError(msg)

        self.configuration = configuration
        self._on_error = None

        try:
            log.info(f"Loading LMStudio embedding model: {configuration.model}")
            self.client = lms.embedding_model(configuration.model)
            log.info("LMStudio embedding model loaded successfully")
        except Exception as e:
            msg = f"Failed to load LMStudio embedding model '{configuration.model}': {e}"
            log.error(msg)
            raise RuntimeError(msg) from e

    async def _execute_llm(
        self,
        input: EmbeddingInput,
        **kwargs: Unpack[LLMInput]
    ) -> EmbeddingOutput | None:
        """Execute embedding generation using LMStudio.

        Args:
            input: The input text(s) to embed. Can be:
                - A single string
                - A list of strings
            **kwargs: Additional parameters including:
                - model_parameters: Model-specific parameters

        Returns:
            List of embedding vectors. Each vector is a list of floats.
            - If input is a string: returns [[float, ...]]
            - If input is a list: returns [[float, ...], [float, ...], ...]
        """
        # Get model parameters
        model_params = kwargs.get("model_parameters") or {}
        embedding_config = self.configuration.get_embedding_config(**model_params)

        try:
            # Handle single string input
            if isinstance(input, str):
                log.debug(f"Embedding single text of length {len(input)}")
                embedding = self.client.embed(input)

                # Ensure embedding is a list of floats
                if not isinstance(embedding, list):
                    embedding = list(embedding)

                # LMStudio returns a single embedding for single input
                # GraphRAG expects a list of embeddings
                return [embedding]

            # Handle list of strings input
            elif isinstance(input, list):
                log.debug(f"Embedding batch of {len(input)} texts")
                embeddings = []

                for text in input:
                    embedding = self.client.embed(text)

                    # Ensure embedding is a list of floats
                    if not isinstance(embedding, list):
                        embedding = list(embedding)

                    embeddings.append(embedding)

                return embeddings

            else:
                error_msg = f"Unsupported input type for embedding: {type(input)}"
                log.error(error_msg)
                raise TypeError(error_msg)

        except Exception as e:
            log.error(f"LMStudio embedding failed: {e}")
            raise
