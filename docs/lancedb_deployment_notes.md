# LanceDB 部署方式記錄

## 📝 記錄時間
2025-12-29 16:20

## 🗄️ LanceDB 在 GraphRAG 中的部署模式

### 核心特點
- **嵌入式資料庫** - 無需獨立部署服務
- **零配置** - 隨 GraphRAG 套件自動安裝
- **檔案型儲存** - 資料存於本地檔案系統
- **自動管理** - GraphRAG 自動處理所有操作

### 配置方式
```yaml
# settings.yaml
vector_store:
  type: lancedb
  db_uri: "./lancedb"
  table_name: "vectors"
  metric: "cosine"
```

### 檔案結構
```
project/
├── settings.yaml
└── lancedb/              # 自動建立
    ├── vectors.lance     # 向量資料
    └── _versions/        # 版本控制
```

### 使用流程
1. `pip install graphrag` - LanceDB 自動包含
2. `graphrag index` - 自動建立資料庫和寫入資料
3. `graphrag query` - 自動從 LanceDB 檢索

### 適用場景
- 開發和測試環境
- 小規模部署
- 需要資料本地化的場景
- 不想依賴雲端服務的情況

### 與 Azure AI Search 對比
| 項目 | LanceDB | Azure AI Search |
|------|---------|----------------|
| 部署 | 本地嵌入 | 雲端服務 |
| 配置 | 極簡 | 複雜 |
| 成本 | 免費 | 付費 |
| 擴展 | 單機限制 | 雲端擴展 |
