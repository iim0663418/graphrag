#!/usr/bin/env python3
"""
GraphRAG UI 後端健康檢查腳本
Given 後端服務已啟動
When 呼叫核心 API 端點（如 `/health` 或 `/api/status`）
Then 回應內容包含版本/狀態資訊且格式正確
"""

import requests
import sys
import json
from typing import Dict, Any

def check_health(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """執行健康檢查並返回結果"""
    results = {
        "success": True,
        "checks": []
    }

    # 檢查 1: 根端點
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        check_1 = {
            "name": "根端點檢查 (/)",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else None
        }
        results["checks"].append(check_1)

        if response.status_code != 200:
            results["success"] = False

        # 驗證回應格式
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, dict) or "message" not in data:
                check_1["status"] = "FAIL"
                check_1["error"] = "回應格式不正確"
                results["success"] = False

    except Exception as e:
        results["checks"].append({
            "name": "根端點檢查 (/)",
            "status": "FAIL",
            "error": str(e)
        })
        results["success"] = False

    # 檢查 2: API 文檔端點
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        check_2 = {
            "name": "API 文檔端點檢查 (/docs)",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code
        }
        results["checks"].append(check_2)

        if response.status_code != 200:
            results["success"] = False

    except Exception as e:
        results["checks"].append({
            "name": "API 文檔端點檢查 (/docs)",
            "status": "FAIL",
            "error": str(e)
        })
        results["success"] = False

    # 檢查 3: 索引狀態端點
    try:
        response = requests.get(f"{base_url}/api/indexing/status", timeout=5)
        check_3 = {
            "name": "索引狀態端點檢查 (/api/indexing/status)",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else None
        }
        results["checks"].append(check_3)

        if response.status_code != 200:
            results["success"] = False

        # 驗證回應格式
        if response.status_code == 200:
            data = response.json()
            required_fields = ["is_indexing", "progress", "message"]
            if not all(field in data for field in required_fields):
                check_3["status"] = "FAIL"
                check_3["error"] = f"回應缺少必要欄位: {required_fields}"
                results["success"] = False

    except Exception as e:
        results["checks"].append({
            "name": "索引狀態端點檢查 (/api/indexing/status)",
            "status": "FAIL",
            "error": str(e)
        })
        results["success"] = False

    return results

def main():
    print("=" * 60)
    print("GraphRAG UI 後端健康檢查")
    print("=" * 60)
    print()

    results = check_health()

    # 輸出結果
    for check in results["checks"]:
        status_symbol = "✅" if check["status"] == "PASS" else "❌"
        print(f"{status_symbol} {check['name']}: {check['status']}")

        if "status_code" in check:
            print(f"   HTTP 狀態碼: {check['status_code']}")

        if "response" in check and check["response"]:
            print(f"   回應內容: {json.dumps(check['response'], ensure_ascii=False, indent=2)}")

        if "error" in check:
            print(f"   錯誤: {check['error']}")

        print()

    # 總結
    print("=" * 60)
    if results["success"]:
        print("✅ 健康檢查通過：所有端點回應正常")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ 健康檢查失敗：部分端點異常")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
