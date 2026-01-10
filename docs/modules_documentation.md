
# GraphRAG 核心模組技術文件

本文件詳細介紹了 GraphRAG 系統的核心模組、其功能設計以及模組間的協作關係。

---

## 1. graphrag/config (配置管理)
**用途：**
負責系統參數的定義、校驗與載入。它是整個 GraphRAG 運行的基石，確保各個組件能獲得正確的運行配置。

**核心類別與符號：**
- `GraphRagConfig`: 基於 Pydantic 的配置模型，定義了 LLM、索引、查詢等所有參數。
- `create_graphrag_config`: 用於初始化配置對象的工廠函數。
- `load_config_from_file`: 支援從 YAML 或 JSON 檔案載入設定。

**詳細說明：**
配置模組採用分層設計，支援從預設值、環境變數（`.env`）以及外部配置文件中提取資訊。它確保了 LLM API 金鑰、模型名稱、以及索引管線的參數（如 Chunk Size）在系統內部的一致性。

---

## 2. graphrag/index (索引管線)
**用途：**
負責將原始文本轉化為結構化知識圖譜的核心引擎。包含數據攝取、實體提取、關係構建與社群生成。

**核心類別與符號：**
- `run_pipeline_with_config`: 啟動整個索引流程的進入點。
- `Workflow`: 定義一組有序的操作（Verbs），如 `create_base_text_units` 或 `extract_graph_entities`。
- `Verb`: 原子化的數據處理步驟（如文本分割、LLM 調用、圖算法應用）。

**詳細說明：**
索引模組基於管線（Pipeline）架構。它首先將文本切分為 `TextUnits`，利用 LLM 提取 `Entities` 與 `Relationships`，接著使用圖聚類算法（如 Leiden）生成層次化的 `Communities`，並為每個社群生成摘要（Community Reports）。

---

## 3. graphrag/llm (LLM 抽象層)
**用途：**
封裝與大語言模型（LLM）的交互邏輯，提供統一的介面並處理底層通訊細節。

**核心類別與符號：**
- `BaseLLM`: 所有 LLM 實作的基類。
- `OpenAIChatLLM`: 針對 OpenAI/Azure OpenAI Chat API 的具體實作。
- `TpmRpmLLMLimiter`: 速率限制器，確保 API 調用不超過 TPM（每分鐘 Token 數）或 RPM（每分鐘請求數）限制。

**詳細說明：**
該模組提供了強大的穩定性保證，包括自動重試機制、異步調用、以及為了節省成本和提高速度而設計的快取機制（Caching）。

---

## 4. graphrag/model (核心數據模型)
**用途：**
定義了系統中流轉的所有核心領域對象，是各模組間交換數據的標準格式。

**核心類別與符號：**
- `Entity`: 代表圖中的實體（如人名、機構、概念）。
- `Relationship`: 代表實體間的關聯。
- `Community`: 圖的子結構聚類。
- `CommunityReport`: LLM 根據社群內的實體與關係生成的總結報告。
- `TextUnit`: 原始文本的最小處理單元。

---

## 5. graphrag/query (查詢引擎)
**用途：**
基於構建好的知識圖譜執行檢索與問答，提供高效的資訊檢索能力。

**核心類別與符號：**
- `LocalSearch`: 區域搜尋引擎。結合向量檢索與圖結構，專注於特定實體及其一度/二度鄰域。
- `GlobalSearch`: 全域搜尋引擎。利用 `Community Reports` 進行宏觀分析，適合回答綜述性問題。
- `ContextBuilder`: 負責將圖數據轉換為 LLM 可理解的 Prompt 上下文。

**詳細說明：**
查詢模組將 RAG（檢索增強生成）提升到了結構化數據層面。它能根據問題類型自動選擇最適合的檢索策略，確保回答的精確度與全面性。

---

## 6. graphrag/vector_stores (向量存儲)
**用途：**
提供抽象的向量資料庫介面，用於實體與文本單元的相似度檢索。

**核心類別與符號：**
- `BaseVectorStore`: 向量資料庫抽象基類。
- `LanceDBVectorStore`: 基於 LanceDB 的本地磁碟向量儲存實作。
- `AzureAISearch`: 針對 Azure AI Search 的雲端實作。

---

## 模組間的關係與協作流程

1.  **配置啟動**：`config` 模組讀取設定，初始化 `llm` 客戶端與環境參數。
2.  **索引建構**：`index` 模組調用 `llm` 進行實體提取，並將生成的 `Entity`、`Relationship` 等對象存入 `model` 結構中。同時，利用 `vector_stores` 為文本建立索引。
3.  **數據持久化**：索引產生的 `CommunityReports` 與圖數據被存儲，供後續查詢。
4.  **查詢檢索**：當使用者提問時，`query` 模組透過 `vector_stores` 進行語義搜尋，並從 `model` 中提取相關的圖結構上下文。
5.  **生成回答**：`query` 模組將組裝好的上下文發送給 `llm`，最終生成準確的回答。
