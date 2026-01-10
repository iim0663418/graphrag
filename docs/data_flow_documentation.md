# GraphRAG 資料流與管線架構文檔 (Data Flow and Pipeline Documentation)

本文件概述了 GraphRAG 系統的核心資料流，涵蓋**索引流程 (Indexing Pipeline)**、**查詢處理 (Query Processing)** 以及**資料轉換工作流 (Data Transformation Workflows)**。

## 1. 索引流程 (Indexing Pipeline)

索引流程負責將非結構化的文本數據轉換為結構化的知識圖譜（Knowledge Graph）及相關的向量索引。此過程通常由 `graphrag.index` 模組驅動。

### 核心階段 (Core Stages)

1.  **輸入載入 (Input Loading)**
    *   從來源（如 CSV, TXT）讀取原始文檔。
    *   **資料流:** `Raw Documents` -> `Input DataFrame`

2.  **文本切分 (Text Splitting/Chunking)**
    *   將長文本切分為較小的文本單元 (Text Units)，以便 LLM 處理。
    *   **資料流:** `Input DataFrame` -> `Text Units`

3.  **元素提取 (Element Extraction)**
    *   **實體與關係提取 (Entity & Relationship Extraction):** 使用 LLM 從文本單元中識別實體（如人物、地點、組織）及其相互關係。
    *   **主張提取 (Claim Extraction):** (可選) 提取與實體相關的事實主張。
    *   **資料流:** `Text Units` -> `Entities`, `Relationships`, `Claims`

4.  **圖譜構建 (Graph Construction)**
    *   將提取的實體與關係整合為圖結構 (NetworkX graph)。
    *   進行實體解析與去重。
    *   **資料流:** `Entities` + `Relationships` -> `Entity Graph`

5.  **社群偵測 (Community Detection)**
    *   使用分層算法 (如 Leiden algorithm) 對圖譜進行分群，識別不同層級的語義社群。
    *   **資料流:** `Entity Graph` -> `Communities (Hierarchy)`

6.  **社群摘要 (Community Summarization)**
    *   針對每個社群生成摘要報告 (Community Reports)，描述該社群的核心主題與見解。
    *   這是 GraphRAG "Global Search" 的基礎。
    *   **資料流:** `Communities` + `Text Units` -> `Community Reports`

7.  **向量嵌入與存儲 (Embedding & Storage)**
    *   為實體描述、社群摘要及原始文本單元生成向量嵌入 (Embeddings)。
    *   將數據存入向量資料庫 (如 LanceDB, Azure AI Search)。
    *   **資料流:** `Text/Reports` -> `Vector Store`

## 2. 查詢處理 (Query Processing)

查詢模組 (`graphrag.query`) 利用預先構建的索引來回答使用者問題。

### 查詢模式 (Query Modes)

#### A. 全域搜尋 (Global Search)
適用於回答關於數據集整體內容的概括性問題 (如 "這些文件主要在討論什麼？")。

1.  **問題分析:** 解析使用者查詢。
2.  **社群篩選:** 選擇特定層級的社群摘要 (通常是較高層級)。
3.  **Map 階段:** 平行處理選定的社群摘要，讓 LLM 針對查詢生成中間答案，並給予評分 (Rating)。
4.  **Reduce 階段:** 聚合評分最高的中間答案，生成最終的綜合回答。
5.  **資料流:** `User Query` -> `Community Reports` -> `Intermediate Answers` -> `Final Answer`

#### B. 局域搜尋 (Local Search)
適用於回答關於特定實體或細節的問題 (如 "誰是 Alice？她與 Bob 有什麼關係？")。

1.  **關鍵字/實體識別:** 從查詢中識別關鍵實體。
2.  **索引檢索:** 在知識圖譜中檢索相關實體、關係、協變量 (Covariates) 及原始文本塊。
3.  **上下文構建:** 將檢索到的相關資訊組合成上下文視窗 (Context Window)。
4.  **答案生成:** LLM 根據上下文生成回答，並附帶引用來源。
5.  **資料流:** `User Query` -> `Vector Search/Graph Traversal` -> `Context` -> `Final Answer`

## 3. 資料轉換工作流 (Data Transformation Workflows)

GraphRAG 的數據處理採用基於 "動詞 (Verbs)" 的工作流架構 (定義於 `graphrag.index.verbs` 與 `workflows`)。

*   **Verbs (動詞):** 定義單一的資料轉換操作，例如 `chunk`, `extract_entities`, `cluster_graph`。
*   **Workflows (工作流):** 定義一系列串聯的動詞，形成完整的處理管線。
*   **擴展性:** 開發者可以通過定義新的動詞或配置 YAML 檔案來自定義資料流，例如替換嵌入模型、調整分群算法或增加自定義的提取邏輯。

---
*註：本文件基於 GraphRAG 架構生成，具體實作細節可能依版本配置 (`settings.yaml`) 而異。*
