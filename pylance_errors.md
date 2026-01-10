# Pylance IDE 警告分析

## 問題描述
GraphRAG factory.py 文件中出現多個 Pylance 類型檢查警告：

### 主要錯誤類型
1. **Protocol 類別無法具現化**: LLMConfig 是 Protocol，不能直接實例化
2. **參數不存在**: LLMConfig 沒有 max_retries, max_retry_wait, sleep_on_rate_limit_recommendation 參數
3. **類型不匹配**: RateLimitingLLM 和 CachingLLM 無法指派給 BaseLLM

### 具體錯誤
- 第48行: 無法將 Protocol 類別 "LLMConfig" 具現化
- 第49行: 沒有名為 "max_retries" 的參數
- 第50行: 沒有名為 "max_retry_wait" 的參數
- 第51行: 沒有名為 "sleep_on_rate_limit_recommendation" 的參數
- 第53行: RateLimitingLLM 類型不匹配
- 第64行: CachingLLM 類型不匹配
- 類似錯誤在 embedding 函數中重複

## 需要分析的問題
1. LLMConfig 的正確使用方式
2. RateLimitingLLM 的正確構造參數
3. CachingLLM 的正確構造參數
4. 正確的類型註解方式

請分析 GraphRAG 源碼並提供正確的修復方案。
