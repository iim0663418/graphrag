# GraphRAG 本地化專案

> **注意**: 這是 Microsoft GraphRAG 的 fork 版本，專注於本地化解決方案。本項目獨立維護，不會合併回原倉庫。

## 🎯 本 Fork 的特色

### 核心修復
- ✅ **解決無限循環問題**: 修復 GraphRAG 實體提取的致命缺陷
- ✅ **LMStudio 完整集成**: 實現零成本本地運行
- ✅ **生產就緒**: 14個 parquet 文件驗證成功

### 與原項目的差異
- **問題修復**: 原項目存在實體提取無限循環問題
- **本地化**: 專注於本地模型集成，無需外部 API
- **企業友好**: 完全數據隱私保護

## 🚀 快速開始

1. **克隆本 fork**
   ```bash
   git clone https://github.com/iim0663418/graphrag.git
   cd graphrag
   ```

2. **應用修復**
   ```bash
   python scripts/fix_graphrag_loop.py
   ```

3. **運行示例**
   ```bash
   cd examples/local_deployment
   python -m graphrag.index --root .
   ```

## 📋 版本說明

- **v1.0.0-local**: 完整本地化解決方案
- **基於**: Microsoft GraphRAG (原始版本)
- **授權**: MIT (與原項目相同)

## ⚠️ 重要聲明

本項目為獨立 fork，專注於本地化功能：
- 遵循原項目 MIT 授權
- 不會提交 PR 回原倉庫
- 獨立維護和演進
- 歡迎社群使用和貢獻

---

詳細文檔請參考 `FORK_MAINTENANCE.md`

## 📁 專案結構

```
graphrag/
├── docs/                          # 文檔
│   ├── local-graphrag-design.md   # 本地化設計方案
│   ├── lmstudio-sdk-guide.md      # LMStudio SDK 指南
│   └── ui-framework-analysis.md   # UI 框架分析
├── examples/                      # 示例
│   └── local_deployment/          # 本地部署示例
│       ├── input/                 # 輸入文件
│       ├── output/                # 索引輸出
│       ├── settings.yaml          # GraphRAG 配置
│       └── .env                   # 環境變量
├── scripts/                       # 工具腳本
│   ├── fix_graphrag_loop.py       # 修復無限循環問題
│   ├── diagnose.py                # 診斷工具
│   └── final_test.py              # 完整測試腳本
├── graphrag_local/                # 本地化適配器
│   ├── adapters/                  # LMStudio 適配器
│   ├── config/                    # 配置管理
│   └── optimization/              # 性能優化
└── graphrag/                      # 原始 GraphRAG 庫
```

## 🚀 快速開始

1. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

2. **啟動 LMStudio**
   - 加載 qwen/qwen3-vl-8b 模型
   - 加載 nomic-embed-text-v1.5 嵌入模型
   - 啟動本地服務器 (http://localhost:1234)

3. **修復循環問題**
   ```bash
   python scripts/fix_graphrag_loop.py
   ```

4. **運行索引**
   ```bash
   cd examples/local_deployment
   python -m graphrag.index --root .
   ```

## ✅ 主要成果

- **零成本運行**: 完全本地化，無需外部 API
- **循環問題修復**: 解決了 GraphRAG 實體提取無限循環
- **完整集成**: LMStudio + GraphRAG 無縫對接
- **性能優化**: 緩存和批處理優化

## 🔧 核心修復

修復了 GraphRAG 在使用本地模型時的無限循環問題：
- 問題：模型對 "YES/NO" 問題總是回答 "YES"
- 解決：實施零收益終止機制
- 效果：索引可以正常完成，生成完整知識圖譜

## 📊 測試結果

成功生成 14 個 parquet 文件，包含：
- 實體提取結果
- 關係映射
- 社群檢測
- 知識圖譜構建

## 🎯 下一步

1. 集成 Kotaemon UI 框架
2. 添加更多本地模型支持
3. 優化大文檔處理性能
4. 實現增量索引更新
