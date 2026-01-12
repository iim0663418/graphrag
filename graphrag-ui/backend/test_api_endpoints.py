"""
BDD Test Script for GraphRAG Core Output Integration
Tests all 4 new API endpoints following the BDD specifications
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import FastAPI testing utilities
from fastapi.testclient import TestClient
from main import app, graphrag_service

client = TestClient(app)


def test_communities_api():
    """
    BDD Scenario 1: 社群分析數據 API
    Given: GraphRAG 已生成社群報告數據
    When: 前端請求 GET /api/communities
    Then: 返回包含標題、摘要、發現、排名的社群列表
    """
    print("\n=== Testing GET /api/communities ===")
    response = client.get("/api/communities")
    print(f"Status Code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response Keys: {data.keys()}")
    print(f"Total Communities: {data.get('total', 0)}")

    # Verify response structure
    assert "communities" in data, "Missing 'communities' key"
    assert "total" in data, "Missing 'total' key"
    assert "message" in data, "Missing 'message' key"

    if data["total"] > 0:
        first_community = data["communities"][0]
        print(f"First Community Keys: {first_community.keys()}")
        # Verify community structure
        assert "id" in first_community, "Missing 'id' in community"
        assert "title" in first_community, "Missing 'title' in community"
        assert "summary" in first_community, "Missing 'summary' in community"
        assert "rank" in first_community, "Missing 'rank' in community"
        print(f"First Community Title: {first_community['title']}")
        print(f"First Community Rank: {first_community['rank']}")

    print("✓ Communities API test passed")


def test_statistics_api():
    """
    BDD Scenario 2: 完整統計數據面板
    Given: GraphRAG 核心輸出包含實體、關係、社群、文本單元數據
    When: 前端請求 GET /api/statistics
    Then: 返回完整統計包括類型分布、權重統計、密度指標
    """
    print("\n=== Testing GET /api/statistics ===")
    response = client.get("/api/statistics")
    print(f"Status Code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response Keys: {data.keys()}")

    # Verify response structure
    assert "entities" in data, "Missing 'entities' key"
    assert "relationships" in data, "Missing 'relationships' key"
    assert "communities" in data, "Missing 'communities' key"
    assert "text_units" in data, "Missing 'text_units' key"
    assert "graph_density" in data, "Missing 'graph_density' key"

    # Verify nested structure
    assert "total" in data["entities"], "Missing 'total' in entities"
    assert "types" in data["entities"], "Missing 'types' in entities"
    assert "weight_stats" in data["relationships"], "Missing 'weight_stats' in relationships"

    print(f"Total Entities: {data['entities']['total']}")
    print(f"Total Relationships: {data['relationships']['total']}")
    print(f"Total Communities: {data['communities']['total']}")
    print(f"Graph Density: {data['graph_density']}")

    if data["entities"]["total"] > 0:
        print(f"Entity Types: {data['entities']['types']}")
        print(f"Weight Stats: {data['relationships']['weight_stats']}")

    print("✓ Statistics API test passed")


def test_entity_types_api():
    """
    BDD Scenario 3: 實體類型分布 API
    Given: 實體數據包含不同類型的實體
    When: 前端請求 GET /api/entity-types
    Then: 返回類型分布統計和百分比
    """
    print("\n=== Testing GET /api/entity-types ===")
    response = client.get("/api/entity-types")
    print(f"Status Code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response Keys: {data.keys()}")

    # Verify response structure
    assert "types" in data, "Missing 'types' key"
    assert "total_entities" in data, "Missing 'total_entities' key"
    assert "message" in data, "Missing 'message' key"

    print(f"Total Entities: {data['total_entities']}")

    if data["total_entities"] > 0:
        print(f"Number of Entity Types: {len(data['types'])}")
        for entity_type in data["types"]:
            assert "type" in entity_type, "Missing 'type' field"
            assert "count" in entity_type, "Missing 'count' field"
            assert "percentage" in entity_type, "Missing 'percentage' field"
            print(f"  - {entity_type['type']}: {entity_type['count']} ({entity_type['percentage']}%)")

    print("✓ Entity Types API test passed")


def test_top_relationships_api():
    """
    BDD Scenario 5: 關係權重排行
    Given: 關係數據包含權重和排名信息
    When: 前端請求 GET /api/relationships/top
    Then: 返回按權重排序的前 10 個重要關係
    """
    print("\n=== Testing GET /api/relationships/top ===")
    response = client.get("/api/relationships/top")
    print(f"Status Code: {response.status_code}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response Keys: {data.keys()}")

    # Verify response structure
    assert "relationships" in data, "Missing 'relationships' key"
    assert "total" in data, "Missing 'total' key"
    assert "message" in data, "Missing 'message' key"

    print(f"Total Relationships in DB: {data['total']}")
    print(f"Top Relationships Returned: {len(data['relationships'])}")

    # Verify we get max 10 relationships
    assert len(data["relationships"]) <= 10, "Should return max 10 relationships"

    if len(data["relationships"]) > 0:
        print("\nTop Relationships:")
        for rel in data["relationships"][:5]:  # Show first 5
            assert "rank" in rel, "Missing 'rank' field"
            assert "source" in rel, "Missing 'source' field"
            assert "target" in rel, "Missing 'target' field"
            assert "weight" in rel, "Missing 'weight' field"
            print(f"  #{rel['rank']}: {rel['source']} -> {rel['target']} (weight: {rel['weight']})")

        # Verify weights are sorted in descending order
        weights = [rel["weight"] for rel in data["relationships"]]
        assert weights == sorted(weights, reverse=True), "Relationships should be sorted by weight descending"

    print("✓ Top Relationships API test passed")


def run_all_tests():
    """Run all BDD test scenarios"""
    print("=" * 70)
    print("GraphRAG Core Output Integration BDD Tests")
    print("=" * 70)

    try:
        test_communities_api()
        test_statistics_api()
        test_entity_types_api()
        test_top_relationships_api()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - BDD specifications satisfied")
        print("=" * 70)
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
