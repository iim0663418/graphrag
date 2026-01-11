#!/usr/bin/env python3
"""
GraphRAG UI 搜尋功能端到端測試
驗收規格：
- Given 使用者已進入搜尋頁且後端索引可用
  When 輸入有效查詢並提交
  Then 顯示搜尋結果列表且包含相關性排序或摘要
- Given 已執行一次搜尋
  When 變更查詢條件或重新提交
  Then 結果更新且不出現舊資料殘留或 UI 異常
- Given 提交無結果的查詢
  When 搜尋完成
  Then 顯示「無結果」狀態與下一步建議
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List

class SearchE2ETester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results = {
            "success": True,
            "tests": []
        }

    def test_global_search_valid_query(self):
        """測試全域搜尋 - 有效查詢"""
        print("測試 1: 全域搜尋 - 有效查詢")
        print("-" * 60)

        test_queries = [
            "What is GraphRAG?",
            "人工智慧",
            "machine learning applications"
        ]

        for query in test_queries:
            print(f"\n查詢: '{query}'")

            try:
                response = requests.post(
                    f"{self.backend_url}/api/search/global",
                    json={"query": query, "type": "global"},
                    timeout=30
                )

                test_result = {
                    "name": f"全域搜尋 - '{query}'",
                    "query": query,
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }

                if response.status_code == 200:
                    data = response.json()
                    test_result["response"] = data

                    # 驗證回應格式
                    if "response" not in data:
                        self.results["success"] = False
                        test_result["status"] = "FAIL"
                        test_result["error"] = "回應缺少 'response' 欄位"
                        print(f"❌ FAIL - {test_result['error']}")
                    else:
                        print(f"✅ PASS - 搜尋成功")
                        print(f"   狀態碼: {response.status_code}")
                        print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                        print(f"   回應長度: {len(data['response'])} 字元")
                        print(f"   回應預覽: {data['response'][:200]}...")
                else:
                    self.results["success"] = False
                    test_result["error"] = f"非預期狀態碼: {response.status_code}"
                    print(f"❌ FAIL - {test_result['error']}")

                self.results["tests"].append(test_result)

            except Exception as e:
                self.results["success"] = False
                self.results["tests"].append({
                    "name": f"全域搜尋 - '{query}'",
                    "query": query,
                    "status": "FAIL",
                    "error": str(e)
                })
                print(f"❌ FAIL - {str(e)}")

            time.sleep(1)  # 避免過快請求

        print()

    def test_local_search_valid_query(self):
        """測試本地搜尋 - 有效查詢"""
        print("測試 2: 本地搜尋 - 有效查詢")
        print("-" * 60)

        query = "specific information about GraphRAG"
        print(f"\n查詢: '{query}'")

        try:
            response = requests.post(
                f"{self.backend_url}/api/search/local",
                json={"query": query, "type": "local"},
                timeout=30
            )

            test_result = {
                "name": "本地搜尋 - 有效查詢",
                "query": query,
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 200:
                data = response.json()
                test_result["response"] = data

                if "response" not in data:
                    self.results["success"] = False
                    test_result["status"] = "FAIL"
                    test_result["error"] = "回應缺少 'response' 欄位"
                    print(f"❌ FAIL - {test_result['error']}")
                else:
                    print(f"✅ PASS - 搜尋成功")
                    print(f"   狀態碼: {response.status_code}")
                    print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                    print(f"   回應長度: {len(data['response'])} 字元")
                    print(f"   回應預覽: {data['response'][:200]}...")
            else:
                self.results["success"] = False
                test_result["error"] = f"非預期狀態碼: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "本地搜尋 - 有效查詢",
                "query": query,
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_sequential_searches(self):
        """測試連續搜尋 - 驗證結果更新"""
        print("測試 3: 連續搜尋 - 驗證結果更新")
        print("-" * 60)

        queries = [
            "first query about AI",
            "second query about machine learning",
            "third query about data science"
        ]

        previous_response = None

        for i, query in enumerate(queries, 1):
            print(f"\n第 {i} 次搜尋: '{query}'")

            try:
                response = requests.post(
                    f"{self.backend_url}/api/search/global",
                    json={"query": query, "type": "global"},
                    timeout=30
                )

                test_result = {
                    "name": f"連續搜尋 - 第 {i} 次",
                    "query": query,
                    "status": "PASS" if response.status_code == 200 else "FAIL",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }

                if response.status_code == 200:
                    data = response.json()
                    current_response = data.get("response", "")

                    # 驗證結果與前次不同（確保更新）
                    if previous_response is not None:
                        if current_response == previous_response:
                            test_result["status"] = "WARNING"
                            test_result["warning"] = "回應與前次相同，可能未正確更新"
                            print(f"⚠️  WARNING - {test_result['warning']}")
                        else:
                            print(f"✅ PASS - 結果已更新")

                    print(f"   狀態碼: {response.status_code}")
                    print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                    print(f"   回應長度: {len(current_response)} 字元")

                    previous_response = current_response
                else:
                    self.results["success"] = False
                    test_result["error"] = f"非預期狀態碼: {response.status_code}"
                    print(f"❌ FAIL - {test_result['error']}")

                self.results["tests"].append(test_result)

            except Exception as e:
                self.results["success"] = False
                self.results["tests"].append({
                    "name": f"連續搜尋 - 第 {i} 次",
                    "query": query,
                    "status": "FAIL",
                    "error": str(e)
                })
                print(f"❌ FAIL - {str(e)}")

            time.sleep(1)

        print()

    def test_empty_query_handling(self):
        """測試空查詢處理"""
        print("測試 4: 空查詢處理")
        print("-" * 60)

        try:
            response = requests.post(
                f"{self.backend_url}/api/search/global",
                json={"query": "", "type": "global"},
                timeout=5
            )

            test_result = {
                "name": "空查詢處理",
                "query": "",
                "status": "PASS" if response.status_code == 400 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 400:
                error_data = response.json()
                test_result["response"] = error_data
                print(f"✅ PASS - 正確拒絕空查詢")
                print(f"   狀態碼: {response.status_code}")
                print(f"   錯誤訊息: {error_data.get('detail', 'N/A')}")
            else:
                self.results["success"] = False
                test_result["error"] = f"應返回 400，實際返回: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "空查詢處理",
                "query": "",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_whitespace_query_handling(self):
        """測試純空白查詢處理"""
        print("測試 5: 純空白查詢處理")
        print("-" * 60)

        try:
            response = requests.post(
                f"{self.backend_url}/api/search/global",
                json={"query": "   ", "type": "global"},
                timeout=5
            )

            test_result = {
                "name": "純空白查詢處理",
                "query": "   ",
                "status": "PASS" if response.status_code == 400 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 400:
                error_data = response.json()
                test_result["response"] = error_data
                print(f"✅ PASS - 正確拒絕純空白查詢")
                print(f"   狀態碼: {response.status_code}")
                print(f"   錯誤訊息: {error_data.get('detail', 'N/A')}")
            else:
                self.results["success"] = False
                test_result["error"] = f"應返回 400，實際返回: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "純空白查詢處理",
                "query": "   ",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def run_all_tests(self):
        """執行所有測試"""
        print("=" * 60)
        print("GraphRAG UI 搜尋功能端到端測試")
        print("=" * 60)
        print(f"後端 URL: {self.backend_url}")
        print("=" * 60)
        print()

        self.test_global_search_valid_query()
        self.test_local_search_valid_query()
        self.test_sequential_searches()
        self.test_empty_query_handling()
        self.test_whitespace_query_handling()

        return self.results

    def print_summary(self):
        """輸出測試摘要"""
        print("=" * 60)
        print("測試摘要")
        print("=" * 60)

        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["status"] == "PASS")
        warnings = sum(1 for t in self.results["tests"] if t["status"] == "WARNING")
        failed = sum(1 for t in self.results["tests"] if t["status"] == "FAIL")

        print(f"總測試數: {total}")
        print(f"通過: {passed}")
        print(f"警告: {warnings}")
        print(f"失敗: {failed}")
        print()

        if self.results["success"]:
            print("✅ 搜尋功能端到端測試通過")
            print("   - 有效查詢正確處理")
            print("   - 連續搜尋結果正確更新")
            print("   - 錯誤查詢適當處理")
            if warnings > 0:
                print(f"   ⚠️  但有 {warnings} 個警告需要注意")
        else:
            print("❌ 搜尋功能端到端測試失敗")
            print("   請檢查上方錯誤詳情")

        print("=" * 60)

def main():
    backend_url = "http://localhost:8000"

    tester = SearchE2ETester(backend_url)
    results = tester.run_all_tests()
    tester.print_summary()

    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main()
