// GraphRAG API 服務
const API_BASE_URL = 'http://localhost:8000';

class GraphRAGAPI {
  // 全域搜尋
  static async globalSearch(query) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分鐘超時
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/search/global`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`搜尋失敗 (${response.status}): ${errorData.detail || response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('搜尋超時（5分鐘），地端模型處理時間過長');
      }
      throw error;
    }
  }

  // 本地搜尋
  static async localSearch(query) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分鐘超時
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/search/local`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`本地搜尋失敗 (${response.status}): ${errorData.detail || response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('本地搜尋超時（5分鐘），請檢查 LMStudio 嵌入模型狀態');
      }
      throw error;
    }
  }

  // 獲取文件列表
  static async getFiles() {
    const response = await fetch(`${API_BASE_URL}/api/files`);
    
    if (!response.ok) {
      throw new Error(`獲取文件失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 上傳文件
  static async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`上傳失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 獲取搜尋建議
  static async getSearchSuggestions() {
    const response = await fetch(`${API_BASE_URL}/api/search/suggestions`);
    
    if (!response.ok) {
      throw new Error(`獲取搜尋建議失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 獲取圖譜數據
  static async getGraphData() {
    const response = await fetch(`${API_BASE_URL}/api/graph/data`);
    
    if (!response.ok) {
      throw new Error(`獲取圖譜數據失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 開始索引
  static async startIndexing() {
    const response = await fetch(`${API_BASE_URL}/api/indexing/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`開始索引失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 獲取索引狀態
  static async getIndexingStatus() {
    const response = await fetch(`${API_BASE_URL}/api/indexing/status`);
    
    if (!response.ok) {
      throw new Error(`獲取索引狀態失敗: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 健康檢查
  static async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/`, { 
        method: 'GET',
        timeout: 5000 
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export default GraphRAGAPI;
