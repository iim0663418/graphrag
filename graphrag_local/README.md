# GraphRAG Local - Phase 1: Prototype Validation

本地化 GraphRAG 整合專案 - LMstudio SDK 整合

## 專案概述

GraphRAG Local 提供完整的本地化解決方案，讓 Microsoft GraphRAG 能夠使用本地 LMstudio 模型，實現：

- ✅ 完全離線運作，無需 API 金鑰
- ✅ 隱私保護，資料不離開本機
- ✅ 零 API 費用
- ✅ 可自訂模型選擇

## Phase 1 目標

Phase 1 專注於原型驗證，包含：

1. **目錄結構建立** ✅
   - 適配器模組 (`adapters/`)
   - 配置管理 (`config/`)
   - 優化工具 (`optimization/`)
   - 測試套件 (`tests/`)

2. **基礎 LMstudio SDK 連接測試** ✅
   - SDK 導入測試
   - 客戶端建立測試
   - 模型列表測試
   - 基礎完成與嵌入測試

3. **適配器原型實作** ✅
   - `base.py` - 基礎介面定義
   - `lmstudio_llm.py` - LLM 適配器
   - `lmstudio_embedding.py` - Embedding 適配器

4. **測試腳本創建** ✅
   - 連接測試 (`test_connection.py`)
   - 適配器測試 (`test_adapters.py`)
   - 整合測試執行器 (`run_phase1_tests.py`)

## 目錄結構

```
graphrag_local/
├── __init__.py
├── README.md
├── adapters/
│   ├── __init__.py
│   ├── base.py                    # 基礎適配器介面
│   ├── lmstudio_llm.py            # LLM 適配器實作
│   └── lmstudio_embedding.py      # Embedding 適配器實作
├── optimization/
│   ├── __init__.py
│   ├── batch_processor.py         # (待 Phase 3 實作)
│   └── cache_manager.py           # (待 Phase 3 實作)
├── config/
│   ├── __init__.py
│   └── local_settings.yaml        # 配置範本
└── tests/
    ├── __init__.py
    ├── test_connection.py         # SDK 連接測試
    ├── test_adapters.py           # 適配器驗證測試
    └── run_phase1_tests.py        # 完整測試執行器
```

## 快速開始

### 1. 環境準備

```bash
# 確保在 graphrag 專案根目錄
cd /path/to/graphrag

# 安裝 GraphRAG (如果尚未安裝)
pip install -e .
```

### 2. 執行 Phase 1 測試

```bash
# 執行完整的 Phase 1 驗證測試
python -m graphrag_local.tests.run_phase1_tests
```

### 3. 單獨測試模組

```bash
# 僅測試 SDK 連接
python graphrag_local/tests/test_connection.py

# 僅測試適配器實作
python graphrag_local/tests/test_adapters.py
```

## 適配器設計

### BaseLLMAdapter

基礎 LLM 適配器介面，定義所有 LLM 適配器必須實作的方法：

```python
class BaseLLMAdapter(ABC):
    @abstractmethod
    async def acreate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """非同步生成回應"""
        pass

    @abstractmethod
    def create(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步生成回應"""
        pass
```

### BaseEmbeddingAdapter

基礎 Embedding 適配器介面：

```python
class BaseEmbeddingAdapter(ABC):
    @abstractmethod
    async def aembed(self, text: str, **kwargs) -> List[float]:
        """非同步生成單一文本的嵌入"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """批次生成多個文本的嵌入"""
        pass
```

### LMStudioChatAdapter

LMstudio 聊天模型適配器，支援：

- OpenAI 訊息格式轉換
- 可配置的生成參數（temperature, max_tokens, top_p）
- 同步與非同步介面
- 系統訊息處理

### LMStudioEmbeddingAdapter

LMstudio 嵌入模型適配器，支援：

- 單一文本嵌入
- 批次處理
- 向量正規化
- 嵌入維度自動檢測
- 簡易快取機制 (LMStudioBatchEmbeddingAdapter)

## 配置範例

參考 `config/local_settings.yaml` 了解如何配置本地模型：

```yaml
llm:
  type: local-lmstudio-chat
  model: "qwen/qwen3-4b-2507"
  temperature: 0.7
  max_tokens: 2048

embeddings:
  llm:
    type: local-lmstudio-embedding
    model: "nomic-embed-text-v1.5"
    batch_size: 32
```

## 測試結果

執行 Phase 1 測試後，你應該會看到：

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          GraphRAG Local - Phase 1: Prototype Validation          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

PHASE 1 VALIDATION REPORT
======================================================================

Test Results:
  ✓ PASS: Dependency Check
  ✓ PASS: LMstudio SDK Connection
  ✓ PASS: Adapter Implementation

Overall: 3/3 test suites passed

🎉 Phase 1 Validation Complete!
```

## 已知限制 (Phase 1)

1. **LMstudio SDK 依賴**
   - 目前 LMstudio Python SDK 可能尚未公開發布
   - 測試腳本會優雅地處理 SDK 缺失情況
   - 一旦 SDK 可用，需要安裝：`pip install lmstudio`

2. **實際模型測試**
   - Phase 1 主要測試介面定義與適配器結構
   - 實際的模型載入與推論測試需要 LMstudio 運行中

3. **API 差異**
   - LMstudio SDK 的實際 API 可能與範例程式碼有差異
   - 需要根據官方文件調整適配器實作

## 下一步：Phase 2

Phase 1 完成後，下一階段將專注於：

1. **核心適配** (2 週)
   - 將適配器整合到 GraphRAG 主程式碼
   - 實作配置載入機制
   - 替換預設的 OpenAI 調用

2. **整合測試**
   - 使用真實 LMstudio 模型測試
   - 端對端 indexing pipeline 測試
   - 查詢功能驗證

3. **文件與範例**
   - 使用手冊
   - 範例程式碼
   - 故障排除指南

## 貢獻指南

### 報告問題

如果發現問題，請提供：

1. 錯誤訊息完整輸出
2. Python 版本與環境資訊
3. LMstudio 版本（如果已安裝）
4. 重現步驟

### 提交改進

歡迎提交 Pull Request！請確保：

1. 通過所有現有測試
2. 新增適當的測試覆蓋
3. 遵循現有程式碼風格
4. 更新相關文件

## 授權

本專案遵循與 Microsoft GraphRAG 相同的授權條款。

## 聯絡資訊

- 專案維護者：[Your Name]
- 問題追蹤：GitHub Issues
- 文件：本 README 與 `.specify/specs/integration_plan.md`

---

**Phase 1 Status**: ✅ 完成
**Last Updated**: 2026-01-10
