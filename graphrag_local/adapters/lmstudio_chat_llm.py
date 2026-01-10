"""
LMStudio Chat LLM Adapter - Phase 2 Core Integration.

This module provides a full GraphRAG-compatible LLM implementation using LMStudio,
replacing OpenAI API calls with local model inference via the LMStudio Python SDK.
"""

import json
import logging
import re
from typing import Any

try:
    from typing_extensions import Unpack  # type: ignore[import-untyped]
except ImportError:
    from typing import Unpack  # type: ignore[attr-defined]

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)

try:
    import lmstudio as lms  # type: ignore[import-untyped]
    LMSTUDIO_AVAILABLE = True
except ImportError:
    lms = None  # type: ignore
    LMSTUDIO_AVAILABLE = False
    lms = None

log = logging.getLogger(__name__)


class LMStudioConfiguration:
    """Configuration for LMStudio LLM adapter."""

    def __init__(self, config: dict[str, Any]):
        """Initialize LMStudio configuration.

        Args:
            config: Configuration dictionary containing model settings
        """
        self.model = config.get("model", "")
        self.temperature = config.get("temperature")
        self.max_tokens = config.get("max_tokens")
        self.top_p = config.get("top_p")
        self.model_supports_json = config.get("model_supports_json", False)

        # Store any additional config parameters
        self._extra_config = {
            k: v for k, v in config.items()
            if k not in ["model", "temperature", "max_tokens", "top_p", "model_supports_json"]
        }

    def get_generation_config(self, **overrides: Any) -> dict[str, Any]:
        """Get generation configuration with optional overrides.

        Args:
            **overrides: Optional parameter overrides

        Returns:
            Dictionary of generation parameters
        """
        config = {}

        # Only add parameters if they are set
        if self.temperature is not None:
            config["temperature"] = self.temperature
        if self.max_tokens is not None:
            config["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            config["top_p"] = self.top_p

        # Add extra config
        config.update(self._extra_config)

        # Apply overrides
        config.update(overrides)

        return config


class LMStudioChatLLM(BaseLLM[CompletionInput, CompletionOutput]):
    """LMStudio Chat LLM adapter for GraphRAG.

    This adapter implements the GraphRAG LLM interface using LMStudio's Python SDK,
    allowing GraphRAG to use locally-hosted models instead of OpenAI API.

    This is the Phase 2 implementation that fully integrates with GraphRAG's
    configuration system and supports all GraphRAG features including:
    - JSON mode output
    - Chat history
    - Variable substitution
    - Retry logic

    Example:
        >>> config = {"model": "qwen/qwen3-4b-2507", "temperature": 0.0}
        >>> llm_config = LMStudioConfiguration(config)
        >>> llm = LMStudioChatLLM(llm_config)
        >>> result = await llm("What is GraphRAG?", name="test_query")
    """

    _client: Any  # lms.LLM instance
    _configuration: LMStudioConfiguration

    def __init__(self, configuration: LMStudioConfiguration):
        """Initialize LMStudio Chat LLM.

        Args:
            configuration: LMStudio configuration object

        Raises:
            ImportError: If lmstudio package is not installed
            RuntimeError: If model cannot be loaded
        """
        if not LMSTUDIO_AVAILABLE or lms is None:
            msg = (
                "LMStudio SDK is not installed. "
                "Please install it with: pip install lmstudio"
            )
            raise ImportError(msg)

        self.configuration = configuration
        self._on_error = None

        try:
            log.info(f"Loading LMStudio model: {configuration.model}")
            self.client = lms.llm(configuration.model)  # type: ignore
            log.info("LMStudio model loaded successfully")
        except Exception as e:
            msg = f"Failed to load LMStudio model '{configuration.model}': {e}"
            log.error(msg)
            raise RuntimeError(msg) from e

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput]
    ) -> CompletionOutput | None:
        """Execute LLM inference using LMStudio.

        Args:
            input: The input prompt string
            **kwargs: Additional LLM parameters including:
                - history: Chat history
                - model_parameters: Model-specific parameters
                - variables: Template variables (handled by caller)

        Returns:
            Generated text response
        """
        # Build chat messages
        history = kwargs.get("history") or []
        messages = [*history, {"role": "user", "content": input}]

        # Create LMStudio Chat object
        if not LMSTUDIO_AVAILABLE or lms is None:
            raise RuntimeError("LMStudio SDK not available")
            
        chat = lms.Chat()  # type: ignore

        # Add messages to chat
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # LMStudio handles system messages
                chat.add_system_message(content)
            elif role == "user":
                chat.add_user_message(content)
            elif role == "assistant":
                chat.add_assistant_message(content)
            else:
                log.warning(f"Unknown message role: {role}, treating as user message")
                chat.add_user_message(content)

        # Merge configuration with runtime parameters
        model_params = kwargs.get("model_parameters") or {}
        generation_config = self.configuration.get_generation_config(**model_params)

        try:
            # Call LMStudio model
            log.debug(f"Calling LMStudio with config: {generation_config}")
            result = self.client.respond(chat, config=generation_config)

            # Extract response content
            if hasattr(result, 'content'):
                response = result.content
            else:
                response = str(result)

            log.debug(f"LMStudio response length: {len(response)} chars")
            return response

        except Exception as e:
            log.error(f"LMStudio inference failed: {e}")
            raise

    async def _invoke_json(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """Generate JSON output from LMStudio.

        For models that support JSON mode, uses native JSON output.
        Otherwise, falls back to manual JSON parsing.

        Args:
            input: The input prompt
            **kwargs: Additional parameters including:
                - is_response_valid: Validation function for JSON output
                - name: Operation name for logging

        Returns:
            LLMOutput with parsed JSON

        Raises:
            RuntimeError: If JSON generation fails after retries
        """
        name = kwargs.get("name") or "unknown"
        is_response_valid = kwargs.get("is_response_valid") or (lambda _x: True)

        _MAX_GENERATION_RETRIES = 3

        async def generate(attempt: int | None = None) -> LLMOutput[CompletionOutput]:
            call_name = name if attempt is None else f"{name}@{attempt}"
            if self.configuration.model_supports_json:
                return await self._native_json(input, **{**kwargs, "name": call_name})
            else:
                return await self._manual_json(input, **{**kwargs, "name": call_name})

        def is_valid(x: dict | None) -> bool:
            return x is not None and is_response_valid(x)

        # First attempt
        result = await generate()
        retry = 0

        # Retry if validation fails
        while not is_valid(result.json) and retry < _MAX_GENERATION_RETRIES:
            result = await generate(retry)
            retry += 1

        if is_valid(result.json):
            return result

        # Failed to generate valid JSON
        error_msg = f"Failed to generate valid JSON output - Faulty JSON: {result.json!s}"
        raise RuntimeError(error_msg)

    async def _native_json(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[CompletionOutput]:
        """Generate JSON using model's native JSON mode.

        Args:
            input: The input prompt
            **kwargs: Additional parameters

        Returns:
            LLMOutput with parsed JSON
        """
        # Add JSON format instruction to model parameters
        result = await self._invoke(
            input,
            **{
                **kwargs,
                "model_parameters": {
                    **(kwargs.get("model_parameters") or {}),
                    # LMStudio may support response_format like OpenAI
                    "response_format": {"type": "json_object"},
                },
            },
        )

        # Parse JSON from output
        output = result.output or ""
        output_clean, json_output = self._try_parse_json_object(output)

        return LLMOutput[CompletionOutput](
            output=output_clean,
            json=json_output,
            history=result.history,
        )

    async def _manual_json(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput]
    ) -> LLMOutput[CompletionOutput]:
        """Generate and parse JSON manually from text output.

        Args:
            input: The input prompt
            **kwargs: Additional parameters

        Returns:
            LLMOutput with parsed JSON
        """
        # Generate response
        result = await self._invoke(input, **kwargs)
        output = result.output or ""
        history = result.history or []

        # Try to parse JSON
        output_clean, json_output = self._try_parse_json_object(output)

        if json_output:
            return LLMOutput[CompletionOutput](
                output=output_clean,
                json=json_output,
                history=history,
            )

        # If parsing failed, log warning and return None json
        # The retry logic in _invoke_json will handle this
        log.warning("Failed to parse JSON from LLM output")
        return LLMOutput[CompletionOutput](
            output=output,
            json=None,
            history=history,
        )

    def _try_parse_json_object(self, text: str) -> tuple[str, dict | None]:
        """Try to parse JSON from text, handling markdown code blocks.

        Args:
            text: Input text that may contain JSON

        Returns:
            Tuple of (cleaned_text, parsed_json or None)
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            json_str = json_match.group(0) if json_match else text

        # Parse JSON
        try:
            json_output = json.loads(json_str)
            # Return cleaned version without markdown wrapper
            return (json_str.strip(), json_output)
        except json.JSONDecodeError:
            return (text, None)
