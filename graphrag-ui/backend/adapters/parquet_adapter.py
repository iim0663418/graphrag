"""Parquet Data Adapter for GraphRAG indexing outputs."""

from pathlib import Path
import pandas as pd
from typing import Optional


class ParquetDataAdapter:
    """讀取 GraphRAG Indexer 產生的 Parquet 檔案。"""

    def __init__(self, data_dir: str):
        """初始化 ParquetDataAdapter。

        Args:
            data_dir: Parquet 檔案所在目錄路徑
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

    def _read_parquet(self, filename: str, required: bool = True) -> Optional[pd.DataFrame]:
        """讀取單個 Parquet 檔案。

        Args:
            filename: Parquet 檔案名稱
            required: 是否為必需檔案

        Returns:
            DataFrame 或 None (若為可選檔案且不存在)

        Raises:
            FileNotFoundError: 必需檔案不存在
            ValueError: Parquet 格式異常
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            if required:
                raise FileNotFoundError(f"Required parquet file not found: {filename}")
            return None

        try:
            df = pd.read_parquet(file_path)
            return df
        except Exception as e:
            raise ValueError(f"Failed to read parquet file {filename}: {str(e)}")

    def read_nodes(self) -> pd.DataFrame:
        """讀取 nodes (create_final_nodes.parquet)。"""
        return self._read_parquet("create_final_nodes.parquet")

    def read_entities(self) -> pd.DataFrame:
        """讀取 entities (create_final_entities.parquet)。"""
        return self._read_parquet("create_final_entities.parquet")

    def read_community_reports(self) -> pd.DataFrame:
        """讀取 community reports (create_final_community_reports.parquet)。"""
        return self._read_parquet("create_final_community_reports.parquet")

    def read_text_units(self) -> pd.DataFrame:
        """讀取 text units (create_final_text_units.parquet)。"""
        return self._read_parquet("create_final_text_units.parquet")

    def read_relationships(self) -> pd.DataFrame:
        """讀取 relationships (create_final_relationships.parquet)。"""
        return self._read_parquet("create_final_relationships.parquet")

    def read_covariates(self) -> Optional[pd.DataFrame]:
        """讀取 covariates (create_final_covariates.parquet) - 可選。"""
        return self._read_parquet("create_final_covariates.parquet", required=False)

    def load_for_global_search(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """載入 global search 所需的所有 Parquet 資料。

        Returns:
            (nodes, entities, community_reports)
        """
        nodes = self.read_nodes()
        entities = self.read_entities()
        community_reports = self.read_community_reports()
        return nodes, entities, community_reports

    def load_for_local_search(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                              pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        """載入 local search 所需的所有 Parquet 資料。

        Returns:
            (nodes, entities, community_reports, text_units, relationships, covariates)
        """
        nodes = self.read_nodes()
        entities = self.read_entities()
        community_reports = self.read_community_reports()
        text_units = self.read_text_units()
        relationships = self.read_relationships()
        covariates = self.read_covariates()

        return nodes, entities, community_reports, text_units, relationships, covariates
