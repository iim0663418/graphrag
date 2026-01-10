# GraphRAG 本地化增強版 🚀

> **🔥 這是 Microsoft GraphRAG 的增強 Fork 版本** - 專門解決原項目的無限循環問題，實現真正可用的本地化 GraphRAG 解決方案

[![Fork](https://img.shields.io/badge/Fork-microsoft%2Fgraphrag-blue)](https://github.com/microsoft/graphrag)
[![Local](https://img.shields.io/badge/Local-GraphRAG-green)](https://github.com/iim0663418/graphrag)
[![LMStudio](https://img.shields.io/badge/LMStudio-Integration-orange)](https://lmstudio.ai/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/iim0663418/graphrag/releases)

## 🎯 為什麼選擇這個 Fork？

### ❌ 原項目問題
- **無限循環缺陷**: 實體提取陷入死循環，索引無法完成
- **高昂成本**: 依賴 OpenAI API，費用昂貴  
- **數據隱私**: 企業數據需要發送到外部服務

### ✅ 本 Fork 解決方案
- **🔧 修復循環問題**: 實施零收益終止機制，徹底解決無限循環
- **💰 零成本運行**: 完整 LMStudio 集成，無需任何 API 費用
- **🔒 數據隱私**: 100% 本地處理，企業數據不出本地
- **📊 驗證成功**: 實際生成 14 個 parquet 文件，證明完整可用

## 🚀 核心差異對比

| 功能 | 原項目 | 本 Fork |
|------|--------|---------|
| 實體提取 | ❌ 無限循環 | ✅ 智能終止 |
| 成本 | 💸 OpenAI API | 💰 完全免費 |
| 數據隱私 | ⚠️ 外部傳輸 | 🔒 本地處理 |
| 部署難度 | 🔧 複雜配置 | 🎯 一鍵部署 |
| 生產就緒 | ⚠️ 不穩定 | ✅ 已驗證 |

## 🛠️ 快速開始

### 1. 克隆並修復
```bash
git clone https://github.com/iim0663418/graphrag.git
cd graphrag
python scripts/fix_graphrag_loop.py  # 一鍵修復循環問題
```

### 2. 啟動 LMStudio
- 加載 `qwen/qwen3-vl-8b` (LLM)
- 加載 `nomic-embed-text-v1.5` (Embedding)  
- 啟動服務: http://localhost:1234

### 3. 運行索引
```bash
cd examples/local_deployment
python -m graphrag.index --root .
```

### 4. 驗證結果
```bash
# 應該看到 14 個 parquet 文件
ls output/*.parquet
```

---

## 📚 原項目信息

👉 [Use the GraphRAG Accelerator solution](https://github.com/Azure-Samples/graphrag-accelerator) <br/>
👉 [Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)<br/>
👉 [Read the docs](https://microsoft.github.io/graphrag)<br/>
👉 [GraphRAG Arxiv](https://arxiv.org/pdf/2404.16130)

<div align="left">
  <a href="https://pypi.org/project/graphrag/">
    <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/graphrag">
  </a>
  <a href="https://pypi.org/project/graphrag/">
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/graphrag">
  </a>
  <a href="https://github.com/microsoft/graphrag/issues">
    <img alt="GitHub Issues" src="https://img.shields.io/github/issues/microsoft/graphrag">
  </a>
  <a href="https://github.com/microsoft/graphrag/discussions">
    <img alt="GitHub Discussions" src="https://img.shields.io/github/discussions/microsoft/graphrag">
  </a>
</div>

## Overview

The GraphRAG project is a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using the power of LLMs.

To learn more about GraphRAG and how it can be used to enhance your LLM's ability to reason about your private data, please visit the <a href="https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/" target="_blank">Microsoft Research Blog Post.</a>

## Quickstart

To get started with the GraphRAG system we recommend trying the [Solution Accelerator](https://github.com/Azure-Samples/graphrag-accelerator) package. This provides a user-friendly end-to-end experience with Azure resources.

## Repository Guidance

This repository presents a methodology for using knowledge graph memory structures to enhance LLM outputs. Please note that the provided code serves as a demonstration and is not an officially supported Microsoft offering.

⚠️ *Warning: GraphRAG indexing can be an expensive operation, please read all of the documentation to understand the process and costs involved, and start small.*

## Diving Deeper

- To learn about our contribution guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md)
- To start developing _GraphRAG_, see [DEVELOPING.md](./DEVELOPING.md)
- Join the conversation and provide feedback in the [GitHub Discussions tab!](https://github.com/microsoft/graphrag/discussions)

## Prompt Tuning

Using _GraphRAG_ with your data out of the box may not yield the best possible results.
We strongly recommend to fine-tune your prompts following the [Prompt Tuning Guide](https://microsoft.github.io/graphrag/posts/prompt_tuning/overview/) in our documentation.

## Responsible AI FAQ

See [RAI_TRANSPARENCY.md](./RAI_TRANSPARENCY.md)

- [What is GraphRAG?](./RAI_TRANSPARENCY.md#what-is-graphrag)
- [What can GraphRAG do?](./RAI_TRANSPARENCY.md#what-can-graphrag-do)
- [What are GraphRAG’s intended use(s)?](./RAI_TRANSPARENCY.md#what-are-graphrags-intended-uses)
- [How was GraphRAG evaluated? What metrics are used to measure performance?](./RAI_TRANSPARENCY.md#how-was-graphrag-evaluated-what-metrics-are-used-to-measure-performance)
- [What are the limitations of GraphRAG? How can users minimize the impact of GraphRAG’s limitations when using the system?](./RAI_TRANSPARENCY.md#what-are-the-limitations-of-graphrag-how-can-users-minimize-the-impact-of-graphrags-limitations-when-using-the-system)
- [What operational factors and settings allow for effective and responsible use of GraphRAG?](./RAI_TRANSPARENCY.md#what-operational-factors-and-settings-allow-for-effective-and-responsible-use-of-graphrag)

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

## Privacy

[Microsoft Privacy Statement](https://privacy.microsoft.com/en-us/privacystatement)
