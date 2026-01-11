"""GraphRAG Service for configuration loading and search operations."""

import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import Optional, Any

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.query.api import global_search, local_search
import yaml

from adapters.parquet_adapter import ParquetDataAdapter

logger = logging.getLogger(__name__)


class GraphRagService:
    """GraphRAG 服務：配置載入與搜尋功能。"""

    def __init__(self, settings_path: str, data_dir: str):
        """初始化 GraphRagService。

        Args:
            settings_path: settings.yaml 路徑
            data_dir: Parquet 資料目錄路徑

        Raises:
            FileNotFoundError: 設定檔或資料目錄不存在
            ValueError: 設定檔格式錯誤
        """
        self.settings_path = Path(settings_path)
        self.data_dir = data_dir
        self.config: Optional[GraphRagConfig] = None
        self.parquet_adapter: Optional[ParquetDataAdapter] = None

        self._load_config()
        self._load_data_adapter()

    def _load_config(self) -> None:
        """載入 GraphRAG 配置檔。

        Raises:
            FileNotFoundError: 設定檔不存在
            ValueError: 設定檔格式錯誤
        """
        if not self.settings_path.exists():
            error_msg = f"Settings file not found: {self.settings_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings_dict = yaml.safe_load(f)

            if not settings_dict:
                raise ValueError("Settings file is empty or invalid")

            root_dir = str(self.settings_path.parent)
            self.config = create_graphrag_config(values=settings_dict, root_dir=root_dir)
            logger.info(f"Successfully loaded GraphRAG config from {self.settings_path}")

        except yaml.YAMLError as e:
            error_msg = f"Failed to parse settings.yaml: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load GraphRAG config: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _load_data_adapter(self) -> None:
        """載入 Parquet 資料適配器。

        Raises:
            FileNotFoundError: 資料目錄不存在
        """
        try:
            self.parquet_adapter = ParquetDataAdapter(self.data_dir)
            logger.info(f"Successfully initialized ParquetDataAdapter for {self.data_dir}")
        except FileNotFoundError as e:
            logger.error(str(e))
            raise

    async def perform_global_search(
        self,
        query: str,
        community_level: int = 2,
        response_type: str = "multiple paragraphs"
    ) -> str | dict[str, Any] | list[dict[str, Any]]:
        """執行 global search。

        Args:
            query: 查詢字串
            community_level: 社群層級
            response_type: 回應類型

        Returns:
            GraphRAG global search 結果

        Raises:
            ValueError: query 為空或配置未載入
            Exception: GraphRAG 內部搜尋錯誤
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not self.config or not self.parquet_adapter:
            raise ValueError("GraphRAG configuration not loaded")

        try:
            nodes, entities, community_reports = self.parquet_adapter.load_for_global_search()

            result = await global_search(
                config=self.config,
                nodes=nodes,
                entities=entities,
                community_reports=community_reports,
                community_level=community_level,
                response_type=response_type,
                query=query
            )

            logger.info(f"Global search completed for query: {query}")
            return result

        except Exception as e:
            error_msg = f"Global search failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def perform_local_search(
        self,
        query: str,
        community_level: int = 2,
        response_type: str = "multiple paragraphs"
    ) -> str | dict[str, Any] | list[dict[str, Any]]:
        """執行 local search。

        Args:
            query: 查詢字串
            community_level: 社群層級
            response_type: 回應類型

        Returns:
            GraphRAG local search 結果

        Raises:
            ValueError: query 為空或配置未載入
            Exception: GraphRAG 內部搜尋錯誤
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not self.config or not self.parquet_adapter:
            raise ValueError("GraphRAG configuration not loaded")

        try:
            nodes, entities, community_reports, text_units, relationships, covariates = \
                self.parquet_adapter.load_for_local_search()

            result = await local_search(
                config=self.config,
                nodes=nodes,
                entities=entities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                covariates=covariates,
                community_level=community_level,
                response_type=response_type,
                query=query
            )

            logger.info(f"Local search completed for query: {query}")
            return result

        except Exception as e:
            error_msg = f"Local search failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
