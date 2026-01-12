"""
簡化的中文 Tokenizer 適配器 - 不依賴 transformers
"""
import logging

log = logging.getLogger(__name__)

def num_tokens_from_string_qwen(text: str) -> int:
    """
    簡化的中文 token 計算
    基於經驗：中文字符通常 1-2 個 token，英文單詞 1 個 token
    """
    if not text:
        return 0
    
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    english_chars = len(text) - chinese_chars
    
    # 中文字符按 1.2 個 token 計算，英文按 0.3 個 token 計算（考慮單詞）
    estimated_tokens = int(chinese_chars * 1.2 + english_chars * 0.3)
    
    # 最小值為文本長度的 20%
    min_tokens = max(1, len(text) // 5)
    
    return max(estimated_tokens, min_tokens)
