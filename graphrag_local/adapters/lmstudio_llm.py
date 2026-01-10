"""
LMstudio LLM Adapter for GraphRAG.

This adapter translates GraphRAG's LLM interface calls into LMstudio SDK calls,
allowing GraphRAG to use local models running in LMstudio.

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

from .base import BaseLLMAdapter


class LMStudioChatAdapter(BaseLLMAdapter):
    """
    Adapter for LMstudio chat/completion models.

    This adapter allows GraphRAG to interact with local LLMs running in LMstudio
    using the same interface it would use for cloud-based models.
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LMstudio chat adapter.

        Args:
            model_name: Name/identifier of the model in LMstudio
            config: Optional configuration including:
                - temperature: float (default: 0.7)
                - max_tokens: int (default: 2048)
                - top_p: float (default: 1.0)
                - stream: bool (default: False)

        Raises:
            ImportError: If lmstudio SDK is not installed
            RuntimeError: If model cannot be loaded
        """
        super().__init__(model_name, config)

        if not LMSTUDIO_AVAILABLE:
            raise ImportError(
                "lmstudio SDK is not installed. "
                "Please install it with: pip install lmstudio"
            )

        # Default configuration
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.top_p = self.config.get("top_p", 1.0)
        self.stream = self.config.get("stream", False)

        # Initialize the model
        if not LMSTUDIO_AVAILABLE or lms is None:
            raise RuntimeError("LMStudio SDK not available")
            
        try:
            self.model = lms.llm(model_name)  # type: ignore
            print(f"✓ Loaded LMstudio model: {model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {e}")

    def _convert_messages_to_chat(
        self,
        messages: List[Dict[str, str]]
    ) -> Any:
        """
        Convert OpenAI-style messages to LMstudio Chat object.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            LMstudio Chat object

        Note:
            This is a prototype implementation. The actual API may differ
            based on LMstudio SDK version.
        """
        if not LMSTUDIO_AVAILABLE or lms is None:
            raise RuntimeError("LMStudio SDK not available")
            
        chat = lms.Chat()  # type: ignore

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Handle system messages
                # May need special handling depending on SDK
                try:
                    chat.add_system_message(content)
                except AttributeError:
                    # Fallback: prepend to first user message
                    chat.add_user_message(f"[SYSTEM]: {content}")

            elif role == "user":
                chat.add_user_message(content)

            elif role == "assistant":
                chat.add_assistant_message(content)

            else:
                # Unknown role, default to user
                chat.add_user_message(content)

        return chat

    async def acreate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Asynchronously generate a response using LMstudio.

        Args:
            messages: List of message dictionaries (OpenAI format)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails
        """
        # Run the synchronous create method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create, messages, **kwargs)

    def create(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Synchronously generate a response using LMstudio.

        Args:
            messages: List of message dictionaries (OpenAI format)
            **kwargs: Additional parameters override config values

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails
        """
        try:
            # Convert messages to Chat format
            chat = self._convert_messages_to_chat(messages)

            # Merge configurations (kwargs override defaults)
            generation_config = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "top_p": kwargs.get("top_p", self.top_p),
            }

            # Call the model
            # Note: Actual API may vary
            result = self.model.respond(chat, config=generation_config)

            # Extract text from result
            # This depends on the SDK's response format
            if hasattr(result, "content"):
                return result.content
            elif isinstance(result, str):
                return result
            else:
                return str(result)

        except Exception as e:
            raise Exception(f"LMstudio generation failed: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model metadata
        """
        info = super().get_model_info()
        info.update({
            "sdk": "lmstudio",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        })
        return info


class LMStudioCompletionAdapter(BaseLLMAdapter):
    """
    Adapter for LMstudio text completion (non-chat) models.

    This is for simpler completion-style models that don't use chat format.
    """

    def __init__(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LMstudio completion adapter.

        Args:
            model_name: Name/identifier of the model in LMstudio
            config: Optional configuration dictionary
        """
        super().__init__(model_name, config)

        if not LMSTUDIO_AVAILABLE or lms is None:
            raise RuntimeError("LMStudio SDK not available")

        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)

        try:
            self.model = lms.llm(model_name)  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {e}")

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message list to a single prompt string.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    async def acreate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Asynchronously generate completion.

        Args:
            messages: Message list to convert to prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create, messages, **kwargs)

    def create(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Synchronously generate completion.

        Args:
            messages: Message list to convert to prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            prompt = self._messages_to_prompt(messages)

            generation_config = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            result = self.model.complete(prompt, config=generation_config)

            if hasattr(result, "content"):
                return result.content
            elif isinstance(result, str):
                return result
            else:
                return str(result)

        except Exception as e:
            raise Exception(f"LMstudio completion failed: {e}")
