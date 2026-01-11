# GraphRAG UI 實作路線圖

> **基於**: 95 小時優化方案 | **時程**: 8 週 | **更新**: 2026-01-11

## 🎯 **實作策略**

### **核心原則**
```yaml
最小可行產品 (MVP): 優先核心功能，後續迭代
API 優先: 先建立穩定後端，再開發前端
漸進式開發: 每週可交付功能模組
風險控制: 關鍵路徑優先，降低技術債務
```

### **技術決策**
```yaml
後端架構: FastAPI + GraphRAG API 包裝
前端架構: 完整沿用最終設計 (React 18 + TypeScript + D3.js)
狀態管理: Zustand (輕量) + React Query (服務端)
視覺化: 完整沿用最終設計的 D3.js 圖譜引擎
部署方式: 本地開發 → Docker 容器化
```

---

## 📅 **Week 1-2: 核心 API 層** (25h)

### **Day 1-2: 專案架構搭建** (8h)
```bash
# 1. 建立專案結構
mkdir -p graphrag-ui/{backend,frontend}
cd graphrag-ui/backend

# 2. Python 環境設定
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pandas pydantic

# 3. 基礎 FastAPI 應用
touch main.py config.py models.py
```

**核心檔案**:
- `main.py`: FastAPI 應用入口
- `config.py`: 配置管理
- `models.py`: Pydantic 資料模型
- `api/`: API 路由模組

### **Day 3-4: GraphRAG API 整合** (6h)
```python
# api/query.py - 查詢 API 包裝
from graphrag.query import api as graphrag_api

@app.post("/api/search/global")
async def global_search(request: SearchRequest):
    result = await graphrag_api.global_search(
        config=get_graphrag_config(),
        query=request.query,
        # ... 其他參數
    )
    return {"response": result, "status": "success"}

@app.post("/api/search/local")  
async def local_search(request: SearchRequest):
    # 類似實現
```

**關鍵任務**:
- GraphRAG 配置載入
- 查詢 API 包裝 (global/local)
- 串流回應處理
- 錯誤處理機制

### **Day 5-6: 資料適配器** (5h)
```python
# adapters/parquet_adapter.py
from graphrag.query.indexer_adapters import read_indexer_entities

class ParquetDataAdapter:
    def get_entities(self) -> List[EntityModel]:
        entities = read_indexer_entities(nodes_df, entities_df, community_level)
        return [EntityModel.from_graphrag(e) for e in entities]
    
    def get_relationships(self) -> List[RelationshipModel]:
        # 類似實現
```

**關鍵任務**:
- Parquet 檔案讀取
- GraphRAG 資料格式轉換
- UI 友善的資料結構
- 快取機制整合

### **Day 7-8: 檔案管理 API** (4h)
```python
# api/files.py
@app.post("/api/files/upload")
async def upload_file(file: UploadFile):
    # 檔案驗證與儲存
    
@app.get("/api/files")
async def list_files():
    # 檔案列表
    
@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    # 檔案刪除
```

### **Day 9-10: 配置與測試** (2h)
- 環境變數配置
- API 測試腳本
- 基礎錯誤處理

---

## 📅 **Week 3-4: 基礎 UI 層** (30h)

### **Day 11-12: React 應用架構** (8h)
```bash
# 前端專案初始化 - 基於最終設計
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install @tanstack/react-query zustand lucide-react tailwindcss d3

# 完整沿用最終設計的專案結構
src/
├── components/
│   ├── DocumentManager.tsx      # 完整沿用最終設計
│   ├── IndexManager.tsx         # 完整沿用最終設計  
│   ├── SearchInterface.tsx      # 完整沿用最終設計
│   ├── KnowledgeGraph.tsx       # 完整沿用最終設計
│   └── shared/                  # 共用組件
├── stores/
│   └── appStore.ts             # 完整沿用 Zustand 狀態管理
├── services/                   # API 服務層
└── App.tsx                     # 完整沿用最終設計主應用
```

**核心任務**:
- 直接複製 `docs/前端雛形/最終設計` 的完整程式碼
- 保持所有 UI 組件、樣式、互動邏輯不變
- 僅調整 API 服務層對接後端

### **Day 13-14: 最終設計程式碼移植** (7h)
```typescript
// 直接使用最終設計的完整實現
// App.tsx - 完整沿用
export default function App() {
  const activeTab = useAppStore(s => s.activeTab);
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const files = useAppStore(s => s.files);
  const deleteFile = useAppStore(s => s.deleteFile);

  // ... 完整保留最終設計的所有邏輯
  return (
    <div className="flex h-screen bg-[#f8fafc] font-sans text-slate-900 overflow-hidden">
      {/* 完整保留最終設計的 JSX 結構 */}
    </div>
  );
}
```

**關鍵任務**:
- 複製最終設計的所有 React 組件
- 保持 Zustand 狀態管理邏輯
- 保持 Tailwind CSS 樣式系統
- 保持 Lucide React 圖示使用

### **Day 15-16: API 服務層對接** (6h)
```typescript
// services/api.ts - 唯一需要開發的新模組
export class GraphRAGAPI {
  private baseURL = 'http://localhost:8000/api';

  async globalSearch(query: string): Promise<SearchResult[]> {
    const response = await fetch(`${this.baseURL}/search/global`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    return response.json();
  }

  async localSearch(query: string): Promise<SearchResult[]> {
    // 類似實現
  }

  async uploadFile(file: File): Promise<FileUploadResult> {
    // 檔案上傳實現
  }

  async startIndexing(): Promise<IndexingStatus> {
    // 索引啟動實現
  }
}
```

**關鍵任務**:
- 建立 API 服務層對接後端
- 修改最終設計中的模擬資料為真實 API 呼叫
- 保持所有 UI 行為與視覺效果不變

### **Day 17-18: 狀態管理整合** (6h)
```typescript
// stores/appStore.ts - 基於最終設計，僅調整資料來源
const useAppStore = createStore((set, get) => ({
  // 完整保留最終設計的狀態結構
  activeTab: 'documents',
  files: [],
  isIndexing: false,
  indexProgress: 0,
  toast: null,
  
  // 修改方法以呼叫真實 API
  addFile: async (file: File) => {
    const api = new GraphRAGAPI();
    const result = await api.uploadFile(file);
    // 更新狀態邏輯保持不變
  },
  
  // 其他方法類似調整
}));
```

### **Day 19-20: D3.js 圖譜整合** (3h)
```typescript
// components/KnowledgeGraph.tsx - 完整沿用最終設計
const KnowledgeGraph = () => {
  const containerRef = useRef();
  const svgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  
  // 完整保留最終設計的 D3.js 實現
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;
    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    
    // 完整保留最終設計的圖譜渲染邏輯
    // 僅調整資料來源為真實 API
  }, [dimensions]);
  
  // 完整保留最終設計的 JSX 結構
  return (
    <div className="flex h-[640px] space-x-10">
      {/* 完整保留最終設計的佈局 */}
    </div>
  );
};
```

---

## 📅 **Week 5-6: 圖譜視覺化** (25h)

### **Day 21-22: 最終設計 D3.js 引擎移植** (10h)
```typescript
// 完整沿用 docs/前端雛形/最終設計 的 KnowledgeGraph 組件
// components/KnowledgeGraph.tsx - 零修改移植
const KnowledgeGraph = () => {
  const containerRef = useRef();
  const svgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 600 });

  // 完整保留最終設計的響應式邏輯
  useLayoutEffect(() => {
    const observer = new ResizeObserver(entries => {
      if (!entries[0]) return;
      setDimensions(prev => ({ ...prev, width: entries[0].contentRect.width }));
    });
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 完整保留最終設計的 D3.js 實現
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;
    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // 完整保留最終設計的資料結構與渲染邏輯
    const data = {
      nodes: [
        { id: 'GraphRAG', group: 1, val: 32 }, 
        { id: 'React 18', group: 2, val: 20 },
        // ... 完整保留最終設計的節點資料
      ],
      links: [
        { source: 'GraphRAG', target: 'Vector DB' },
        // ... 完整保留最終設計的連結資料
      ]
    };

    // 完整保留最終設計的 D3.js 力導向佈局
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id(d => d.id).distance(200))
      .force("charge", d3.forceManyBody().strength(-800))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // 完整保留最終設計的渲染與互動邏輯
    // ... (所有 D3.js 程式碼保持不變)
  }, [dimensions]);

  // 完整保留最終設計的 JSX 結構與樣式
  return (
    <div className="flex h-[640px] space-x-10">
      <div ref={containerRef} className="flex-1 bg-white rounded-[50px] border border-slate-100 shadow-2xl relative overflow-hidden">
        <svg ref={svgRef} className="w-full h-full" />
        {/* 完整保留最終設計的所有 UI 元素 */}
      </div>
      <div className="w-[400px] bg-white rounded-[50px] border border-slate-100 shadow-2xl p-12 overflow-y-auto">
        {/* 完整保留最終設計的節點詳情面板 */}
      </div>
    </div>
  );
};
```

**關鍵任務**:
- 零修改移植最終設計的完整 D3.js 實現
- 保持所有視覺效果、動畫、互動邏輯
- 僅調整資料來源為真實 GraphRAG 資料

### **Day 23-24: 搜尋介面完整移植** (8h)
```typescript
// 完整沿用最終設計的 AccessibleSearch 組件
const AccessibleSearch = () => {
  const [query, setQuery] = useState('');
  const [type, setType] = useState('global');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);

  // 完整保留最終設計的建議查詢
  const suggestions = [
    "分析文檔中的核心論點",
    "提取相關市場趨勢數據", 
    "總結實體間的關聯結構",
    "檢查技術架構的完整性"
  ];

  // 修改搜尋邏輯以呼叫真實 API
  const handleSearch = async (e, q = query) => {
    if (e) e.preventDefault();
    if (!q) return;
    setIsSearching(true);
    setResults([]);
    
    try {
      const api = new GraphRAGAPI();
      const searchResults = type === 'global' 
        ? await api.globalSearch(q)
        : await api.localSearch(q);
      setResults(searchResults);
    } finally {
      setIsSearching(false);
    }
  };

  // 完整保留最終設計的 JSX 結構與樣式
  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in duration-700">
      {/* 完整保留最終設計的所有 UI 元素 */}
    </div>
  );
};
```

### **Day 25-26: 索引管理介面移植** (4h)
```typescript
// 完整沿用最終設計的 EmotionalIndexingProgress 組件
const EmotionalIndexingProgress = () => {
  const isIndexing = useAppStore(s => s.isIndexing);
  const progress = useAppStore(s => s.indexProgress);
  // ... 完整保留最終設計的所有狀態與邏輯

  // 修改啟動邏輯以呼叫真實 API
  const start = async () => {
    setShowWarning(false);
    setIndexing(true);
    setIndexProgress(0);
    
    try {
      const api = new GraphRAGAPI();
      await api.startIndexing();
      // 監控進度的邏輯
    } catch (error) {
      // 錯誤處理
    }
  };

  // 完整保留最終設計的 JSX 結構與樣式
  return (
    <div className="max-w-2xl mx-auto mt-12 p-12 bg-white rounded-[40px] border border-slate-100 shadow-2xl">
      {/* 完整保留最終設計的所有 UI 元素 */}
    </div>
  );
};
```

### **Day 27-28: 檔案管理介面移植** (3h)
```typescript
// 完整沿用最終設計的檔案管理組件
const EnhancedFileUpload = () => {
  const addFile = useAppStore(s => s.addFile);
  const [dragState, setDragState] = useState('idle');
  
  // 修改檔案處理邏輯以呼叫真實 API
  const handleFileDrop = async (e) => {
    e.preventDefault();
    setDragState('dropping');
    
    try {
      const file = e.dataTransfer.files[0];
      const api = new GraphRAGAPI();
      await api.uploadFile(file);
      addFile(file.name);
    } finally {
      setTimeout(() => setDragState('idle'), 500);
    }
  };

  // 完整保留最終設計的 JSX 結構與樣式
  return (
    <div 
      onDragOver={(e) => { e.preventDefault(); setDragState('hover'); }}
      onDragLeave={() => setDragState('idle')}
      onDrop={handleFileDrop}
      className={`border-2 border-dashed rounded-[40px] p-20 transition-all flex flex-col items-center justify-center cursor-pointer group ${
        dragState === 'hover' ? 'border-blue-600 bg-white scale-[1.01] shadow-2xl' : 'border-slate-200 bg-transparent hover:border-blue-400'
      }`}
    >
      {/* 完整保留最終設計的所有 UI 元素 */}
    </div>
  );
};
```

---

## 📅 **Week 7-8: 優化整合** (15h)

### **Day 29-30: 效能優化** (6h)
```typescript
// 虛擬化渲染
const VirtualizedGraph = () => {
  const [visibleNodes, setVisibleNodes] = useState([]);
  
  const updateVisibleNodes = useCallback((viewport) => {
    const visible = nodes.filter(node => 
      isInViewport(node, viewport)
    );
    setVisibleNodes(visible);
  }, [nodes]);
  
  return <D3Graph nodes={visibleNodes} />;
};
```

### **Day 31-32: 用戶體驗優化** (4h)
- 載入狀態優化
- 錯誤提示改進
- 響應式設計調整
- 無障礙功能

### **Day 33-34: 測試與部署** (2h)
```bash
# Docker 容器化
# Dockerfile
FROM node:18-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim as backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/frontend/dist ./static

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Day 35-36: 文檔完善** (1h)
- README.md 更新
- API 文檔生成
- 部署指南

### **Day 37-40: 緩衝時間** (2h)
- Bug 修復
- 效能調優
- 功能完善

---

## 🔧 **開發工具與環境**

### **後端開發**
```bash
# 開發環境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 啟動開發服務器
uvicorn main:app --reload --port 8000
```

### **前端開發**
```bash
# 開發環境
npm install
npm run dev

# 建置生產版本
npm run build
```

### **整合測試**
```bash
# 同時啟動前後端
npm run dev:all

# API 測試
curl -X POST http://localhost:8000/api/search/global \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

---

## 📊 **里程碑檢查點**

### **Week 2 檢查點**
- [ ] FastAPI 服務正常運行
- [ ] GraphRAG API 整合完成
- [ ] 基礎查詢功能可用
- [ ] 檔案上傳功能正常

### **Week 4 檢查點**
- [ ] 最終設計完整移植完成
- [ ] 所有 UI 組件視覺效果一致
- [ ] 前後端 API 通信正常
- [ ] Zustand 狀態管理穩定運行
- [ ] D3.js 圖譜渲染正常

### **Week 6 檢查點**
- [ ] 最終設計的圖譜視覺化完整運行
- [ ] 所有節點互動功能保持一致
- [ ] 搜尋結果高亮效果正常
- [ ] 最終設計的所有動畫效果正常
- [ ] 效能表現符合最終設計標準

### **Week 8 檢查點**
- [ ] 系統整體穩定運行
- [ ] 效能優化完成
- [ ] 部署流程驗證
- [ ] 文檔完整

---

## 🚨 **風險控制**

### **技術風險**
- **D3.js 複雜度**: 預留額外 4h 緩衝時間
- **GraphRAG API 變更**: 使用穩定版本，避免 dev 分支
- **效能瓶頸**: 提前實施虛擬化渲染

### **時程風險**
- **關鍵路徑**: API 層 → UI 層 → 圖譜層
- **並行開發**: 前後端可部分並行
- **緩衝時間**: 每階段預留 10% 緩衝

### **品質風險**
- **測試策略**: 每週末整合測試
- **程式碼審查**: 關鍵模組雙人檢查
- **效能監控**: 持續效能基準測試

---

## 📈 **成功指標**

### **功能指標**
- 檔案上傳成功率 > 95%
- 查詢回應時間 < 3s
- 圖譜渲染時間 < 5s
- 系統穩定運行 > 24h

### **體驗指標**
- UI 回應時間 < 200ms
- 圖譜互動流暢度 > 30fps
- 錯誤恢復時間 < 10s
- 學習曲線 < 10min

### **技術指標**
- 程式碼覆蓋率 > 80%
- API 可用性 > 99%
- 記憶體使用 < 2GB
- CPU 使用率 < 50%
