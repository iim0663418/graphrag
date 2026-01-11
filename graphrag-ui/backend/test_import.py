"""測試 GraphRAG 模組 import 是否正常。"""

import sys
from pathlib import Path

# 將 GraphRAG 專案根目錄加入 sys.path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"✓ Project root added to sys.path: {project_root}")
print(f"✓ Current sys.path: {sys.path[:3]}...")  # 顯示前3個路徑

try:
    from graphrag.config.create_graphrag_config import create_graphrag_config
    print("✓ Successfully imported: graphrag.config.create_graphrag_config")
except ImportError as e:
    print(f"✗ Failed to import graphrag.config.create_graphrag_config: {e}")
    sys.exit(1)

try:
    from graphrag.config.models.graph_rag_config import GraphRagConfig
    print("✓ Successfully imported: graphrag.config.models.graph_rag_config")
except ImportError as e:
    print(f"✗ Failed to import graphrag.config.models.graph_rag_config: {e}")
    sys.exit(1)

try:
    from graphrag.query.api import global_search, local_search
    print("✓ Successfully imported: graphrag.query.api (global_search, local_search)")
except ImportError as e:
    print(f"✗ Failed to import graphrag.query.api: {e}")
    sys.exit(1)

print("\n✓ All GraphRAG imports successful!")
print(f"✓ GraphRAG module location: {Path(project_root) / 'graphrag'}")
