#!/usr/bin/env python3
"""
GraphRAG UI API 連接測試腳本
驗收規格：
- Given 前端已啟動且後端 API 可用
  When 前端發出任一讀取型請求（如索引狀態或預設資料）
  Then 前端成功取得回應且 UI 正確呈現資料
- Given 前端發出 API 請求
  When API 回傳錯誤或逾時
  Then UI 顯示可理解的錯誤提示並不崩潰
"""

import requests
import json
import sys
from typing import Dict, Any

class APIConnectionTester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results = {
            "success": True,
            "tests": []
        }

    def test_basic_connectivity(self):
        """測試基本連接性"""
        print("測試 1: 基本連接性檢查")
        print("-" * 60)

        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)

            test_result = {
                "name": "基本連接性",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 200:
                test_result["response"] = response.json()
                print(f"✅ PASS - 連接成功")
                print(f"   狀態碼: {response.status_code}")
                print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                print(f"   回應內容: {json.dumps(response.json(), ensure_ascii=False)}")
            else:
                self.results["success"] = False
                test_result["error"] = f"非預期狀態碼: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "基本連接性",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_indexing_status(self):
        """測試索引狀態端點（讀取型請求）"""
        print("測試 2: 索引狀態查詢（讀取型請求）")
        print("-" * 60)

        try:
            response = requests.get(
                f"{self.backend_url}/api/indexing/status",
                timeout=5
            )

            test_result = {
                "name": "索引狀態查詢",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 200:
                data = response.json()
                test_result["response"] = data

                # 驗證回應格式
                required_fields = ["is_indexing", "progress", "message"]
                missing_fields = [f for f in required_fields if f not in data]

                if missing_fields:
                    self.results["success"] = False
                    test_result["status"] = "FAIL"
                    test_result["error"] = f"缺少必要欄位: {missing_fields}"
                    print(f"❌ FAIL - {test_result['error']}")
                else:
                    print(f"✅ PASS - 索引狀態查詢成功")
                    print(f"   狀態碼: {response.status_code}")
                    print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                    print(f"   索引進行中: {data['is_indexing']}")
                    print(f"   進度: {data['progress']}%")
                    print(f"   訊息: {data['message']}")
            else:
                self.results["success"] = False
                test_result["error"] = f"非預期狀態碼: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "索引狀態查詢",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_files_list(self):
        """測試文件列表端點"""
        print("測試 3: 文件列表查詢")
        print("-" * 60)

        try:
            response = requests.get(
                f"{self.backend_url}/api/files",
                timeout=5
            )

            test_result = {
                "name": "文件列表查詢",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 200:
                data = response.json()
                test_result["response"] = data
                print(f"✅ PASS - 文件列表查詢成功")
                print(f"   狀態碼: {response.status_code}")
                print(f"   回應時間: {response.elapsed.total_seconds():.3f}s")
                print(f"   文件數量: {len(data)}")
            else:
                self.results["success"] = False
                test_result["error"] = f"非預期狀態碼: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "文件列表查詢",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_error_handling(self):
        """測試錯誤處理"""
        print("測試 4: API 錯誤處理")
        print("-" * 60)

        # 測試空查詢
        try:
            response = requests.post(
                f"{self.backend_url}/api/search/global",
                json={"query": ""},
                timeout=5
            )

            test_result = {
                "name": "空查詢錯誤處理",
                "status": "PASS" if response.status_code == 400 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 400:
                error_data = response.json()
                test_result["response"] = error_data
                print(f"✅ PASS - 正確處理空查詢錯誤")
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
                "name": "空查詢錯誤處理",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def test_invalid_endpoint(self):
        """測試無效端點處理"""
        print("測試 5: 無效端點處理")
        print("-" * 60)

        try:
            response = requests.get(
                f"{self.backend_url}/api/invalid/endpoint",
                timeout=5
            )

            test_result = {
                "name": "無效端點處理",
                "status": "PASS" if response.status_code == 404 else "FAIL",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }

            if response.status_code == 404:
                print(f"✅ PASS - 正確處理無效端點")
                print(f"   狀態碼: {response.status_code}")
            else:
                self.results["success"] = False
                test_result["error"] = f"應返回 404，實際返回: {response.status_code}"
                print(f"❌ FAIL - {test_result['error']}")

            self.results["tests"].append(test_result)

        except Exception as e:
            self.results["success"] = False
            self.results["tests"].append({
                "name": "無效端點處理",
                "status": "FAIL",
                "error": str(e)
            })
            print(f"❌ FAIL - {str(e)}")

        print()

    def run_all_tests(self):
        """執行所有測試"""
        print("=" * 60)
        print("GraphRAG UI API 連接測試")
        print("=" * 60)
        print(f"後端 URL: {self.backend_url}")
        print("=" * 60)
        print()

        self.test_basic_connectivity()
        self.test_indexing_status()
        self.test_files_list()
        self.test_error_handling()
        self.test_invalid_endpoint()

        return self.results

    def print_summary(self):
        """輸出測試摘要"""
        print("=" * 60)
        print("測試摘要")
        print("=" * 60)

        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"] if t["status"] == "PASS")
        failed = total - passed

        print(f"總測試數: {total}")
        print(f"通過: {passed}")
        print(f"失敗: {failed}")
        print()

        if self.results["success"]:
            print("✅ 所有 API 連接測試通過")
            print("   前端可正常與後端通信")
        else:
            print("❌ API 連接測試失敗")
            print("   請檢查後端服務並查看上方錯誤詳情")

        print("=" * 60)

def main():
    backend_url = "http://localhost:8000"

    tester = APIConnectionTester(backend_url)
    results = tester.run_all_tests()
    tester.print_summary()

    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main()
