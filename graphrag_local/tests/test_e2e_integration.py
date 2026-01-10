"""
End-to-End Integration Tests for LMStudio + GraphRAG Phase 2.

This test suite validates the complete integration of LMStudio with GraphRAG,
including configuration loading, LLM inference, and embedding generation.
"""

import asyncio
import pytest

from graphrag.config import create_graphrag_config
from graphrag.config.enums import LLMType
from graphrag.llm.types import LLMOutput

# Import LMStudio adapters
try:
    from graphrag_local.adapters.lmstudio_chat_llm import (
        LMStudioChatLLM,
        LMStudioConfiguration,
    )
    from graphrag_local.adapters.lmstudio_embeddings_llm import (
        LMStudioEmbeddingsLLM,
        LMStudioEmbeddingConfiguration,
    )
    from graphrag_local.lmstudio_factories import (
        create_lmstudio_chat_llm,
        create_lmstudio_embedding_llm,
    )
    LMSTUDIO_AVAILABLE = True
except ImportError:
    LMSTUDIO_AVAILABLE = False

# Skip all tests if lmstudio is not available
pytestmark = pytest.mark.skipif(
    not LMSTUDIO_AVAILABLE,
    reason="LMStudio SDK not installed"
)


class TestLMStudioChatLLM:
    """Test suite for LMStudio Chat LLM integration."""

    @pytest.fixture
    def chat_config(self):
        """Create a test configuration for chat LLM."""
        return {
            "model": "qwen/qwen3-4b-2507",
            "temperature": 0.0,
            "max_tokens": 100,
            "top_p": 1.0,
            "model_supports_json": False,
        }

    @pytest.fixture
    def chat_llm(self, chat_config):
        """Create a LMStudio chat LLM instance."""
        config = LMStudioConfiguration(chat_config)
        return LMStudioChatLLM(config)

    @pytest.mark.asyncio
    async def test_basic_completion(self, chat_llm):
        """Test basic text completion."""
        result = await chat_llm(
            "What is GraphRAG?",
            name="test_basic_completion"
        )

        assert isinstance(result, LLMOutput)
        assert result.output is not None
        assert len(result.output) > 0
        print(f"\n✓ Basic completion result: {result.output[:100]}...")

    @pytest.mark.asyncio
    async def test_chat_history(self, chat_llm):
        """Test chat with history."""
        history = [
            {"role": "user", "content": "Hi, I'm learning about knowledge graphs."},
            {"role": "assistant", "content": "That's great! Knowledge graphs are powerful tools."}
        ]

        result = await chat_llm(
            "What is GraphRAG?",
            history=history,
            name="test_chat_history"
        )

        assert isinstance(result, LLMOutput)
        assert result.output is not None
        print(f"\n✓ Chat with history result: {result.output[:100]}...")

    @pytest.mark.asyncio
    async def test_json_mode(self, chat_config):
        """Test JSON mode output."""
        chat_config["model_supports_json"] = True
        config = LMStudioConfiguration(chat_config)
        llm = LMStudioChatLLM(config)

        prompt = """Extract entities from this text and return as JSON:
        "Microsoft was founded by Bill Gates in 1975 in Seattle."

        Return format: {"entities": [{"name": "...", "type": "..."}]}
        """

        result = await llm(
            prompt,
            json=True,
            name="test_json_mode"
        )

        assert isinstance(result, LLMOutput)
        assert result.json is not None
        assert "entities" in result.json or result.json is not None
        print(f"\n✓ JSON mode result: {result.json}")


class TestLMStudioEmbeddingsLLM:
    """Test suite for LMStudio Embeddings LLM integration."""

    @pytest.fixture
    def embedding_config(self):
        """Create a test configuration for embedding LLM."""
        return {
            "model": "nomic-embed-text-v1.5",
        }

    @pytest.fixture
    def embedding_llm(self, embedding_config):
        """Create a LMStudio embedding LLM instance."""
        config = LMStudioEmbeddingConfiguration(embedding_config)
        return LMStudioEmbeddingsLLM(config)

    @pytest.mark.asyncio
    async def test_single_embedding(self, embedding_llm):
        """Test embedding a single text."""
        result = await embedding_llm(
            "GraphRAG is a knowledge graph system.",
            name="test_single_embedding"
        )

        assert isinstance(result, LLMOutput)
        assert result.output is not None
        assert isinstance(result.output, list)
        assert len(result.output) > 0
        assert isinstance(result.output[0], list)
        assert all(isinstance(x, float) for x in result.output[0])
        print(f"\n✓ Single embedding dimension: {len(result.output[0])}")

    @pytest.mark.asyncio
    async def test_batch_embedding(self, embedding_llm):
        """Test embedding multiple texts."""
        texts = [
            "GraphRAG is a knowledge graph system.",
            "LMStudio is a local LLM runner.",
            "Python is a programming language."
        ]

        result = await embedding_llm(
            texts,
            name="test_batch_embedding"
        )

        assert isinstance(result, LLMOutput)
        assert result.output is not None
        assert isinstance(result.output, list)
        assert len(result.output) == len(texts)
        assert all(isinstance(emb, list) for emb in result.output)
        print(f"\n✓ Batch embedding count: {len(result.output)}")


class TestLMStudioFactories:
    """Test suite for LMStudio factory functions."""

    def test_create_chat_llm(self):
        """Test creating chat LLM via factory."""
        config = {
            "model": "qwen/qwen3-4b-2507",
            "temperature": 0.0,
        }

        llm = create_lmstudio_chat_llm(config)
        assert llm is not None
        print("\n✓ Chat LLM created via factory")

    def test_create_embedding_llm(self):
        """Test creating embedding LLM via factory."""
        config = {
            "model": "nomic-embed-text-v1.5",
        }

        llm = create_lmstudio_embedding_llm(config)
        assert llm is not None
        print("\n✓ Embedding LLM created via factory")


class TestGraphRAGConfigIntegration:
    """Test suite for GraphRAG configuration integration."""

    def test_lmstudio_enum_exists(self):
        """Test that LMStudio LLMType enums exist."""
        assert hasattr(LLMType, "LMStudioChat")
        assert hasattr(LLMType, "LMStudioEmbedding")
        assert LLMType.LMStudioChat.value == "lmstudio_chat"
        assert LLMType.LMStudioEmbedding.value == "lmstudio_embedding"
        print("\n✓ LMStudio LLMType enums registered")

    def test_config_creation(self):
        """Test creating GraphRAG config with LMStudio."""
        config_values = {
            "llm": {
                "type": "lmstudio_chat",
                "model": "qwen/qwen3-4b-2507",
                "temperature": 0.0,
            },
            "embeddings": {
                "llm": {
                    "type": "lmstudio_embedding",
                    "model": "nomic-embed-text-v1.5",
                }
            }
        }

        config = create_graphrag_config(values=config_values)

        assert config.llm.type == LLMType.LMStudioChat
        assert config.llm.model == "qwen/qwen3-4b-2507"
        assert config.embeddings.llm.type == LLMType.LMStudioEmbedding
        assert config.embeddings.llm.model == "nomic-embed-text-v1.5"
        print("\n✓ GraphRAG config created with LMStudio settings")


class TestEndToEndPipeline:
    """End-to-end pipeline test."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_pipeline(self):
        """Test the full pipeline: config -> LLM creation -> inference."""
        # 1. Create configuration
        config_values = {
            "llm": {
                "type": "lmstudio_chat",
                "model": "qwen/qwen3-4b-2507",
                "temperature": 0.0,
                "max_tokens": 100,
            },
            "embeddings": {
                "llm": {
                    "type": "lmstudio_embedding",
                    "model": "nomic-embed-text-v1.5",
                }
            }
        }

        config = create_graphrag_config(values=config_values)
        print("\n✓ Step 1: Configuration created")

        # 2. Create LLMs
        chat_llm = create_lmstudio_chat_llm({
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
        })

        embedding_llm = create_lmstudio_embedding_llm({
            "model": config.embeddings.llm.model,
        })
        print("✓ Step 2: LLMs created")

        # 3. Test chat completion
        chat_result = await chat_llm(
            "What is a knowledge graph?",
            name="e2e_test_chat"
        )
        assert chat_result.output is not None
        print(f"✓ Step 3: Chat completion successful: {chat_result.output[:50]}...")

        # 4. Test embedding
        embed_result = await embedding_llm(
            "Knowledge graphs organize information.",
            name="e2e_test_embed"
        )
        assert embed_result.output is not None
        assert len(embed_result.output) > 0
        print(f"✓ Step 4: Embedding successful: dimension={len(embed_result.output[0])}")

        print("\n✅ Full E2E pipeline test PASSED!")


if __name__ == "__main__":
    """Run tests directly."""
    print("=" * 70)
    print("LMStudio + GraphRAG Phase 2 - End-to-End Integration Tests")
    print("=" * 70)

    # Run with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])
