# GraphRAG Local 部署指南

## 🚀 快速部署測試

### 1. 環境準備

```bash
# 確保 Python 3.10+
python --version

# 安裝必要依賴
pip install lmstudio graphrag pyyaml

# 檢查 GraphRAG 安裝
graphrag --help
```

### 2. LMStudio 設置

1. **下載並啟動 LMStudio**
   - 訪問 [lmstudio.ai](https://lmstudio.ai) 下載
   - 啟動應用程式

2. **下載推薦模型**
   ```bash
   # 聊天模型（選擇其一）
   lms get qwen/qwen3-4b-2507
   lms get microsoft/Phi-3-mini-4k-instruct-gguf
   
   # 嵌入模型
   lms get nomic-ai/nomic-embed-text-v1.5
   ```

3. **載入模型**
   - 在 LMStudio 中載入一個聊天模型
   - 載入嵌入模型
   - 確保模型狀態為 "Loaded"

### 3. 運行部署測試

```bash
# 執行自動化測試
python deploy_test.py
```

### 4. 手動測試步驟

如果自動測試有問題，可以手動執行：

```bash
# 1. 創建測試目錄
mkdir graphrag_test
cd graphrag_test

# 2. 初始化 GraphRAG
graphrag init --root .

# 3. 創建測試配置
cat > settings.yaml << EOF
llm:
  type: lmstudio_chat
  model: "qwen/qwen3-4b-2507"
  model_supports_json: true
  max_tokens: 4000
  temperature: 0.1

embeddings:
  llm:
    type: lmstudio_embedding
    model: "nomic-embed-text-v1.5"
    batch_size: 16

chunks:
  size: 300
  overlap: 100

input:
  type: file
  file_type: text
  base_dir: input
  file_encoding: utf-8
  file_pattern: ".*\\.txt$"
EOF

# 4. 創建測試數據
mkdir -p input
cat > input/test.txt << EOF
GraphRAG 是一個知識圖譜檢索增強生成系統。
它能夠從文本中提取實體和關係，建構知識圖譜。
主要功能包括實體提取、關係建構、社群檢測等。
EOF

# 5. 運行索引
graphrag index --root .

# 6. 測試查詢
graphrag query --method global --query "什麼是 GraphRAG？"
graphrag query --method local --query "GraphRAG 的功能有哪些？"
```

## 🔧 故障排除

### 常見問題

1. **LMStudio 連接失敗**
   ```
   錯誤: LM Studio is not reachable
   解決: 確保 LMStudio 應用程式已啟動並載入模型
   ```

2. **模型未找到**
   ```
   錯誤: Model not found
   解決: 檢查模型名稱是否正確，確保模型已載入
   ```

3. **GraphRAG 命令不存在**
   ```
   錯誤: graphrag: command not found
   解決: pip install graphrag
   ```

4. **配置文件錯誤**
   ```
   錯誤: Invalid configuration
   解決: 檢查 settings.yaml 格式，確保縮排正確
   ```

### 調試模式

```bash
# 啟用詳細日誌
export GRAPHRAG_LOG_LEVEL=DEBUG

# 運行測試
python deploy_test.py
```

### 檢查日誌

```bash
# 查看索引日誌
ls -la output/*/artifacts/

# 查看錯誤日誌
tail -f output/*/logs/*.log
```

## 📊 預期結果

### 成功指標

1. **環境檢查** ✅
   - Python 3.10+
   - 所有依賴已安裝
   - LMStudio SDK 可用

2. **LMStudio 連接** ✅
   - 客戶端連接成功
   - 模型已載入

3. **GraphRAG 整合** ✅
   - 本地適配器導入成功
   - 工廠函數可用

4. **索引處理** ✅
   - 實體提取完成
   - 關係建構完成
   - 輸出文件生成

5. **查詢測試** ✅
   - 全域查詢返回結果
   - 局域查詢返回結果

### 輸出文件

成功後應該看到：
```
test_deployment/
├── input/
│   └── graphrag_intro.txt
├── output/
│   └── artifacts/
│       ├── entities.parquet
│       ├── relationships.parquet
│       ├── communities.parquet
│       └── community_reports.parquet
├── cache/
└── settings.yaml
```

## 🎯 下一步

部署測試成功後：

1. **性能調優**
   - 調整批次大小
   - 優化快取設置
   - 監控資源使用

2. **生產部署**
   - 配置持久化存儲
   - 設置監控告警
   - 建立備份策略

3. **功能擴展**
   - 整合更多模型
   - 添加 UI 介面
   - 實作 API 服務

## 📞 支援

如遇問題：
1. 檢查 `deploy_test.py` 輸出
2. 查看 GraphRAG 日誌
3. 確認 LMStudio 狀態
4. 驗證配置文件格式
