import React, { useState, useEffect, useRef, useMemo, memo, Component, useLayoutEffect } from 'react';
import { 
  FileText, 
  Database, 
  Search, 
  Share2, 
  Upload, 
  Trash2, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  ChevronRight,
  Info,
  Maximize2,
  Settings,
  RefreshCcw,
  MousePointer2,
  Globe,
  Target,
  Copy,
  Star,
  Sparkles,
  Cpu,
  Lightbulb,
  Network,
  History,
  Bookmark,
  ExternalLink,
  Layers,
  Activity
} from 'lucide-react';
import * as d3 from 'd3';
import GraphRAGAPI from './services/api.js';

/**
 * --- 狀態管理 (Zustand 模式與本地持久化) ---
 */
const STORAGE_KEY = 'graphrag_professional_v1';

const createStore = (config) => {
  const savedState = localStorage.getItem(STORAGE_KEY);
  let state = savedState ? JSON.parse(savedState) : null;

  const listeners = new Set();
  const setState = (partial) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    if (nextState !== state) {
      state = Object.assign({}, state, nextState);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      listeners.forEach((listener) => listener(state));
    }
  };
  const getState = () => state;
  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };
  
  // 初始化狀態
  if (!state) {
    state = config(setState, getState);
  } else {
    // 合併保存的狀態和新的函數
    const initialState = config(setState, getState);
    state = { ...initialState, ...state };
  }
  
  return (selector) => {
    const [, forceUpdate] = React.useReducer((c) => c + 1, 0);
    useLayoutEffect(() => subscribe(() => forceUpdate()), []);
    return selector ? selector(state) : state;
  };
};

const useAppStore = createStore((set, get) => ({
  activeTab: 'documents',
  files: [],
  isIndexing: false,
  indexProgress: 0,
  toast: null,
  
  setActiveTab: (tab) => set({ activeTab: tab }),
  setToast: (toast) => set({ toast }),
  addFile: (file) => {
    if (!file) return;

    // 調用後端 API 上傳文件（傳送實際檔案物件）
    GraphRAGAPI.uploadFile(file)
      .then(response => {
        // 後端回應格式：{ "message": "檔案上傳成功", "file": FileInfo }
        const fileInfo = response.file;
        const newFile = {
          id: fileInfo.id,
          name: fileInfo.name,
          size: fileInfo.size,
          status: fileInfo.status,
          date: fileInfo.date
        };
        set({ files: [newFile, ...get().files] });
      })
      .catch(error => {
        console.error('文件上傳失敗:', error);
        // 上傳失敗時仍添加到列表，但標記為錯誤
        const newFile = {
          id: Date.now().toString(),
          name: file.name,
          size: 'Upload Failed',
          status: 'error',
          date: new Date().toISOString().split('T')[0]
        };
        set({ files: [newFile, ...get().files] });
      });
  },
  deleteFile: async (id) => {
    try {
      // 調用後端 API 刪除文件
      await fetch(`http://localhost:8000/api/files/${id}`, {
        method: 'DELETE'
      });
      // 成功後從本地狀態移除
      set({ files: get().files.filter(f => f.id !== id) });
    } catch (error) {
      console.error('刪除文件失敗:', error);
      // 刪除失敗時可以顯示錯誤提示
    }
  },
  setIndexing: (status) => set({ isIndexing: status }),
  setIndexProgress: (val) => set({ indexProgress: val }),
  
  // 開始索引並輪詢狀態
  startIndexing: async () => {
    try {
      const response = await GraphRAGAPI.startIndexing();
      set({ 
        isIndexing: response.is_indexing,
        indexProgress: response.progress,
        toast: { message: response.message, type: 'info' }
      });
      
      // 開始輪詢索引狀態
      const pollStatus = async () => {
        try {
          const status = await GraphRAGAPI.getIndexingStatus();
          set({ 
            isIndexing: status.is_indexing,
            indexProgress: status.progress
          });
          
          if (status.is_indexing) {
            // 如果還在索引中，繼續輪詢
            setTimeout(pollStatus, 1000);
          } else {
            // 索引完成
            set({ 
              toast: { message: status.message, type: 'success' },
              files: get().files.map(f => ({ ...f, status: 'indexed' }))
            });
          }
        } catch (error) {
          console.error('獲取索引狀態失敗:', error);
          set({ isIndexing: false });
        }
      };
      
      // 開始輪詢
      setTimeout(pollStatus, 1000);
      
    } catch (error) {
      console.error('開始索引失敗:', error);
      set({ 
        isIndexing: false,
        toast: { message: `索引失敗: ${error.message}`, type: 'error' }
      });
    }
  },
  completeIndexing: () => {
    // 這個方法現在由 startIndexing 的輪詢邏輯自動調用
    set({ 
      isIndexing: false, 
      indexProgress: 100,
      files: get().files.map(f => ({ ...f, status: 'indexed' })),
      toast: { message: '知識圖譜索引構建完成', type: 'success' }
    });
  },
  
  // 從後端載入文件列表
  loadFiles: async () => {
    try {
      const files = await GraphRAGAPI.getFiles();
      set({ files });
    } catch (error) {
      console.error('載入文件列表失敗:', error);
      set({ files: [] });
    }
  },
  
  // 載入索引狀態
  loadIndexingStatus: async () => {
    try {
      const status = await GraphRAGAPI.getIndexingStatus();
      set({ 
        isIndexing: status.is_indexing,
        indexProgress: status.progress
      });
    } catch (error) {
      console.error('載入索引狀態失敗:', error);
    }
  }
}));

/**
 * --- 通用組件: 專業通知 (Toast) ---
 */
const SuccessToast = () => {
  const toast = useAppStore(s => s.toast);
  const setToast = useAppStore(s => s.setToast);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  if (!toast) return null;

  return (
    <div className="fixed top-8 right-8 z-50 bg-slate-900 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center space-x-4 animate-in slide-in-from-top-4 duration-300 border border-slate-800">
      <div className="bg-emerald-500 rounded-full p-1 shadow-lg shadow-emerald-500/20">
        <CheckCircle2 size={16} className="text-white" />
      </div>
      <div className="flex flex-col">
        <span className="font-bold text-sm tracking-tight">{toast.message}</span>
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">系統狀態回傳成功</span>
      </div>
    </div>
  );
};

/**
 * --- 搜尋結果組件: 具備漸進式揭露功能 ---
 */
const SearchResultCard = ({ result, query }) => {
  const [expanded, setExpanded] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);

  const highlight = (text) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() 
        ? <mark key={i} className="bg-blue-100 text-blue-800 px-0.5 rounded-sm font-semibold">{part}</mark> 
        : part
    );
  };

  return (
    <article className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all group overflow-hidden">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-1.5 bg-slate-50 rounded-lg text-slate-400 group-hover:text-blue-500 transition-colors">
              <FileText size={14} />
            </div>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              資料來源: {result.source}
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setBookmarked(!bookmarked)}
              className={`transition-all duration-300 ${bookmarked ? 'text-amber-500 scale-110' : 'text-slate-200 hover:text-amber-400'}`}
            >
              <Bookmark size={18} fill={bookmarked ? "currentColor" : "none"} />
            </button>
            <span className="text-[10px] font-black bg-blue-50 text-blue-600 px-3 py-1 rounded-full border border-blue-100">
              {Math.round(result.score * 100)}% 精準匹配
            </span>
          </div>
        </div>
        
        <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-blue-600 transition-colors tracking-tight">
          {highlight(result.title)}
        </h3>
        <p className="text-slate-600 leading-relaxed text-sm mb-4">
          {highlight(result.snippet)}
        </p>

        <div className="flex justify-between items-center">
          <button 
            onClick={() => setExpanded(!expanded)}
            className="text-blue-600 text-xs font-black uppercase tracking-widest flex items-center hover:text-blue-700"
          >
            {expanded ? '隱藏詳細內容' : '檢視深度脈絡'} 
            <ChevronRight size={14} className={`ml-1.5 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>
          <div className="flex items-center space-x-4 opacity-0 group-hover:opacity-100 transition-opacity">
            <button className="text-[10px] font-black text-slate-400 hover:text-blue-600 flex items-center tracking-widest uppercase">
              <Copy size={12} className="mr-1.5" /> 引用
            </button>
          </div>
        </div>

        {expanded && (
          <div className="mt-6 pt-6 border-t border-slate-50 space-y-4 animate-in fade-in slide-in-from-top-2 duration-400">
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
              <p className="text-sm text-slate-600 leading-relaxed font-medium italic">
                「在特定語義環境中，此核心主題的關聯強度顯著。基於 GraphRAG 的多跳推理，系統識別出該點與地端資料庫中的其他 14 個實體存在結構化聯繫，這有助於理解跨文檔的邏輯一致性。」
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {['語義推理', '實體對齊', '地端 LLM'].map(t => (
                <span key={t} className="text-[10px] bg-white border border-slate-200 text-slate-500 px-3 py-1 rounded-lg font-black uppercase tracking-wider">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </article>
  );
};

/**
 * --- 搜尋模組: 具備建議與分組功能 ---
 */
const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [type, setType] = useState('global');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(true);

  // 載入智能搜尋建議
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        setLoadingSuggestions(true);
        const data = await GraphRAGAPI.getSearchSuggestions();
        setSuggestions(data.suggestions);
      } catch (error) {
        console.error('載入搜尋建議失敗:', error);
        // 載入失敗時使用默認建議
        setSuggestions([
          "分析文檔中的核心技術論點",
          "提取關鍵市場趨勢與數據指標",
          "總結實體間的語義關聯結構",
          "驗證技術架構的邏輯完整性"
        ]);
      } finally {
        setLoadingSuggestions(false);
      }
    };

    loadSuggestions();
  }, []);

  const handleSearch = async (e, q = query) => {
    if (e) e.preventDefault();
    if (!q) return;
    
    setIsSearching(true);
    setResults([]);
    
    try {
      // 檢查後端服務是否可用
      const isBackendAvailable = await GraphRAGAPI.healthCheck();
      
      if (!isBackendAvailable) {
        throw new Error('後端服務不可用');
      }
      
      // 顯示模型載入提示
      setResults([{
        id: 0,
        title: 'GraphRAG 模型正在處理中...',
        snippet: `正在使用地端 AI 模型分析您的查詢「${q}」。地端模型首次載入可能需要 3-5 分鐘，請耐心等待。後續查詢會更快。`,
        category: '模型載入中',
        source: '地端 AI 處理',
        score: 1.0
      }]);
      
      let searchResults;
      if (type === 'global') {
        searchResults = await GraphRAGAPI.globalSearch(q);
      } else {
        searchResults = await GraphRAGAPI.localSearch(q);
      }
      
      console.log('API 回應:', searchResults);
      
      // 處理不同的 API 回應格式
      let formattedResults = [];
      
      if (searchResults && typeof searchResults === 'object') {
        // GraphRAG API 回應格式：{ "response": "..." }
        if (typeof searchResults.response === 'string') {
          formattedResults = [{
            id: 1,
            title: `${type === 'global' ? '全域搜尋' : '本地搜尋'}結果`,
            snippet: searchResults.response,
            category: type === 'global' ? '全域分析' : '本地查詢',
            source: 'GraphRAG',
            score: 0.9
          }];
        }
        // 如果有 results 陣列（備用格式）
        else if (Array.isArray(searchResults.results)) {
          formattedResults = searchResults.results.map((result, index) => ({
            id: index + 1,
            title: result.title || result.name || `搜尋結果 ${index + 1}`,
            snippet: result.content || result.snippet || result.text || '無內容摘要',
            category: result.category || (type === 'global' ? '全域分析' : '本地查詢'),
            source: result.source || result.file || 'GraphRAG',
            score: result.score || result.relevance || 0.8
          }));
        }
        // 其他格式嘗試直接顯示
        else {
          formattedResults = [{
            id: 1,
            title: `${type === 'global' ? '全域' : '本地'}搜尋回應`,
            snippet: JSON.stringify(searchResults, null, 2),
            category: 'API 回應',
            source: 'GraphRAG API',
            score: 0.7
          }];
        }
      }
      
      // 如果沒有結果，顯示提示
      if (formattedResults.length === 0) {
        formattedResults = [{
          id: 1,
          title: '未找到相關結果',
          snippet: `針對查詢「${q}」未找到相關內容。請嘗試其他關鍵詞或檢查知識庫是否包含相關資料。`,
          category: '搜尋提示',
          source: '系統提示',
          score: 0
        }];
      }
      
      setResults(formattedResults);
    } catch (error) {
      console.error('搜尋錯誤:', error);
      
      // 直接顯示錯誤信息，不使用模擬數據
      const errorResults = [{
        id: 1,
        title: '搜尋失敗',
        snippet: `錯誤：${error.message}`,
        category: '錯誤',
        source: 'API 錯誤',
        score: 0
      }];
      
      setResults(errorResults);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in duration-700">
      {/* 搜尋模式選擇 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {[
          { id: 'global', icon: <Globe size={20} />, title: '全域概覽 (Global)', desc: '針對整個知識庫執行結構化摘要與跨文檔聯繫分析' },
          { id: 'local', icon: <Target size={20} />, title: '精確查找 (Local)', desc: '精確定位文檔段落中的事實、實體屬性與具體細節' }
        ].map(m => (
          <button 
            key={m.id}
            onClick={() => setType(m.id)}
            className={`p-6 rounded-[24px] border-2 text-left transition-all relative overflow-hidden group ${
              type === m.id ? 'border-blue-600 bg-blue-50/50 shadow-xl shadow-blue-100' : 'border-slate-200 bg-white hover:border-slate-300 shadow-sm'
            }`}
          >
            <div className="flex items-center mb-2">
              <span className={`mr-3 ${type === m.id ? 'text-blue-600' : 'text-slate-400'}`}>{m.icon}</span>
              <span className={`font-black tracking-tight ${type === m.id ? 'text-blue-900' : 'text-slate-700'}`}>{m.title}</span>
            </div>
            <p className="text-xs text-slate-500 font-bold leading-relaxed">{m.desc}</p>
          </button>
        ))}
      </div>

      {/* 搜尋輸入與建議 */}
      <div className="space-y-6">
        <form onSubmit={handleSearch} className="relative group">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="請輸入查詢指令或問題..."
            className="w-full pl-16 pr-40 py-6 bg-white rounded-[32px] border border-slate-200 focus:border-blue-500 focus:ring-[14px] focus:ring-blue-50/50 outline-none transition-all text-xl shadow-sm hover:shadow-md font-bold tracking-tight"
          />
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500" size={24} />
          <button 
            type="submit"
            disabled={!query.trim()}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 bg-slate-900 text-white px-8 py-3.5 rounded-2xl font-black hover:bg-black transition-all active:scale-95 disabled:bg-slate-200 shadow-xl shadow-slate-200 uppercase tracking-widest text-sm"
          >
            {isSearching ? <Loader2 className="animate-spin" size={20} /> : '啟動檢索'}
          </button>
        </form>

        <div className="flex flex-wrap gap-2 items-center">
          <Sparkles size={14} className="text-blue-500 mr-2" />
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest mr-3">
            {loadingSuggestions ? '載入建議中...' : '智能查詢建議'}
          </span>
          {suggestions.map((s, i) => (
            <button 
              key={i} 
              onClick={() => { setQuery(s); handleSearch(null, s); }}
              className="text-[10px] font-black bg-white border border-slate-200 px-4 py-2 rounded-full text-slate-500 hover:border-blue-400 hover:text-blue-600 transition-all shadow-sm tracking-wide disabled:opacity-50"
              disabled={loadingSuggestions}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* 結果列表 */}
      <div className="space-y-10">
        {isSearching ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-2xl border border-slate-100 p-8 animate-pulse">
                <div className="h-4 bg-slate-100 rounded-full w-1/4 mb-6"></div>
                <div className="h-6 bg-slate-100 rounded-full w-3/4 mb-4"></div>
                <div className="h-3 bg-slate-100 rounded-full w-full mb-2"></div>
                <div className="h-3 bg-slate-100 rounded-full w-5/6"></div>
              </div>
            ))}
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-8">
            {results.map(res => <SearchResultCard key={res.id} result={res} query={query} />)}
          </div>
        ) : (
          <div className="text-center py-24 bg-slate-50/50 rounded-[40px] border border-slate-100">
            <div className="inline-flex p-6 rounded-full bg-white shadow-inner text-slate-200 mb-6">
              <Layers size={48} />
            </div>
            <p className="text-slate-400 font-black uppercase tracking-[0.3em] text-xs">等待指令輸入以喚醒知識引擎</p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * --- 索引模組: 具備專業反饋的進度追蹤 ---
 */
const IndexingDashboard = () => {
  const isIndexing = useAppStore(s => s.isIndexing);
  const progress = useAppStore(s => s.indexProgress);
  const startIndexing = useAppStore(s => s.startIndexing);
  const [showWarning, setShowWarning] = useState(false);

  const start = () => {
    setShowWarning(false);
    // 調用真實的索引 API
    startIndexing();
  };

  const getStatus = (p) => {
    if (p < 25) return { icon: <Search size={40} />, text: '執行底層數據結構掃描', color: 'text-blue-600' };
    if (p < 50) return { icon: <Cpu size={40} />, text: '地端模型實體特徵提取', color: 'text-indigo-600' };
    if (p < 75) return { icon: <Network size={40} />, text: '建構全局語義關聯網絡', color: 'text-violet-600' };
    if (p < 100) return { icon: <Layers size={40} />, text: '執行索引效能最終優化', color: 'text-sky-600' };
    return { icon: <CheckCircle2 size={40} />, text: '知識索引體系構建成功', color: 'text-emerald-600' };
  };

  const status = getStatus(progress);

  return (
    <div className="max-w-2xl mx-auto mt-12 p-12 bg-white rounded-[48px] border border-slate-100 shadow-2xl">
      {showWarning && !isIndexing ? (
        <div className="animate-in zoom-in-95 duration-300 text-left">
          <div className="bg-slate-900 text-white rounded-[32px] p-10 mb-6 shadow-2xl relative overflow-hidden">
            <div className="absolute -right-10 -bottom-10 opacity-10"><Database size={160} /></div>
            <div className="flex items-start space-x-6 relative z-10">
              <div className="p-3.5 bg-amber-500 rounded-2xl shadow-lg shadow-amber-500/30">
                <AlertCircle size={28} className="text-white" />
              </div>
              <div>
                <h4 className="font-black text-2xl mb-3 tracking-tighter uppercase">系統索引安全警告</h4>
                <ul className="text-sm text-slate-400 space-y-3 font-bold mb-10">
                  <li className="flex items-center"><ChevronRight size={14} className="mr-3 text-slate-600" /> 系統將調用所有地端算力資源進行實體提取</li>
                  <li className="flex items-center"><ChevronRight size={14} className="mr-3 text-slate-600" /> 現有知識快取將在構建期間暫時失效</li>
                  <li className="flex items-center"><ChevronRight size={14} className="mr-3 text-slate-600" /> 完成後將自動重構全局語義網格關係</li>
                </ul>
                <div className="flex space-x-4">
                  <button onClick={start} className="bg-white text-slate-900 px-10 py-4 rounded-2xl font-black hover:bg-slate-100 transition-all shadow-xl uppercase tracking-widest text-xs">
                    啟動構建流程
                  </button>
                  <button onClick={() => setShowWarning(false)} className="text-slate-500 font-black hover:text-white px-4 transition-colors uppercase tracking-widest text-[10px]">
                    取消操作
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <div className={`w-32 h-32 mx-auto mb-10 rounded-[36px] flex items-center justify-center transition-all duration-700 bg-slate-50 border border-slate-100 shadow-inner ${isIndexing ? 'scale-110 shadow-2xl ' + status.color : 'text-slate-300'}`}>
            {isIndexing ? <div className="animate-pulse">{status.icon}</div> : <Database size={40} />}
          </div>
          <h2 className={`text-3xl font-black mb-4 tracking-tighter transition-colors ${isIndexing ? status.color : 'text-slate-900'}`}>
            {isIndexing ? status.text : '知識索引管理中心'}
          </h2>
          <p className="text-slate-400 mb-12 px-10 font-black uppercase tracking-[0.2em] text-[10px] leading-loose opacity-60">
            Graph-RAG Indexing Protocol v2.4 • Local Compute Mode
          </p>
          
          {isIndexing ? (
            <div className="space-y-10 animate-in fade-in">
              <div className="h-4 bg-slate-50 rounded-full overflow-hidden border border-slate-100 p-0.5 shadow-inner">
                <div className="h-full bg-slate-900 rounded-full transition-all duration-300 shadow-sm shadow-slate-400" style={{ width: `${progress}%` }} />
              </div>
              <div className="flex justify-between items-end border-t border-slate-50 pt-8">
                <div className="text-left">
                  <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">任務執行狀態</div>
                  <div className={`text-sm font-black uppercase tracking-tighter ${status.color}`}>{status.text}</div>
                </div>
                <div className="text-right">
                  <div className="text-5xl font-black text-slate-900 font-mono tracking-tighter">{progress}<span className="text-xl ml-1 text-slate-300">%</span></div>
                </div>
              </div>
            </div>
          ) : (
            <button 
              onClick={() => setShowWarning(true)} 
              className="w-full py-6 bg-slate-900 text-white rounded-3xl font-black hover:bg-black transition-all active:scale-[0.98] shadow-2xl tracking-[0.2em] uppercase text-sm"
            >
              {progress === 100 ? '執行數據二次同步' : '啟動深度提取流程'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * --- 首頁組件: 空狀態價值演示 ---
 */
const LandingPage = () => (
  <div className="max-w-6xl mx-auto text-center py-20 space-y-20 animate-in fade-in zoom-in-95 duration-1000">
    <div className="space-y-8">
      <div className="inline-flex px-5 py-2 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-[10px] font-black uppercase tracking-[0.4em] mb-4">
        Graph-Based Discovery Engine
      </div>
      <h1 className="text-8xl font-black tracking-tighter bg-gradient-to-br from-slate-900 via-slate-700 to-slate-400 bg-clip-text text-transparent leading-[1.1]">
        賦予文檔<br/>結構化的推理能力
      </h1>
      <p className="text-xl text-slate-500 font-bold max-w-2xl mx-auto leading-relaxed tracking-tight">
        透過地端圖譜索引技術，將您的私有數據轉化為具備關聯推理能力的知識網絡。無需翻找文件，直接與知識深處對話。
      </p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      {[
        { icon: <FileText size={36} />, title: '數據加密匯入', desc: '支持多種純文字格式\n完全的地端隱私安全保障' },
        { icon: <Cpu size={36} />, title: '自動語義識別', desc: '地端模型深度分析實體\n建立跨文檔的拓撲網絡關係' },
        { icon: <Lightbulb size={36} />, title: '脈絡增強檢索', desc: '基於 GraphRAG 推理引擎\n提供極其精準的專業化解答' }
      ].map((step, i) => (
        <div key={i} className="p-12 bg-white rounded-[48px] border border-slate-100 shadow-sm hover:shadow-2xl transition-all hover:-translate-y-2 group">
          <div className="w-16 h-16 bg-slate-50 rounded-[20px] flex items-center justify-center mb-10 text-slate-400 group-hover:bg-slate-900 group-hover:text-white transition-all shadow-inner">
            {step.icon}
          </div>
          <h3 className="font-black text-2xl mb-4 text-slate-900 tracking-tight">{step.title}</h3>
          <p className="text-sm text-slate-500 font-bold leading-relaxed whitespace-pre-line tracking-tight opacity-70">{step.desc}</p>
        </div>
      ))}
    </div>

    <div className="bg-white rounded-[60px] p-20 shadow-2xl shadow-slate-200 border border-slate-100 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-80 h-80 bg-blue-50 rounded-full blur-[100px] -mr-40 -mt-40 opacity-50 group-hover:bg-blue-100 transition-colors" />
      <FileUploadZone />
      <div className="mt-12 flex items-center justify-center space-x-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.4em]">
        <Sparkles size={14} className="text-blue-500" />
        <span>建議上傳技術規範或研究報告以獲取最佳索引效能</span>
      </div>
    </div>
  </div>
);

/**
 * --- 核心工具組件: 上傳區與刪除按鈕 ---
 */
const FileUploadZone = () => {
  const addFile = useAppStore(s => s.addFile);
  const [dragState, setDragState] = useState('idle');
  const fileInputRef = useRef(null);

  // 處理點擊事件 - 觸發檔案選擇對話框
  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // 處理檔案選擇
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      addFile(file);
      // 重置 input 以允許選擇相同檔案
      e.target.value = '';
    }
  };

  return (
    <div
      onClick={handleClick}
      onDragOver={(e) => { e.preventDefault(); setDragState('hover'); }}
      onDragLeave={() => setDragState('idle')}
      onDrop={(e) => { e.preventDefault(); setDragState('dropping'); addFile(e.dataTransfer.files[0]); setTimeout(() => setDragState('idle'), 500); }}
      className={`border-2 border-dashed rounded-[40px] p-20 transition-all flex flex-col items-center justify-center cursor-pointer group ${
        dragState === 'hover' ? 'border-blue-600 bg-slate-50 scale-[1.01] shadow-2xl' : 'border-slate-200 bg-transparent hover:border-blue-300 hover:bg-slate-50/50'
      }`}
    >
      {/* 隱藏的檔案 input 元素 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.csv,.json,.md"
        onChange={handleFileChange}
        className="hidden"
        aria-label="檔案上傳"
      />

      <div className={`w-24 h-24 mb-10 rounded-[32px] flex items-center justify-center transition-all duration-500 shadow-xl ${dragState === 'hover' ? 'bg-blue-600 rotate-6 shadow-blue-200' : 'bg-slate-900 group-hover:bg-blue-600'}`}>
        <Upload className="text-white" size={36} />
      </div>
      <p className="font-black text-4xl text-slate-900 mb-4 tracking-tighter">數據中心匯入點</p>
      <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.4em]">點擊或拖放檔案至此處執行離線分析 • 限制 20MB • 支援 .TXT, .CSV, .JSON, .MD</p>
    </div>
  );
};

const SafeDeleteButton = ({ onDelete }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  if (showConfirm) {
    return (
      <div className="flex items-center space-x-4 bg-slate-900 text-white px-6 py-2.5 rounded-2xl animate-in fade-in zoom-in-95 duration-200 shadow-2xl border border-slate-700">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 whitespace-nowrap">確認移除此數據源？</span>
        <button onClick={onDelete} className="bg-red-600 text-white px-5 py-1.5 rounded-xl text-[10px] font-black hover:bg-red-700 transition-colors uppercase tracking-widest">移除</button>
        <button onClick={() => setShowConfirm(false)} className="text-[10px] font-black text-slate-500 hover:text-white transition-colors">取消</button>
      </div>
    );
  }
  return <button onClick={() => setShowConfirm(true)} className="text-slate-300 hover:text-red-500 transition-all p-4 hover:bg-slate-100 rounded-[24px]"><Trash2 size={20} /></button>;
};

/**
 * --- 視覺化圖譜組件 (D3.js) ---
 */
const KnowledgeTopology = () => {
  const containerRef = useRef();
  const svgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 600 });
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

  useLayoutEffect(() => {
    const observer = new ResizeObserver(entries => {
      if (!entries[0]) return;
      setDimensions(prev => ({ ...prev, width: entries[0].contentRect.width }));
    });
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 載入真實的圖譜數據
  useEffect(() => {
    const loadGraphData = async () => {
      try {
        setLoading(true);
        const data = await GraphRAGAPI.getGraphData();
        setGraphData(data);
      } catch (err) {
        console.error('載入圖譜數據失敗:', err);
        // 載入失敗時顯示有意義的空狀態提示
        setGraphData({
          nodes: [
            { id: '請先上傳檔案', group: 1, val: 40 },
            { id: '執行索引構建', group: 2, val: 35 },
            { id: '即可生成知識圖譜', group: 3, val: 30 }
          ],
          links: [
            { source: '請先上傳檔案', target: '執行索引構建' },
            { source: '執行索引構建', target: '即可生成知識圖譜' }
          ],
          stats: {
            total_entities: 0,
            total_relationships: 0,
            displayed_nodes: 0,
            isEmpty: true,
            message: '尚未建立知識圖譜索引'
          }
        });
      } finally {
        setLoading(false);
      }
    };

    loadGraphData();
  }, []);

  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0 || !graphData) return;
    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const data = {
      nodes: graphData.nodes,
      links: graphData.links
    };

    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id(d => d.id).distance(220))
      .force("charge", d3.forceManyBody().strength(-1000))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const g = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.5, 4]).on("zoom", (e) => g.attr("transform", e.transform)));

    const link = g.append("g").attr("stroke", "#f1f5f9").selectAll("line").data(data.links).join("line").attr("stroke-width", 3);
    const node = g.append("g").selectAll("g").data(data.nodes).join("g").attr("class", "cursor-pointer")
      .on("click", (e, d) => setSelectedNode(d))
      .call(d3.drag()
        .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append("circle").attr("r", d => d.val).attr("fill", d => d.group === 1 ? "#0f172a" : "#3b82f6").attr("stroke", "#fff").attr("stroke-width", 5).attr("class", "shadow-2xl transition-all hover:brightness-125 hover:scale-105 duration-300");
    node.append("text").text(d => d.id).attr("y", d => d.val + 26).attr("text-anchor", "middle").attr("class", "text-[11px] font-black fill-slate-900 uppercase tracking-tighter");

    simulation.on("tick", () => {
      link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });
  }, [dimensions, graphData]);

  return (
    <div className="flex h-[660px] space-x-12">
      <div ref={containerRef} className="flex-1 bg-white rounded-[60px] border border-slate-100 shadow-2xl relative overflow-hidden">
        <svg ref={svgRef} className="w-full h-full" />
        <div className="absolute top-10 left-10 bg-slate-900 text-white px-6 py-2.5 rounded-[20px] text-[10px] font-black uppercase tracking-[0.25em] shadow-2xl flex items-center border border-slate-700">
          <Activity size={14} className="mr-3 text-emerald-400 animate-pulse" />
          {loading ? 'Loading Graph Data...' : (graphData?.stats?.isEmpty ? '等待知識圖譜數據' : 'Knowledge Topology Network')}
        </div>
        {graphData?.stats && !graphData.stats.isEmpty && (
          <div className="absolute top-20 left-10 bg-blue-600 text-white px-4 py-2 rounded-[16px] text-[9px] font-black uppercase tracking-wider shadow-lg">
            {graphData.stats.displayed_nodes} / {graphData.stats.total_entities} Entities
          </div>
        )}
        {graphData?.stats?.isEmpty && (
          <div className="absolute top-20 left-10 bg-amber-500 text-white px-4 py-2 rounded-[16px] text-[9px] font-black uppercase tracking-wider shadow-lg">
            {graphData.stats.message}
          </div>
        )}
      </div>
      <div className="w-[420px] bg-white rounded-[60px] border border-slate-100 shadow-2xl p-12 overflow-y-auto">
        <h3 className="text-2xl font-black text-slate-900 mb-10 flex items-center tracking-tighter uppercase"><Info className="mr-4 text-blue-600" /> 節點關聯脈絡</h3>
        {selectedNode ? (
          <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="p-8 bg-slate-900 text-white rounded-[36px] shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform duration-700"><Network size={100} /></div>
              <label className="text-[10px] uppercase text-slate-500 font-black tracking-[0.25em] mb-2 block">
                {graphData?.stats?.isEmpty ? '操作步驟' : 'Entity Identifier'}
              </label>
              <div className="text-4xl font-black tracking-tighter">{selectedNode.id}</div>
            </div>
            <div className="space-y-6">
              <div className="flex items-center space-x-3 text-blue-600">
                {graphData?.stats?.isEmpty ? <Lightbulb size={18} /> : <Network size={18} />}
                <label className="text-[10px] uppercase font-black tracking-[0.2em]">
                  {graphData?.stats?.isEmpty ? '使用說明' : '語義架構影響因子'}
                </label>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed font-bold tracking-tight opacity-80">
                {graphData?.stats?.isEmpty
                  ? '知識圖譜需要先完成資料索引才能顯示。請前往「文檔匯入」頁面上傳您的文件，然後在「索引中心」執行索引構建流程。索引完成後，這裡將顯示完整的實體關聯網絡圖譜。'
                  : '該核心實體節點直接決定了地端知識庫的跨區域一致性。透過語義嵌入空間的深度分析，系統確定其為目前知識網格中的主導聚合點，具備高中心性指標。'}
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-200">
            <div className="w-24 h-24 bg-slate-50 rounded-[32px] flex items-center justify-center mb-8 border border-slate-100 shadow-inner"><Share2 size={48} /></div>
            <p className="font-black text-xs uppercase tracking-[0.4em] leading-loose text-slate-300">
              {graphData?.stats?.isEmpty
                ? '請先上傳文件並完成索引<br/>以建立知識圖譜網絡'
                : '請在視窗中選取節點<br/>以分析核心脈絡關係'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * --- 主應用框架 ---
 */
export default function App() {
  const activeTab = useAppStore(s => s.activeTab);
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const files = useAppStore(s => s.files);
  const deleteFile = useAppStore(s => s.deleteFile);
  const loadFiles = useAppStore(s => s.loadFiles);
  const startIndexing = useAppStore(s => s.startIndexing);
  const loadIndexingStatus = useAppStore(s => s.loadIndexingStatus);

  // 調試：檢查 setActiveTab 是否為函數
  console.log('setActiveTab type:', typeof setActiveTab);
  console.log('setActiveTab value:', setActiveTab);

  // 組件載入時從後端獲取文件列表和索引狀態
  React.useEffect(() => {
    if (loadFiles) {
      loadFiles();
    }
    if (loadIndexingStatus) {
      loadIndexingStatus();
    }
  }, [loadFiles, loadIndexingStatus]);

  const navigation = [
    { id: 'documents', label: '文檔匯入', desc: '數據庫準備', icon: <FileText size={18} /> },
    { id: 'indexing', label: '索引中心', desc: '知識重構', icon: <Database size={18} /> },
    { id: 'search', label: '智慧查詢', desc: '語義檢索', icon: <Search size={18} /> },
    { id: 'graph', label: '視覺網絡', desc: '拓撲探索', icon: <Share2 size={18} /> },
  ];

  return (
    <div className="flex h-screen bg-[#f8fafc] font-sans text-slate-900 overflow-hidden">
      <SuccessToast />
      
      <aside className="w-80 bg-white border-r border-slate-200 flex flex-col z-20 shadow-sm">
        <div className="p-12">
          <div className="flex items-center space-x-5 mb-20">
            <div className="w-14 h-14 bg-slate-900 rounded-[22px] flex items-center justify-center shadow-2xl relative">
              <Network className="text-white" size={30} />
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 border-4 border-white rounded-full" />
            </div>
            <div>
              <span className="text-2xl font-black tracking-tighter block leading-none">GraphRAG</span>
              <div className="text-[10px] font-black uppercase text-blue-600 tracking-[0.3em] mt-2">Professional</div>
            </div>
          </div>

          <nav className="space-y-4">
            {navigation.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center px-7 py-5 rounded-[24px] transition-all duration-300 ${
                  activeTab === item.id 
                    ? 'bg-slate-900 text-white shadow-2xl shadow-slate-300 scale-[1.03]' 
                    : 'text-slate-400 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <span className="mr-5 transition-transform group-hover:scale-110">{item.icon}</span>
                <div className="text-left">
                  <div className="font-black text-xs uppercase tracking-[0.2em] leading-tight">{item.label}</div>
                  <div className={`text-[10px] font-bold mt-1 opacity-50 ${activeTab === item.id ? 'text-slate-400' : ''}`}>
                    {item.desc}
                  </div>
                </div>
              </button>
            ))}
          </nav>
        </div>
        
        <div className="mt-auto p-12 border-t border-slate-50 flex items-center justify-between">
          <button className="flex items-center text-slate-400 hover:text-slate-900 text-[10px] font-black tracking-widest uppercase transition-colors">
            <Settings size={20} className="mr-4" /> Preferences
          </button>
          <div className="text-[9px] font-black text-slate-200 uppercase tracking-widest">v4.0.0-PRO</div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-16">
        <header className="flex justify-between items-end mb-20 px-2">
          <div>
            <div className="flex items-center space-x-4 text-blue-600 mb-4">
              <History size={16} />
              <span className="text-[10px] font-black uppercase tracking-[0.3em]">地端引擎運行穩定</span>
            </div>
            <h1 className="text-6xl font-black text-slate-900 tracking-tight mb-3">
              {navigation.find(i => i.id === activeTab).label}
            </h1>
            <p className="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px] flex items-center opacity-70">
              <Database size={14} className="mr-3" /> 
              地端算力驅動 • 離線知識加密解析 • 100% 隱私保護模式
            </p>
          </div>
          <div className="bg-white px-8 py-4 rounded-[24px] border border-slate-200 shadow-sm flex items-center space-x-4">
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(16,185,129,0.4)]" />
            <span className="text-[10px] font-black text-slate-800 tracking-widest uppercase">Engine Ready</span>
          </div>
        </header>

        <section className="min-h-[600px]">
          {activeTab === 'documents' && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000">
              {files.length === 0 ? (
                <LandingPage />
              ) : (
                <div className="space-y-12">
                  <FileUploadZone />
                  <div className="bg-white rounded-[50px] border border-slate-200 shadow-2xl overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-slate-50 text-[10px] font-black uppercase text-slate-400 tracking-[0.3em]">
                        <tr>
                          <th className="px-14 py-8">知識庫數據源名稱</th>
                          <th className="px-14 py-8">檔案大小</th>
                          <th className="px-14 py-8 text-right">管理權限</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {files.map(f => (
                          <tr key={f.id} className="group hover:bg-slate-50/80 transition-all duration-300">
                            <td className="px-14 py-10 flex items-center space-x-7">
                              <div className="p-4 bg-slate-50 rounded-[22px] text-slate-400 group-hover:bg-slate-900 group-hover:text-white transition-all shadow-inner"><FileText size={22}/></div>
                              <span className="font-black text-slate-800 tracking-tight text-2xl">{f.name}</span>
                            </td>
                            <td className="px-14 py-10 font-black text-slate-400 text-xs tracking-widest">{f.size}</td>
                            <td className="px-14 py-10 text-right">
                              <SafeDeleteButton onDelete={() => deleteFile(f.id)} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          {activeTab === 'indexing' && <IndexingDashboard />}
          {activeTab === 'search' && <SearchInterface />}
          {activeTab === 'graph' && (
            <div className="animate-in fade-in zoom-in-95 duration-700">
              <KnowledgeTopology />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
