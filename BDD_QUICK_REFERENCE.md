# GraphRAG BDD 實作快速參考

## 🎯 5 個 Scenario 實作位置速查

| Scenario | 組件名稱 | 檔案位置 | 集成位置 | API 端點 |
|----------|----------|----------|----------|----------|
| 1️⃣ 動態分析文本 | SearchResultCard | App.jsx:244-358 | 搜尋結果 | `/api/statistics` |
| 2️⃣ 社群分析面板 | CommunityAnalysisPanel | App.jsx:362-476 | Graph:1542 | `/api/communities` |
| 3️⃣ 完整統計數據 | StatisticsPanel | App.jsx:480-574 | Graph:1545 | `/api/statistics` |
| 4️⃣ 實體類型分布 | EntityTypeDistribution | App.jsx:576-693 | Graph:1549 | `/api/entity-types` |
| 5️⃣ 關係權重排行 | RelationshipWeightRanking | App.jsx:695-790 | Graph:1550 | `/api/relationships/top` |

## 📡 API 端點摘要

```
GET /api/communities         - 社群分析數據
GET /api/statistics          - 完整統計數據
GET /api/entity-types        - 實體類型分布
GET /api/relationships/top   - 關係權重排行
```

## 🔍 快速驗證命令

```bash
# 檢查語法
grep -n "const.*Panel\|const.*Distribution\|const.*Ranking" graphrag-ui/frontend/src/App.jsx

# 檢查集成
grep -n "CommunityAnalysisPanel\|StatisticsPanel\|EntityTypeDistribution\|RelationshipWeightRanking" graphrag-ui/frontend/src/App.jsx

# 測試編譯
cd graphrag-ui/frontend && npm run build

# 啟動開發服務器
cd graphrag-ui/frontend && npm run dev
```

## ✅ 實作檢查清單

### 代碼完整性
- [x] 5 個組件全部定義
- [x] 所有組件正確集成到 Graph 標籤頁
- [x] SearchResultCard 正確修改
- [x] API 服務包含所有方法

### 功能完整性
- [x] 載入狀態 (loading)
- [x] 錯誤處理 (error)
- [x] 空狀態處理 (empty state)
- [x] 數據動態顯示

### UI/UX
- [x] Tailwind CSS 樣式
- [x] 響應式佈局
- [x] 過渡動畫
- [x] 圖標使用
- [x] 顏色一致性

## 🎨 設計 Token 速查

```css
/* 圓角 */
rounded-2xl  /* 主要容器 */
rounded-xl   /* 次要卡片 */
rounded-lg   /* 小元素 */

/* 陰影 */
shadow-sm    /* 輕微陰影 */
shadow-md    /* 中等陰影 */
shadow-2xl   /* 重陰影 */

/* 顏色 */
blue-600     /* 主要藍色 */
slate-900    /* 深灰色 */
emerald-500  /* 成功綠色 */
amber-500    /* 警告黃色 */

/* 字體 */
font-black   /* 極粗 */
font-bold    /* 粗體 */
text-xs      /* 極小 */
text-sm      /* 小 */
text-base    /* 正常 */
```

## 🐛 常見問題排查

| 問題 | 原因 | 解決方案 |
|------|------|----------|
| 組件不顯示 | API 未啟動 | 檢查後端服務 |
| 載入卡住 | API 超時 | 檢查網絡連接 |
| 數據為空 | 未建立索引 | 執行索引構建 |
| 樣式錯誤 | CSS 未編譯 | 重啟開發服務器 |

## 📊 數據格式範例

### GET /api/communities
```json
{
  "communities": [
    {
      "id": "community_1",
      "title": "核心技術社群",
      "summary": "包含主要技術實體...",
      "rank": 1,
      "size": 45,
      "activity": "high"
    }
  ]
}
```

### GET /api/statistics
```json
{
  "total_entities": 102,
  "total_relationships": 287,
  "avg_relationships_per_entity": 2.81,
  "graph_density": 0.0547,
  "max_degree": 15,
  "num_communities": 8,
  "entity_types": {
    "ORGANIZATION": 72,
    "EVENT": 22
  }
}
```

### GET /api/entity-types
```json
{
  "types": [
    {
      "name": "ORGANIZATION",
      "count": 72,
      "percentage": 70.6
    }
  ]
}
```

### GET /api/relationships/top
```json
{
  "relationships": [
    {
      "source": "實體A",
      "target": "實體B",
      "description": "強關聯",
      "weight": 4.0
    }
  ]
}
```

## 🚀 測試流程

1. **編譯測試**
   ```bash
   cd graphrag-ui/frontend
   npm run build
   ```

2. **啟動服務**
   ```bash
   # 終端 1: 後端
   cd graphrag-ui/backend
   uvicorn main:app --reload

   # 終端 2: 前端
   cd graphrag-ui/frontend
   npm run dev
   ```

3. **功能驗證**
   - 訪問 http://localhost:5173
   - 切換到「視覺網絡」標籤
   - 檢查所有新組件是否正確顯示
   - 展開搜尋結果驗證動態數據

## 📝 修改摘要

```
graphrag-ui/frontend/src/App.jsx
├── 修改: SearchResultCard (Line 244-358)
│   └── 添加動態統計數據載入
│
└── 新增: 4 個完整組件
    ├── CommunityAnalysisPanel (Line 362-476)
    ├── StatisticsPanel (Line 480-574)
    ├── EntityTypeDistribution (Line 576-693)
    └── RelationshipWeightRanking (Line 695-790)

總增加: ~500 行代碼
```

## ✨ 關鍵特性

- ✅ 完全動態數據驅動
- ✅ 優雅的載入和錯誤處理
- ✅ 響應式設計
- ✅ 一致的視覺風格
- ✅ 可維護的組件結構

---

**最後更新**: 2026-01-12
**狀態**: ✅ 實作完成，可投入測試
