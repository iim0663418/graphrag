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
import markdown
from bs4 import BeautifulSoup

from services.graphrag_service import GraphRagService

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="GraphRAG UI API", version="1.0.0")

# 初始化 GraphRAG 服務
graphrag_service: Optional[GraphRagService] = None

# 檔案上傳配置
BACKEND_ROOT = Path(__file__).parent
INPUT_DIR = BACKEND_ROOT / "input"
OUTPUT_DIR = BACKEND_ROOT / "output"
# GraphRAG 支援 .txt, .csv, .md 格式 (參考 graphrag/config/enums.py InputFileType)
ALLOWED_EXTENSIONS = {".txt", ".csv", ".md"}
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

        # 如果是 Markdown 檔案，轉換為純文字
        if file_ext == ".md":
            try:
                # 將 bytes 轉換為字串
                md_content = file_content.decode("utf-8")
                # Markdown 轉 HTML
                html_content = markdown.markdown(md_content)
                # HTML 轉純文字
                soup = BeautifulSoup(html_content, "html.parser")
                text_content = soup.get_text()
                # 更新內容和副檔名
                file_content = text_content.encode("utf-8")
                file_ext = ".txt"
                # 更新檔名（移除 .md，加上 .txt）
                original_filename = Path(file.filename).stem + ".txt"
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Markdown 轉換失敗: {str(e)}"
                )
        else:
            original_filename = file.filename

        # 儲存檔案到 input 目錄
        file_path = INPUT_DIR / original_filename

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
    """檔案列表 - 顯示 input/ 目錄中的實際檔案"""
    try:
        # 掃描 input/ 目錄的實際檔案
        actual_files = []
        file_counter = 1

        if INPUT_DIR.exists():
            for file_path in INPUT_DIR.iterdir():
                # 只處理檔案，跳過目錄
                if not file_path.is_file():
                    continue

                # 只顯示支援的檔案類型
                if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    continue

                # 獲取檔案資訊
                file_stat = file_path.stat()
                file_size = file_stat.st_size
                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

                # 格式化檔案大小
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / 1024 / 1024:.1f} MB"

                # 創建 FileInfo 物件
                file_info = FileInfo(
                    id=str(file_counter),
                    name=file_path.name,
                    size=size_str,
                    status="ready",
                    date=file_mtime.strftime("%Y-%m-%d")
                )
                actual_files.append(file_info)
                file_counter += 1

        # 按日期排序（最新的在前）
        actual_files.sort(key=lambda f: f.date, reverse=True)

        return actual_files

    except Exception as e:
        logging.error(f"List files error: {str(e)}")
        # 發生錯誤時返回空列表，保持向後相容性
        return []

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """刪除檔案 - 從 input/ 目錄中刪除實際檔案"""
    try:
        # 獲取當前檔案列表以找到對應的檔案名稱
        current_files = await list_files()
        target_file = next((f for f in current_files if f.id == file_id), None)

        if not target_file:
            raise HTTPException(status_code=404, detail="找不到指定的檔案")

        # 刪除實際檔案
        file_path = INPUT_DIR / target_file.name
        if file_path.exists():
            file_path.unlink()
            logging.info(f"Deleted file: {file_path}")

        # 保持向後相容性 - 同時從記憶體資料庫中移除
        global files_db
        files_db = [f for f in files_db if f.id != file_id]

        return {"message": "檔案刪除成功", "filename": target_file.name}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete file error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檔案刪除失敗: {str(e)}")

@app.get("/api/search/suggestions")
async def get_search_suggestions():
    """獲取智能搜尋建議"""
    # 預設建議（在沒有索引數據時使用）
    default_suggestions = [
        "總結文檔中的核心概念",
        "提取關鍵實體間的關聯",
        "分析知識圖譜的結構特徵",
        "探索文檔的主要主題"
    ]

    # 如果服務未初始化，返回預設建議
    if graphrag_service is None:
        logging.warning("GraphRAG service not initialized, returning default suggestions")
        return {"suggestions": default_suggestions}

    try:
        # 檢查 parquet adapter 是否存在
        if graphrag_service.parquet_adapter is None:
            logging.warning("Parquet adapter not initialized, returning default suggestions")
            return {"suggestions": default_suggestions}

        # 嘗試讀取實體數據生成建議
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
            for suggestion in default_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    if len(suggestions) >= 4:
                        break

        return {"suggestions": suggestions[:4]}

    except FileNotFoundError as e:
        # Parquet 檔案不存在，返回預設建議
        logging.warning(f"Parquet files not found: {str(e)}, returning default suggestions")
        return {"suggestions": default_suggestions}
    except Exception as e:
        # 其他錯誤也返回預設建議
        logging.warning(f"Search suggestions error: {str(e)}, returning default suggestions")
        return {"suggestions": default_suggestions}

@app.get("/api/graph/data")
async def get_graph_data():
    """獲取知識圖譜數據"""
    # 空的圖譜結構（在沒有索引數據時使用）
    empty_graph = {
        "nodes": [],
        "links": [],
        "stats": {
            "total_entities": 0,
            "total_relationships": 0,
            "total_communities": 0,
            "displayed_nodes": 0,
            "displayed_links": 0
        }
    }

    # 如果服務未初始化，返回空圖譜
    if graphrag_service is None:
        logging.warning("GraphRAG service not initialized, returning empty graph")
        return empty_graph

    try:
        # 檢查 parquet adapter 是否存在
        if graphrag_service.parquet_adapter is None:
            logging.warning("Parquet adapter not initialized, returning empty graph")
            return empty_graph

        # 嘗試讀取實體、關係和社群數據
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
    except FileNotFoundError as e:
        # Parquet 檔案不存在，返回空圖譜
        logging.warning(f"Parquet files not found: {str(e)}, returning empty graph")
        return empty_graph
    except Exception as e:
        # 其他錯誤也返回空圖譜而不是拋出異常
        logging.warning(f"Graph data error: {str(e)}, returning empty graph")
        return empty_graph

@app.post("/api/indexing/start")
async def start_indexing():
    """開始索引 - 執行真實的 GraphRAG 索引處理"""
    if indexing_state["is_indexing"]:
        raise HTTPException(status_code=409, detail="索引已在進行中")

    indexing_state["is_indexing"] = True
    indexing_state["progress"] = 0

    # 立即啟動索引任務，不等待完成
    try:
        asyncio.create_task(run_real_indexing())
        logging.info("GraphRAG indexing task created successfully")
    except Exception as e:
        logging.error(f"Failed to create indexing task: {str(e)}")
        indexing_state["is_indexing"] = False
        raise HTTPException(status_code=500, detail=f"無法啟動索引: {str(e)}")

    return IndexingStatus(
        is_indexing=True,
        progress=0,
        message="索引開始 - 執行真實的 GraphRAG 處理"
    )

@app.get("/api/indexing/status", response_model=IndexingStatus)
async def get_indexing_status():
    """獲取索引狀態"""
    return IndexingStatus(
        is_indexing=indexing_state["is_indexing"],
        progress=indexing_state["progress"],
        message="索引進行中" if indexing_state["is_indexing"] else "索引完成"
    )

async def run_real_indexing():
    """執行真實的 GraphRAG 索引流程 - 處理所有 input 目錄中的檔案"""
    try:
        logging.info("Starting real GraphRAG indexing for all files in input directory")

        # 使用項目根目錄作為執行環境
        project_root = Path(__file__).parent.parent.parent
        backend_dir = Path(__file__).parent

        # 檢查 input 目錄中是否有檔案
        input_files = list(INPUT_DIR.glob("*"))
        input_files = [f for f in input_files if f.is_file() and f.suffix in ALLOWED_EXTENSIONS]

        if not input_files:
            logging.warning("No input files found for indexing")
            indexing_state["is_indexing"] = False
            indexing_state["progress"] = 0
            return

        logging.info(f"Found {len(input_files)} files to index: {[f.name for f in input_files]}")

        # 使用當前 Python 解釋器，從 graphrag 目錄執行
        import shutil
        python_executable = shutil.which('python') or sys.executable
        
        cmd = [
            python_executable,
            "-m",
            "graphrag.index",
            "--root",
            str(backend_dir)  # 使用絕對路徑確保正確的配置
        ]

        # 不需要設置 PYTHONPATH，因為我們在正確的目錄執行

        logging.info(f"Running command: {' '.join(cmd)} from {project_root}")

        # 更新進度
        indexing_state["progress"] = 10

        # 執行索引命令，從項目根目錄執行
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_root)  # 從 graphrag 目錄執行
        )

        indexing_state["progress"] = 30

        # 簡化的進度監控 - 不阻塞等待
        async def monitor_progress():
            while process.returncode is None:
                await asyncio.sleep(10)  # 每10秒更新一次進度
                if indexing_state["progress"] < 90:
                    indexing_state["progress"] += 5

        # 啟動進度監控任務
        monitor_task = asyncio.create_task(monitor_progress())

        # 等待進程完成
        return_code = await process.wait()
        
        # 取消進度監控
        monitor_task.cancel()

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
        logging.error(f"Real indexing error: {str(e)}")
        indexing_state["progress"] = 0

    finally:
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

        # 使用項目根目錄作為執行環境
        project_root = Path(__file__).parent.parent.parent
        backend_dir = Path(__file__).parent

        # 使用 python -m graphrag.index 執行索引，從項目根目錄執行
        cmd = [
            sys.executable,
            "-m",
            "graphrag.index",
            "--root",
            str(backend_dir),
            "--verbose"
        ]

        logging.info(f"Running command: {' '.join(cmd)} from {project_root}")

        # 更新進度
        indexing_state["progress"] = 10

        # 執行索引命令，從項目根目錄執行
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_root)  # 關鍵修改：從項目根目錄執行
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
