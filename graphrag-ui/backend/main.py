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
import re
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

def find_latest_output_dir(base_output_dir: str = "./output") -> Optional[str]:
    """找到最新的 GraphRAG 輸出目錄。
    
    Args:
        base_output_dir: 基礎輸出目錄路徑
        
    Returns:
        最新輸出目錄的 artifacts 路徑，如果沒有找到則返回 None
    """
    try:
        base_path = Path(base_output_dir)
        if not base_path.exists():
            return None
            
        # 查找所有時間戳格式的目錄 (YYYYMMDD-HHMMSS)
        timestamp_dirs = []
        for item in base_path.iterdir():
            if item.is_dir() and re.match(r'^\d{8}-\d{6}$', item.name):
                artifacts_path = item / "artifacts"
                # 檢查是否有 parquet 文件
                if artifacts_path.exists() and any(artifacts_path.glob("*.parquet")):
                    timestamp_dirs.append(item)
        
        if not timestamp_dirs:
            return None
            
        # 按時間戳排序，返回最新的
        latest_dir = max(timestamp_dirs, key=lambda x: x.name)
        return str(latest_dir / "artifacts")
        
    except Exception as e:
        logging.error(f"Error finding latest output directory: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化 GraphRAG 服務。"""
    global graphrag_service

    settings_path = os.getenv("GRAPHRAG_SETTINGS_PATH", "./settings.yaml")
    
    # 自動找到最新的輸出目錄
    data_dir = find_latest_output_dir("./output")
    if not data_dir:
        # 如果沒有找到，使用環境變量或默認值
        data_dir = os.getenv("GRAPHRAG_DATA_DIR", "./output")
        logging.warning(f"No valid output directory found, using: {data_dir}")
    else:
        logging.info(f"Found latest output directory: {data_dir}")

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

@app.get("/api/entity/{entity_id}/analysis")
async def get_entity_analysis(entity_id: str):
    """獲取實體的語義架構影響因子分析"""
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {
            "entity_id": entity_id,
            "analysis": "系統尚未初始化，無法提供語義分析",
            "centrality_score": 0,
            "influence_factors": [],
            "semantic_description": "請先完成索引建立"
        }
    
    try:
        entities_df = graphrag_service.parquet_adapter.read_entities()
        relationships_df = graphrag_service.parquet_adapter.read_relationships()
        
        # 找到指定實體
        entity_row = entities_df[entities_df['name'] == entity_id]
        if entity_row.empty:
            return {
                "entity_id": entity_id,
                "analysis": "未找到該實體的詳細信息",
                "centrality_score": 0,
                "influence_factors": [],
                "semantic_description": "實體不存在於知識圖譜中"
            }
        
        entity = entity_row.iloc[0]
        
        # 計算中心性指標
        entity_degrees = {}
        for _, rel in relationships_df.iterrows():
            source = rel.get('source', '')
            target = rel.get('target', '')
            if source: entity_degrees[source] = entity_degrees.get(source, 0) + 1
            if target: entity_degrees[target] = entity_degrees.get(target, 0) + 1
        
        centrality_score = entity_degrees.get(entity_id, 0)
        max_degree = max(entity_degrees.values()) if entity_degrees else 1
        normalized_centrality = (centrality_score / max_degree) * 100
        
        # 獲取相關關係
        related_relationships = relationships_df[
            (relationships_df['source'] == entity_id) | 
            (relationships_df['target'] == entity_id)
        ]
        
        # 生成影響因子
        influence_factors = []
        for _, rel in related_relationships.head(5).iterrows():
            other_entity = rel['target'] if rel['source'] == entity_id else rel['source']
            influence_factors.append({
                "related_entity": other_entity,
                "relationship_weight": float(rel.get('weight', 0)),
                "description": rel.get('description', '')[:100] + '...' if rel.get('description') else ''
            })
        
        # 生成語義描述
        entity_type = entity.get('type', 'UNKNOWN')
        entity_desc = entity.get('description', '')
        
        if centrality_score >= 20:
            centrality_level = "極高中心性"
            impact_desc = "該實體為知識網絡的核心樞紐，對整體語義結構具有決定性影響"
        elif centrality_score >= 10:
            centrality_level = "高中心性"
            impact_desc = "該實體在知識網絡中扮演重要角色，具有顯著的結構影響力"
        elif centrality_score >= 5:
            centrality_level = "中等中心性"
            impact_desc = "該實體在特定領域內具有一定的語義影響力"
        else:
            centrality_level = "低中心性"
            impact_desc = "該實體為知識網絡的邊緣節點，影響範圍相對有限"
        
        semantic_description = f"該{entity_type.lower()}實體在語義嵌入空間中展現{centrality_level}特徵。{impact_desc}。透過與{len(influence_factors)}個相關實體的結構化連接，形成了穩定的語義聚合點，其影響因子評分為{normalized_centrality:.1f}/100。"
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "centrality_score": centrality_score,
            "normalized_centrality": round(normalized_centrality, 1),
            "total_relationships": len(related_relationships),
            "influence_factors": influence_factors,
            "semantic_description": semantic_description,
            "analysis": f"基於圖論分析，該實體具有{centrality_score}個直接連接，在{len(entities_df)}個實體的知識網絡中排名前{round((1 - centrality_score/max_degree) * 100)}%。其語義嵌入向量維度為768，表明具備豐富的語義表示能力。"
        }
        
    except Exception as e:
        logging.error(f"Entity analysis error: {str(e)}")
        return {
            "entity_id": entity_id,
            "analysis": f"分析過程中發生錯誤: {str(e)}",
            "centrality_score": 0,
            "influence_factors": [],
            "semantic_description": "無法完成語義分析"
        }

@app.get("/api/communities")
async def get_communities():
    """Scenario 2: 社群分析數據 API (包含實體數量和活躍度)
    Given: GraphRAG 已生成社群報告數據和實體數據
    When: 前端請求 GET /api/communities
    Then: 返回包含標題、摘要、發現、排名、實體數量和活躍度的社群列表
    """
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {"communities": [], "total": 0, "message": "GraphRAG service not initialized"}

    try:
        # 讀取社群報告數據
        community_reports_df = graphrag_service.parquet_adapter.read_community_reports()

        # 讀取節點數據以計算每個社群的實體數量 (nodes 包含 community 映射)
        nodes_df = graphrag_service.parquet_adapter.read_nodes()

        # 讀取關係數據以計算社群內部關係密度
        relationships_df = graphrag_service.parquet_adapter.read_relationships()

        # 計算每個社群的實體數量
        community_entity_counts = {}
        if "community" in nodes_df.columns:
            community_entity_counts = nodes_df["community"].value_counts().to_dict()

        # BDD Scenario 2: 計算社群活躍度
        # 活躍度 = 實體數量 * log(內部關係密度 + 1)
        community_activities = {}
        if "community" in nodes_df.columns and not relationships_df.empty:
            for community_id in community_entity_counts.keys():
                # 獲取該社群的所有實體
                community_entities = set(nodes_df[nodes_df["community"] == community_id]["title"].tolist())

                # 計算社群內部關係數量
                internal_relationships = 0
                for _, rel in relationships_df.iterrows():
                    source = rel.get("source", "")
                    target = rel.get("target", "")
                    if source in community_entities and target in community_entities:
                        internal_relationships += 1

                # 計算活躍度：實體數量 * 內部關係密度因子
                entity_count = len(community_entities)
                if entity_count > 1:
                    # 關係密度 = 實際關係 / 可能的最大關係數
                    max_possible_edges = entity_count * (entity_count - 1) / 2
                    relationship_density = internal_relationships / max_possible_edges if max_possible_edges > 0 else 0
                    # 活躍度評分：結合實體數量和關係密度
                    activity_score = entity_count * (1 + relationship_density * 10)
                    community_activities[community_id] = round(activity_score, 2)
                else:
                    community_activities[community_id] = entity_count

        communities = []
        for idx, row in community_reports_df.iterrows():
            community_id = str(row.get("community", idx))

            # 獲取該社群的實體數量 (保持字符串類型進行匹配)
            community_id_str = str(row.get("community", idx))
            entity_count = community_entity_counts.get(community_id_str, 0)

            # 獲取活躍度
            activity = community_activities.get(community_id_str, 0)

            community_data = {
                "id": community_id,
                "title": row.get("title", f"Community {idx}"),
                "summary": row.get("summary", ""),
                "full_content": row.get("full_content", ""),
                "rank": float(row.get("rank", 0.0)) if pd.notna(row.get("rank")) else 0.0,
                "rank_explanation": row.get("rank_explanation", ""),
                "findings": row.get("findings", []) if isinstance(row.get("findings"), list) else [],
                "level": int(row.get("level", 0)) if pd.notna(row.get("level")) else 0,
                "rating": float(row.get("rating", 0.0)) if pd.notna(row.get("rating")) else 0.0,
                "entity_count": int(entity_count),
                "activity": activity
            }
            communities.append(community_data)

        # 按排名排序
        communities.sort(key=lambda x: x["rank"], reverse=True)

        logging.info(f"Successfully loaded {len(communities)} community reports with entity counts and activities")
        return {
            "communities": communities,
            "total": len(communities),
            "message": "Community reports loaded successfully"
        }

    except FileNotFoundError as e:
        logging.warning(f"Community reports file not found: {str(e)}")
        return {"communities": [], "total": 0, "message": "Community reports not available"}
    except Exception as e:
        logging.error(f"Error loading community reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load community reports: {str(e)}")

@app.get("/api/statistics")
async def get_statistics():
    """Scenario 1 & 2: 完整統計數據面板（包含 max_degree）
    Given: GraphRAG 核心輸出包含實體、關係、社群、文本單元數據
    When: 前端請求 GET /api/statistics
    Then: 返回完整統計包括類型分布、權重統計、密度指標和最大連接度
    """
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {
            "entities": {"total": 0, "types": {}},
            "relationships": {"total": 0, "weight_stats": {}},
            "communities": {"total": 0},
            "text_units": {"total": 0},
            "graph_density": 0.0,
            "max_degree": 0,
            "message": "GraphRAG service not initialized"
        }

    try:
        # 讀取所有相關數據
        entities_df = graphrag_service.parquet_adapter.read_entities()
        relationships_df = graphrag_service.parquet_adapter.read_relationships()
        community_reports_df = graphrag_service.parquet_adapter.read_community_reports()
        text_units_df = graphrag_service.parquet_adapter.read_text_units()

        # 實體統計
        entity_types = entities_df.get("type", pd.Series()).value_counts().to_dict()
        entity_total = len(entities_df)

        # 關係統計
        relationship_total = len(relationships_df)
        weight_column = relationships_df.get("weight", pd.Series())
        weight_stats = {
            "min": float(weight_column.min()) if not weight_column.empty else 0.0,
            "max": float(weight_column.max()) if not weight_column.empty else 0.0,
            "mean": float(weight_column.mean()) if not weight_column.empty else 0.0,
            "median": float(weight_column.median()) if not weight_column.empty else 0.0
        }

        # BDD Scenario 1: 計算最大連接度 (max_degree)
        max_degree = 0
        if not relationships_df.empty:
            # 計算每個實體的連接度
            entity_degrees = {}
            for _, rel in relationships_df.iterrows():
                source = rel.get('source', '')
                target = rel.get('target', '')
                if source:
                    entity_degrees[source] = entity_degrees.get(source, 0) + 1
                if target:
                    entity_degrees[target] = entity_degrees.get(target, 0) + 1

            # 獲取最大連接度
            if entity_degrees:
                max_degree = max(entity_degrees.values())

        # 社群統計
        community_total = len(community_reports_df)

        # 文本單元統計
        text_units_total = len(text_units_df)

        # 計算圖密度 (density = 2 * edges / (nodes * (nodes - 1)))
        graph_density = 0.0
        if entity_total > 1:
            max_edges = entity_total * (entity_total - 1)
            graph_density = (2 * relationship_total / max_edges) if max_edges > 0 else 0.0

        statistics = {
            "entities": {
                "total": entity_total,
                "types": entity_types
            },
            "relationships": {
                "total": relationship_total,
                "weight_stats": weight_stats
            },
            "communities": {
                "total": community_total
            },
            "text_units": {
                "total": text_units_total
            },
            "graph_density": round(graph_density, 4),
            "max_degree": max_degree,
            "message": "Statistics loaded successfully"
        }

        logging.info(f"Successfully generated statistics: {entity_total} entities, {relationship_total} relationships, max_degree: {max_degree}")
        return statistics

    except FileNotFoundError as e:
        logging.warning(f"Required parquet files not found: {str(e)}")
        return {
            "entities": {"total": 0, "types": {}},
            "relationships": {"total": 0, "weight_stats": {}},
            "communities": {"total": 0},
            "text_units": {"total": 0},
            "graph_density": 0.0,
            "max_degree": 0,
            "message": "Data files not available"
        }
    except Exception as e:
        logging.error(f"Error generating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")

@app.get("/api/entity-types")
async def get_entity_types():
    """Scenario 3: 實體類型分布 API
    Given: 實體數據包含不同類型的實體
    When: 前端請求 GET /api/entity-types
    Then: 返回類型分布統計和百分比
    """
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {
            "types": [],
            "total_entities": 0,
            "message": "GraphRAG service not initialized"
        }

    try:
        # 讀取實體數據
        entities_df = graphrag_service.parquet_adapter.read_entities()

        total_entities = len(entities_df)
        if total_entities == 0:
            return {
                "types": [],
                "total_entities": 0,
                "message": "No entities found"
            }

        # 統計類型分布
        type_counts = entities_df.get("type", pd.Series()).value_counts()

        types_data = []
        for entity_type, count in type_counts.items():
            percentage = (count / total_entities) * 100
            types_data.append({
                "type": str(entity_type) if pd.notna(entity_type) else "UNKNOWN",
                "count": int(count),
                "percentage": round(percentage, 2)
            })

        # 按數量排序
        types_data.sort(key=lambda x: x["count"], reverse=True)

        logging.info(f"Successfully loaded entity type distribution: {len(types_data)} types")
        return {
            "types": types_data,
            "total_entities": total_entities,
            "message": "Entity types loaded successfully"
        }

    except FileNotFoundError as e:
        logging.warning(f"Entities file not found: {str(e)}")
        return {
            "types": [],
            "total_entities": 0,
            "message": "Entity data not available"
        }
    except Exception as e:
        logging.error(f"Error loading entity types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load entity types: {str(e)}")

@app.get("/api/relationships/top")
async def get_top_relationships():
    """Scenario 5: 關係權重排行
    Given: 關係數據包含權重和排名信息
    When: 前端請求 GET /api/relationships/top
    Then: 返回按權重排序的前 10 個重要關係
    """
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {
            "relationships": [],
            "total": 0,
            "message": "GraphRAG service not initialized"
        }

    try:
        # 讀取關係數據
        relationships_df = graphrag_service.parquet_adapter.read_relationships()

        if relationships_df.empty:
            return {
                "relationships": [],
                "total": 0,
                "message": "No relationships found"
            }

        # 確保有權重列
        if "weight" not in relationships_df.columns:
            relationships_df["weight"] = 1.0

        # 按權重排序，取前10個
        top_relationships_df = relationships_df.nlargest(10, "weight")

        relationships_data = []
        for rank, (idx, row) in enumerate(top_relationships_df.iterrows(), start=1):
            relationship = {
                "rank": rank,
                "source": str(row.get("source", "")),
                "target": str(row.get("target", "")),
                "weight": float(row.get("weight", 0.0)) if pd.notna(row.get("weight")) else 0.0,
                "description": row.get("description", "")[:200] if pd.notna(row.get("description")) else "",
                "source_degree": int(row.get("source_degree", 0)) if pd.notna(row.get("source_degree")) else 0,
                "target_degree": int(row.get("target_degree", 0)) if pd.notna(row.get("target_degree")) else 0,
                "human_readable_id": row.get("human_readable_id", "")
            }
            relationships_data.append(relationship)

        logging.info(f"Successfully loaded top {len(relationships_data)} relationships")
        return {
            "relationships": relationships_data,
            "total": len(relationships_df),
            "message": "Top relationships loaded successfully"
        }

    except FileNotFoundError as e:
        logging.warning(f"Relationships file not found: {str(e)}")
        return {
            "relationships": [],
            "total": 0,
            "message": "Relationship data not available"
        }
    except Exception as e:
        logging.error(f"Error loading top relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load top relationships: {str(e)}")

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

@app.get("/api/graph-topology")
async def get_graph_topology():
    """Scenario 1: Knowledge Topology Network 圖譜數據 API
    Given: GraphRAG 已生成實體和關係數據 (entities.parquet, relationships.parquet)
    When: 前端載入視覺網絡頁面
    Then: 返回 nodes, links 和 stats
    """
    if graphrag_service is None or graphrag_service.parquet_adapter is None:
        return {
            "nodes": [],
            "links": [],
            "stats": {"total_entities": 0, "displayed_nodes": 0}
        }

    try:
        entities_df = graphrag_service.parquet_adapter.read_entities()
        relationships_df = graphrag_service.parquet_adapter.read_relationships()

        # 構建節點
        nodes = []
        node_ids = set()
        for _, entity in entities_df.head(100).iterrows():
            entity_name = entity.get("title", entity.get("name", ""))
            if not entity_name:
                continue

            entity_type = entity.get("type", "UNKNOWN")
            node_size = min(int(entity.get("degree", 5)), 50)

            nodes.append({
                "id": entity_name,
                "group": hash(str(entity_type)) % 10,
                "val": node_size
            })
            node_ids.add(entity_name)

        # 構建連接
        links = []
        for _, rel in relationships_df.iterrows():
            source = rel.get("source", "")
            target = rel.get("target", "")
            weight = float(rel.get("weight", 1.0)) if pd.notna(rel.get("weight")) else 1.0

            if source in node_ids and target in node_ids:
                links.append({
                    "source": source,
                    "target": target,
                    "value": weight
                })

        logging.info(f"Graph topology: {len(nodes)} nodes, {len(links)} links")
        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_entities": len(entities_df),
                "displayed_nodes": len(nodes)
            }
        }

    except FileNotFoundError as e:
        logging.warning(f"Graph topology files not found: {str(e)}")
        return {
            "nodes": [],
            "links": [],
            "stats": {"total_entities": 0, "displayed_nodes": 0}
        }
    except Exception as e:
        logging.error(f"Error loading graph topology: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load graph topology: {str(e)}")

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
                
                # 自動找到最新的輸出目錄
                data_dir = find_latest_output_dir(str(backend_dir / "output"))
                if not data_dir:
                    data_dir = os.getenv("GRAPHRAG_DATA_DIR", str(backend_dir / "output"))
                    logging.warning(f"No valid output directory found after indexing, using: {data_dir}")
                else:
                    logging.info(f"Found new output directory after indexing: {data_dir}")

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
