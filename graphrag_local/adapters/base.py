"""
Base adapter interfaces for LLM and Embedding models.

These abstract classes define the contract that any local model adapter
must implement to work with GraphRAG.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.

    This adapter translates GraphRAG's LLM interface calls into
    local model SDK calls.
    """

    def __init__(self, model_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM adapter.

        Args:
            model_name: Name/identifier of the model to use
            config: Optional configuration dictionary
        """
        self.model_name = model_name
        self.config = config or {}

    @abstractmethod
    async def acreate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Asynchronously generate a response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
                     Compatible with OpenAI message format
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response as a string
        """
        pass

    @abstractmethod
    def create(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Synchronously generate a response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional generation parameters

        Returns:
            Generated text response as a string
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_name": self.model_name,
            "config": self.config
        }


class BaseEmbeddingAdapter(ABC):
    """
    Abstract base class for embedding model adapters.

    This adapter translates GraphRAG's embedding interface calls into
    local embedding model SDK calls.
    """

    def __init__(self, model_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the embedding adapter.

        Args:
            model_name: Name/identifier of the embedding model to use
            config: Optional configuration dictionary
        """
        self.model_name = model_name
        self.config = config or {}

    @abstractmethod
    async def aembed(self, text: str, **kwargs) -> List[float]:
        """
        Asynchronously generate embeddings for a single text.

        Args:
            text: Input text to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def embed(self, text: str, **kwargs) -> List[float]:
        """
        Synchronously generate embeddings for a single text.

        Args:
            text: Input text to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    async def aembed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Asynchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of embedding vectors, one per input text
        """
        pass

    @abstractmethod
    def embed_batch(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Synchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of embedding vectors, one per input text
        """
        pass

    def get_embedding_dimension(self) -> Optional[int]:
        """
        Get the dimension of the embedding vectors.

        Returns:
            Integer dimension size, or None if unknown
        """
        return None

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded embedding model.

        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_name": self.model_name,
            "config": self.config,
            "dimension": self.get_embedding_dimension()
        }
