import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import asyncio
from datetime import datetime
import logging
import shutil
import subprocess

from services.graphrag_service import GraphRagService

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="GraphRAG UI API", version="1.0.0")

# 初始化 GraphRAG 服務
graphrag_service: Optional[GraphRagService] = None

# 檔案上傳配置
BACKEND_ROOT = Path(__file__).parent
INPUT_DIR = BACKEND_ROOT / "input"
OUTPUT_DIR = BACKEND_ROOT / "output"
# GraphRAG 僅支援 .txt 和 .csv 格式 (參考 graphrag/config/enums.py InputFileType)
ALLOWED_EXTENSIONS = {".txt", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 確保目錄存在
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 GraphRAG 服務。"""
    global graphrag_service

    settings_path = os.getenv("GRAPHRAG_SETTINGS_PATH", "./settings.yaml")
    data_dir = os.getenv("GRAPHRAG_DATA_DIR", "./output")

    try:
        graphrag_service = GraphRagService(
            settings_path=settings_path,
            data_dir=data_dir
        )
        logging.info("GraphRAG service initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize GraphRAG service: {str(e)}")
        raise

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 開發服務器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 資料模型
class SearchRequest(BaseModel):
    query: str
    type: str = "global"  # global 或 local

class SearchResult(BaseModel):
    id: str
    title: str
    snippet: str
    score: float
    source: str
    category: str

class FileInfo(BaseModel):
    id: str
    name: str
    size: str
    status: str
    date: str

class IndexingStatus(BaseModel):
    is_indexing: bool
    progress: int
    message: str

# 全域狀態
indexing_state = {"is_indexing": False, "progress": 0}
files_db = []

@app.get("/")
async def root():
    return {"message": "GraphRAG UI API", "status": "running"}

@app.post("/api/search/global")
async def global_search_endpoint(request: SearchRequest):
    """全域搜尋"""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if graphrag_service is None:
        raise HTTPException(status_code=500, detail="GraphRAG service not initialized")

    try:
        result = await graphrag_service.perform_global_search(
            query=request.query,
            community_level=2,
            response_type="multiple paragraphs"
        )
        return {"response": result}
    except Exception as e:
        logging.error(f"Global search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/search/local")
async def local_search_endpoint(request: SearchRequest):
    """本地搜尋"""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if graphrag_service is None:
        raise HTTPException(status_code=500, detail="GraphRAG service not initialized")

    try:
        result = await graphrag_service.perform_local_search(
            query=request.query,
            community_level=2,
            response_type="multiple paragraphs"
        )
        return {"response": result}
    except Exception as e:
        logging.error(f"Local search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """檔案上傳並觸發索引"""
    try:
        # 驗證檔名
        if not file.filename:
            raise HTTPException(status_code=400, detail="檔案名稱不能為空")

        # 驗證副檔名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的檔案類型。允許的類型: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 讀取檔案內容以檢查大小
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"檔案大小超過限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="檔案內容為空")

        # 儲存檔案到 input 目錄
        file_path = INPUT_DIR / file.filename

        # 如果檔案已存在，添加時間戳避免覆蓋
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_stem = file_path.stem
            file_path = INPUT_DIR / f"{file_stem}_{timestamp}{file_ext}"

        # 寫入檔案
        with open(file_path, "wb") as f:
            f.write(file_content)

        logging.info(f"File saved to: {file_path}")

        # 創建檔案資訊
        file_info = FileInfo(
            id=str(len(files_db) + 1),
            name=file_path.name,
            size=f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.1f} MB",
            status="uploaded",
            date=datetime.now().strftime("%Y-%m-%d")
        )
        files_db.append(file_info)

        # 觸發索引流程（異步）
        asyncio.create_task(trigger_indexing(file_path))

        return {
            "message": "檔案上傳成功，開始建立索引",
            "file": file_info,
            "path": str(file_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檔案上傳失敗: {str(e)}")

@app.get("/api/files", response_model=List[FileInfo])
async def list_files():
    """檔案列表"""
    return files_db

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """刪除檔案"""
    global files_db
    files_db = [f for f in files_db if f.id != file_id]
    return {"message": "檔案刪除成功"}

@app.get("/api/search/suggestions")
async def get_search_suggestions():
    """獲取智能搜尋建議"""
    if graphrag_service is None:
        raise HTTPException(status_code=500, detail="GraphRAG service not initialized")

    try:
        # 讀取實體數據生成建議
        entities_df = graphrag_service.parquet_adapter.read_entities()
        
        # 獲取高頻實體作為搜尋建議
        suggestions = []
        
        # 基於實體類型和重要性生成建議
        if not entities_df.empty:
            # 獲取前幾個重要實體
            top_entities = entities_df.head(10)
            
            for _, entity in top_entities.iterrows():
                entity_name = entity.get("title", entity.get("name", ""))
                if entity_name and len(entity_name) > 2:
                    suggestions.append(f"分析 {entity_name} 的相關內容")
                    if len(suggestions) >= 4:
                        break
        
        # 如果實體不足，添加通用建議
        while len(suggestions) < 4:
            generic_suggestions = [
                "總結文檔中的核心概念",
                "提取關鍵實體間的關聯",
                "分析知識圖譜的結構特徵",
                "探索文檔的主要主題"
            ]
            for suggestion in generic_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    if len(suggestions) >= 4:
                        break
        
        return {"suggestions": suggestions[:4]}
        
    except Exception as e:
        logging.error(f"Search suggestions error: {str(e)}")
        # 錯誤時返回默認建議
        return {
            "suggestions": [
                "分析文檔中的核心技術論點",
                "提取關鍵市場趨勢與數據指標", 
                "總結實體間的語義關聯結構",
                "驗證技術架構的邏輯完整性"
            ]
        }

@app.get("/api/graph/data")
async def get_graph_data():
    """獲取知識圖譜數據"""
    if graphrag_service is None:
        raise HTTPException(status_code=500, detail="GraphRAG service not initialized")

    try:
        # 讀取實體、關係和社群數據
        entities_df = graphrag_service.parquet_adapter.read_entities()
        relationships_df = graphrag_service.parquet_adapter.read_relationships()
        
        # 嘗試讀取社群數據
        communities_df = None
        try:
            communities_df = graphrag_service.parquet_adapter._read_parquet("create_final_communities.parquet")
        except Exception as e:
            logging.warning(f"Could not read communities data: {e}")
            communities_df = None
        
        # 轉換為前端需要的格式
        nodes = []
        node_ids = set()
        for _, entity in entities_df.head(20).iterrows():  # 限制節點數量避免過載
            node_id = entity.get("title", entity.get("name", f"Entity_{entity.name}"))
            nodes.append({
                "id": node_id,
                "group": hash(str(entity.get("type", "unknown"))) % 5 + 1,  # 根據類型分組
                "val": min(int(entity.get("degree", 10)), 50)  # 節點大小
            })
            node_ids.add(node_id)
        
        links = []
        for _, rel in relationships_df.head(30).iterrows():  # 限制連接數量
            source = rel.get("source", "")
            target = rel.get("target", "")
            # 只添加兩端節點都存在的連接
            if source and target and source in node_ids and target in node_ids:
                links.append({
                    "source": source,
                    "target": target
                })
        
        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_entities": len(entities_df),
                "total_relationships": len(relationships_df),
                "total_communities": len(communities_df) if communities_df is not None else 0,
                "displayed_nodes": len(nodes),
                "displayed_links": len(links)
            }
        }
    except Exception as e:
        logging.error(f"Graph data error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load graph data: {str(e)}")

@app.post("/api/indexing/start")
async def start_indexing():
    """開始索引"""
    indexing_state["is_indexing"] = True
    indexing_state["progress"] = 0
    
    # 模擬索引進度
    asyncio.create_task(simulate_indexing())
    
    return IndexingStatus(
        is_indexing=True,
        progress=0,
        message="索引開始"
    )

@app.get("/api/indexing/status", response_model=IndexingStatus)
async def get_indexing_status():
    """獲取索引狀態"""
    return IndexingStatus(
        is_indexing=indexing_state["is_indexing"],
        progress=indexing_state["progress"],
        message="索引進行中" if indexing_state["is_indexing"] else "索引完成"
    )

async def simulate_indexing():
    """模擬索引進度"""
    for i in range(0, 101, 2):
        indexing_state["progress"] = i
        await asyncio.sleep(0.1)
    indexing_state["is_indexing"] = False

async def trigger_indexing(file_path: Path):
    """觸發 GraphRAG 索引流程"""
    if indexing_state["is_indexing"]:
        logging.warning("Indexing already in progress, skipping new request")
        return

    indexing_state["is_indexing"] = True
    indexing_state["progress"] = 0

    try:
        logging.info(f"Starting GraphRAG indexing for file: {file_path}")

        # 切換到 backend 目錄執行索引
        backend_dir = Path(__file__).parent

        # 使用 python -m graphrag.index 執行索引
        cmd = [
            sys.executable,
            "-m",
            "graphrag.index",
            "--root",
            str(backend_dir),
            "--verbose"
        ]

        logging.info(f"Running command: {' '.join(cmd)}")

        # 更新進度
        indexing_state["progress"] = 10

        # 執行索引命令
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(backend_dir)
        )

        indexing_state["progress"] = 30

        # 監控進度
        async def read_output(stream, is_stderr=False):
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_text = line.decode().strip()
                if line_text:
                    if is_stderr:
                        logging.error(f"GraphRAG stderr: {line_text}")
                    else:
                        logging.info(f"GraphRAG stdout: {line_text}")

                    # 根據輸出更新進度
                    if "completed" in line_text.lower() or "success" in line_text.lower():
                        indexing_state["progress"] = min(indexing_state["progress"] + 5, 90)

        # 同時讀取 stdout 和 stderr
        await asyncio.gather(
            read_output(process.stdout, False),
            read_output(process.stderr, True)
        )

        # 等待進程完成
        return_code = await process.wait()

        if return_code == 0:
            indexing_state["progress"] = 100
            logging.info("GraphRAG indexing completed successfully")

            # 重新初始化 GraphRAG 服務以載入新數據
            global graphrag_service
            try:
                settings_path = os.getenv("GRAPHRAG_SETTINGS_PATH", str(backend_dir / "settings.yaml"))
                data_dir = os.getenv("GRAPHRAG_DATA_DIR", str(backend_dir / "output"))

                graphrag_service = GraphRagService(
                    settings_path=settings_path,
                    data_dir=data_dir
                )
                logging.info("GraphRAG service reinitialized with new data")
            except Exception as e:
                logging.error(f"Failed to reinitialize GraphRAG service: {str(e)}")

        else:
            logging.error(f"GraphRAG indexing failed with return code: {return_code}")
            indexing_state["progress"] = 0

    except Exception as e:
        logging.error(f"Indexing error: {str(e)}")
        indexing_state["progress"] = 0

    finally:
        indexing_state["is_indexing"] = False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
