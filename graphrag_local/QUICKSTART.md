# GraphRAG Local - Quick Start Guide

Phase 1 原型驗證快速上手指南

## 前置需求

- Python 3.10+
- GraphRAG 已安裝
- （可選）LMstudio 應用程式

## Step 1: 驗證安裝

檢查 `graphrag_local` 模組是否正確建立：

```bash
# 在 graphrag 專案根目錄執行
ls -la graphrag_local/
```

應該看到：
```
adapters/
config/
optimization/
tests/
__init__.py
README.md
```

## Step 2: 執行測試

### 完整測試套件

```bash
python -m graphrag_local.tests.run_phase1_tests
```

### 個別測試

```bash
# 測試 LMstudio SDK 連接
python graphrag_local/tests/test_connection.py

# 測試適配器實作
python graphrag_local/tests/test_adapters.py
```

## Step 3: 檢視測試結果

成功的測試應該顯示：

```
✓ PASS: Dependency Check
✓ PASS: LMstudio SDK Connection
✓ PASS: Adapter Implementation

🎉 Phase 1 Validation Complete!
```

## Step 4: 理解適配器架構

### 基礎適配器

位置：`graphrag_local/adapters/base.py`

定義兩個核心介面：
- `BaseLLMAdapter` - LLM 文本生成
- `BaseEmbeddingAdapter` - 文本嵌入

### LLM 適配器

位置：`graphrag_local/adapters/lmstudio_llm.py`

提供兩個實作：
- `LMStudioChatAdapter` - 聊天格式模型
- `LMStudioCompletionAdapter` - 完成格式模型

### Embedding 適配器

位置：`graphrag_local/adapters/lmstudio_embedding.py`

提供兩個實作：
- `LMStudioEmbeddingAdapter` - 基本嵌入
- `LMStudioBatchEmbeddingAdapter` - 批次處理與快取

## Step 5: 配置範例

查看配置範本：

```bash
cat graphrag_local/config/local_settings.yaml
```

關鍵配置項目：

```yaml
llm:
  type: local-lmstudio-chat
  model: "qwen/qwen3-4b-2507"  # 你的模型名稱
  temperature: 0.7

embeddings:
  llm:
    type: local-lmstudio-embedding
    model: "nomic-embed-text-v1.5"  # 你的嵌入模型
    batch_size: 32
```

## 常見問題

### Q: 測試顯示 "lmstudio SDK not installed"

**A:** 這是正常的！Phase 1 階段 LMstudio Python SDK 可能尚未公開。測試設計為優雅地處理這種情況。當 SDK 可用時，安裝方式：

```bash
pip install lmstudio
```

### Q: 如何驗證適配器邏輯正確？

**A:** 執行適配器測試：

```bash
python graphrag_local/tests/test_adapters.py
```

這會測試：
- 介面定義正確性
- 訊息格式轉換
- 配置處理
- 非同步方法簽名

### Q: 下一步是什麼？

**A:** Phase 1 完成後：

1. 等待 LMstudio SDK 發布（或使用替代方案）
2. 安裝並配置 LMstudio
3. 載入測試模型
4. 進入 Phase 2：核心適配整合

### Q: 可以使用其他本地 LLM 解決方案嗎？

**A:** 可以！適配器設計是模組化的。你可以：

1. 繼承 `BaseLLMAdapter` 和 `BaseEmbeddingAdapter`
2. 實作對應的方法
3. 使用你偏好的 LLM 框架（Ollama、vLLM 等）

範例：

```python
from graphrag_local.adapters import BaseLLMAdapter

class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, model_name, config=None):
        super().__init__(model_name, config)
        # 初始化 Ollama 客戶端

    def create(self, messages, **kwargs):
        # 實作 Ollama API 調用
        pass
```

## 故障排除

### 導入錯誤

如果遇到導入問題：

```bash
# 確保在正確的目錄
cd /path/to/graphrag

# 檢查 Python 路徑
python -c "import sys; print('\n'.join(sys.path))"

# 確認 graphrag_local 可見
python -c "import graphrag_local; print(graphrag_local.__version__)"
```

### 測試失敗

1. 檢查 Python 版本：`python --version`
2. 確認所有檔案已建立：`ls -R graphrag_local/`
3. 查看詳細錯誤訊息

## 實用指令

```bash
# 查看專案結構
tree graphrag_local/

# 統計程式碼行數
find graphrag_local -name "*.py" -exec wc -l {} + | tail -1

# 檢查程式碼風格（如果安裝了 flake8）
flake8 graphrag_local/

# 執行型別檢查（如果安裝了 mypy）
mypy graphrag_local/
```

## 學習資源

1. **整合規劃文件**
   - `.specify/specs/integration_plan.md`

2. **適配器原始碼**
   - `graphrag_local/adapters/base.py` - 理解介面設計
   - `graphrag_local/adapters/lmstudio_llm.py` - LLM 實作
   - `graphrag_local/adapters/lmstudio_embedding.py` - Embedding 實作

3. **測試範例**
   - `graphrag_local/tests/` - 測試最佳實踐

## 貢獻

發現問題或有改進建議？

1. 查看 `README.md` 了解貢獻指南
2. 在 GitHub 建立 Issue
3. 提交 Pull Request

## 下一階段預覽

Phase 2 將包含：

- ✅ 工廠模式實作（`factory.py`）
- ✅ GraphRAG 配置整合
- ✅ 端對端測試
- ✅ 效能基準測試

---

**Happy Coding!** 🚀

如果你成功完成 Phase 1 驗證，你已經為本地化 GraphRAG 奠定了堅實的基礎！
