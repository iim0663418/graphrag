# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utilities for working with tokens."""

import logging

import tiktoken
from .qwen_tokenizer import num_tokens_from_string_qwen

DEFAULT_ENCODING_NAME = "cl100k_base"
log = logging.getLogger(__name__)


def num_tokens_from_string(
    string: str, model: str | None = None, encoding_name: str | None = None
) -> int:
    """Return the number of tokens in a text string."""
    # 檢查是否使用 Qwen 模型
    if model and ("qwen" in model.lower() or "qwen3-vl" in model.lower()):
        return num_tokens_from_string_qwen(string)
    
    # 原有的 OpenAI tokenizer 邏輯
    if model is not None:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            msg = f"Failed to get encoding for {model} when getting num_tokens_from_string. Fall back to default encoding {DEFAULT_ENCODING_NAME}"
            log.warning(msg)
            encoding = tiktoken.get_encoding(DEFAULT_ENCODING_NAME)
    else:
        encoding = tiktoken.get_encoding(encoding_name or DEFAULT_ENCODING_NAME)
    return len(encoding.encode(string))


def string_from_tokens(
    tokens: list[int], model: str | None = None, encoding_name: str | None = None
) -> str:
    """Return a text string from a list of tokens."""
    if model is not None:
        encoding = tiktoken.encoding_for_model(model)
    elif encoding_name is not None:
        encoding = tiktoken.get_encoding(encoding_name)
    else:
        msg = "Either model or encoding_name must be specified."
        raise ValueError(msg)
    return encoding.decode(tokens)
