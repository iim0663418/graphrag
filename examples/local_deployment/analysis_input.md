# GraphRAG 實體提取無限循環問題分析

## 問題描述
GraphRAG 在使用 LMStudio 本地模型進行實體提取時出現無限循環，具體表現為：
- 模型不斷收到 "MANY entities and relationships were missed..." 提示
- qwen/qwen3-vl-8b 模型對 "Answer YES | NO" 總是回答 "YES"
- 導致索引過程無法完成

## 技術細節
1. GraphRAG 源碼位置： 第 163-174 行
2. 問題邏輯：使用  詢問是否需要繼續提取實體
3. 默認 ，但循環邏輯依賴模型準確判斷

## 外部驗證
- GDELT Project 研究證實這是 LLM 實體提取的普遍問題
- 微小的文本變化就能觸發無限循環
- 影響多種 LLM 模型，不限於特定實現

## 當前解決方案
設置  可以避免循環，但可能影響提取質量

## 需要分析的問題
1. 如何修復 GraphRAG 的循環邏輯？
2. 如何改進 LOOP_PROMPT 設計？
3. 如何針對不同模型優化提示？
4. 是否有更好的替代方案？

請提供詳細的修正實作方案。
