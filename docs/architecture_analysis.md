基於提供的檔案結構與上下文，以下為 GraphRAG 專案的綜合架構分析報告。

# GraphRAG 系統架構分析 (System Architecture Analysis)

## 1. 系統概覽 (System Overview)
GraphRAG 是一個基於知識圖譜 (Knowledge Graph) 的檢索增強生成 (RAG) 系統。其主要目標是透過結構化的圖譜資訊來增強大型語言模型 (LLM) 的上下文理解與檢索能力。專案採用高度模組化的設計，將索引 (Indexing)、查詢 (Querying)、LLM 互動與配置管理分離，以支援可擴展的資料處理管線與靈活的檢索策略。

## 2. 核心組件 (Core Components)

系統主要由 `graphrag` 套件下的幾個核心子模組構成：

### 2.1 索引引擎 (`graphrag.index`)
這是系統的資料處理核心，負責將原始文本轉換為知識圖譜。
*   **Workflows & Verbs**: 採用管線式架構 (`workflows`, `verbs`)，定義了一系列資料轉換操作（如文字分割、實體抽取、摘要生成）。
*   **Storage & Cache**: 提供資料持久化 (`storage`) 與中間結果快取 (`cache`) 機制，支援中斷恢復與增量更新。
*   **Graph Processing**: 包含圖譜建構 (`graph`) 與社群檢測等邏輯。
*   **API & CLI**: 提供 `api.py` 與 `cli.py` 作為外部呼叫入口。

### 2.2 查詢引擎 (`graphrag.query`)
負責處理使用者查詢，利用已建立的索引進行檢索。
*   **Search Strategies**: 雖然檔案列表未完全展開，但通常包含 "Local Search" (針對特定實體鄰域) 與 "Global Search" (針對全域社群摘要) 兩種策略。
*   **Context Building**: 負責從圖譜與向量資料庫中組裝上下文。

### 2.3 LLM 抽象層 (`graphrag.llm`)
統一處理與大型語言模型的互動。
*   **Provider Abstraction**: 包含 `openai` 與 `mock` 等實作，允許切換不同的底層模型。
*   **Rate Limiting**: `limiting` 模組負責處理 API 速率限制與重試機制。

### 2.4 提示詞優化 (`graphrag.prompt_tune`)
自動化生成與優化領域特定的 Prompt。
*   **Generators**: 包含 `community_report_summarization`, `entity_extraction_prompt`, `persona` 等生成器，用於針對特定資料領域自動調整 Prompt，提升抽取與生成品質。

### 2.5 向量儲存 (`graphrag.vector_stores`)
負責向量資料的儲存與檢索介面。
*   **Adapters**: 支援多種後端，如 `lancedb` (本地/嵌入式) 與 `azure_ai_search` (雲端服務)。
*   **Interface**: 透過 `base.py` 定義統一介面，實現儲存層的抽換。

### 2.6 配置管理 (`graphrag.config`)
集中管理系統設定。
*   **Loading**: 支援從環境變數 (`environment_reader.py`) 與設定檔 (`config_file_loader.py`) 讀取配置。
*   **Models**: 定義強型別的配置模型 (`input_models`, `models`)，確保設定的正確性。

## 3. 資料流 (Data Flow)

1.  **配置載入**: 系統啟動時透過 `graphrag.config` 載入環境與使用者設定。
2.  **索引階段 (Indexing Phase)**:
    *   **Input**: 讀取原始文件。
    *   **Text Splitting**: 透過 `index.text_splitting` 進行切分。
    *   **Extraction**: 利用 `llm` 模組與優化後的 Prompt (`prompt_tune`) 抽取實體與關係。
    *   **Graph Construction**: 建立圖譜結構。
    *   **Community Detection**: 識別圖譜社群並生成摘要 (`model.community_report`)。
    *   **Indexing**: 生成向量索引並存入 `vector_stores`。
3.  **查詢階段 (Query Phase)**:
    *   **Input**: 接收使用者問題。
    *   **Retrieval**: 根據查詢策略 (Global/Local)，從 `vector_stores` 檢索相關實體或社群報告。
    *   **Synthesis**: 結合檢索到的上下文，透過 `llm` 生成最終回答。

## 4. 模組依賴 (Module Dependencies)

*   **`graphrag.index`** 依賴於：
    *   `graphrag.llm` (用於抽取與摘要)
    *   `graphrag.model` (資料結構定義)
    *   `graphrag.config` (管線設定)
    *   `graphrag.vector_stores` (寫入索引)
*   **`graphrag.query`** 依賴於：
    *   `graphrag.vector_stores` (讀取索引)
    *   `graphrag.llm` (生成答案)
    *   `graphrag.model`
*   **`graphrag.prompt_tune`** 依賴於：
    *   `graphrag.llm` (用於生成與評估 Prompt)
*   **共用基礎**: `config`, `model`, `llm` 是被上層應用 (`index`, `query`) 共同依賴的基礎設施。

## 5. 關鍵設計模式 (Key Design Patterns)

1.  **Pipeline / Workflow Pattern**: 在 `graphrag.index` 中明顯使用了管線模式，將複雜的索引過程拆解為獨立的、可組合的 "Verbs" (操作單元)。
2.  **Strategy Pattern (策略模式)**:
    *   `vector_stores`: 透過 `BaseVectorStore` (推測) 定義介面，具體實作如 `LanceDBVectorStore` 或 `AzureAISearchVectorStore` 可動態切換。
    *   `llm`: 不同的 LLM 提供者 (OpenAI, Mock) 實作統一介面。
3.  **Factory Pattern (工廠模式)**: `create_pipeline_config.py` 與 `create_graphrag_config.py` 暗示了配置物件與管線實例的建立採用了工廠方法。
4.  **Adapter Pattern (轉接器模式)**: `graphrag.llm` 充當了外部 LLM API 的轉接器，封裝了重試、錯誤處理與標準化輸入輸出。
5.  **Domain-Driven Design (DDD) 元素**: `graphrag.model` 中定義了 `Document`, `CommunityReport`, `Covariate` 等領域物件，反映了系統的核心業務邏輯。
