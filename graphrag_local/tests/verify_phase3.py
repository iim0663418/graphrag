#!/usr/bin/env python3
"""
Phase 3 驗證腳本

驗證 Phase 3 所有組件是否正確安裝和配置。
"""

import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def check_imports():
    """檢查所有模組是否可導入"""
    print("=" * 70)
    print("檢查模組導入...")
    print("=" * 70)

    checks = []

    # 檢查快取管理器
    try:
        from graphrag_local.optimization import (
            HashBasedCache,
            MultiLevelCache,
            EntityRelationshipCache,
            CacheStats,
        )
        print("✓ cache_manager.py 導入成功")
        checks.append(True)
    except Exception as e:
        print(f"✗ cache_manager.py 導入失敗: {e}")
        checks.append(False)

    # 檢查批次處理器
    try:
        from graphrag_local.optimization import (
            BatchConfig,
            BatchProcessor,
            AdaptiveBatchProcessor,
            TextChunkBatcher,
            DedupBatchProcessor,
        )
        print("✓ batch_processor.py 導入成功")
        checks.append(True)
    except Exception as e:
        print(f"✗ batch_processor.py 導入失敗: {e}")
        checks.append(False)

    # 檢查效能監控
    try:
        from graphrag_local.optimization import (
            PerformanceMonitor,
            PerformanceMetrics,
            ComparisonAnalyzer,
        )
        print("✓ performance_monitor.py 導入成功")
        checks.append(True)
    except Exception as e:
        print(f"✗ performance_monitor.py 導入失敗: {e}")
        checks.append(False)

    # 檢查優化適配器
    try:
        from graphrag_local.adapters import (
            OptimizedLMStudioChatAdapter,
            OptimizedLMStudioEmbeddingAdapter,
        )
        print("✓ lmstudio_optimized.py 導入成功")
        checks.append(True)
    except Exception as e:
        print(f"✗ lmstudio_optimized.py 導入失敗: {e}")
        checks.append(False)

    return all(checks)


def test_cache_functionality():
    """測試快取功能"""
    print("\n" + "=" * 70)
    print("測試快取功能...")
    print("=" * 70)

    try:
        from graphrag_local.optimization import HashBasedCache
        import tempfile
        import shutil

        # 創建臨時目錄
        temp_dir = tempfile.mkdtemp()

        try:
            # 測試快取
            cache = HashBasedCache(cache_dir=temp_dir, enable_persistence=True)

            # 寫入測試
            cache.set("test_key", "test_value")
            result = cache.get("test_key")

            if result == "test_value":
                print("✓ 快取讀寫測試通過")

                # 統計測試
                stats = cache.get_stats()
                if stats["hits"] == 1 and stats["misses"] == 0:
                    print("✓ 快取統計測試通過")
                    return True
                else:
                    print(f"✗ 快取統計不正確: {stats}")
                    return False
            else:
                print(f"✗ 快取讀取值不正確: {result}")
                return False

        finally:
            # 清理
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"✗ 快取功能測試失敗: {e}")
        return False


def test_batch_processor():
    """測試批次處理器"""
    print("\n" + "=" * 70)
    print("測試批次處理器...")
    print("=" * 70)

    try:
        from graphrag_local.optimization import BatchConfig, BatchProcessor
        import asyncio

        # 模擬批次處理函數
        def mock_batch_fn(items):
            return [f"processed: {item}" for item in items]

        config = BatchConfig(
            min_batch_size=1,
            max_batch_size=10,
            max_wait_time_ms=50.0
        )

        processor = BatchProcessor(config=config)

        # 測試處理
        async def test():
            tasks = [
                processor.process(f"item_{i}", mock_batch_fn)
                for i in range(5)
            ]
            results = await asyncio.gather(*tasks)
            await processor.flush(mock_batch_fn)
            return results

        results = asyncio.run(test())

        if len(results) == 5 and results[0] == "processed: item_0":
            print("✓ 批次處理測試通過")

            # 統計測試
            stats = processor.get_stats()
            if stats["total_batches"] > 0:
                print(f"✓ 批次統計測試通過 (批次數: {stats['total_batches']})")
                return True
            else:
                print(f"✗ 批次統計不正確: {stats}")
                return False
        else:
            print(f"✗ 批次處理結果不正確: {results}")
            return False

    except Exception as e:
        print(f"✗ 批次處理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_monitor():
    """測試效能監控"""
    print("\n" + "=" * 70)
    print("測試效能監控...")
    print("=" * 70)

    try:
        from graphrag_local.optimization import PerformanceMonitor
        import time

        monitor = PerformanceMonitor(enable_memory_tracking=False)

        # 測試計時
        with monitor.track("test_operation"):
            time.sleep(0.1)

        # 記錄調用
        monitor.record_llm_call(duration_s=0.5, cached=False)
        monitor.record_llm_call(duration_s=0.1, cached=True)

        # 獲取指標
        metrics = monitor.get_metrics()

        if metrics.total_llm_calls == 2 and metrics.cached_llm_hits == 1:
            print("✓ 效能監控測試通過")
            print(f"  - LLM 調用: {metrics.total_llm_calls}")
            print(f"  - 快取命中: {metrics.cached_llm_hits}")
            return True
        else:
            print(f"✗ 效能監控指標不正確: {metrics}")
            return False

    except Exception as e:
        print(f"✗ 效能監控測試失敗: {e}")
        return False


def check_documentation():
    """檢查文檔是否存在"""
    print("\n" + "=" * 70)
    print("檢查文檔...")
    print("=" * 70)

    docs = [
        "docs/phase3_optimization_guide.md",
        "docs/PHASE3_IMPLEMENTATION_SUMMARY.md",
        "graphrag_local/optimization/README.md",
    ]

    checks = []
    for doc in docs:
        doc_path = Path(__file__).parent.parent.parent / doc
        if doc_path.exists():
            print(f"✓ {doc}")
            checks.append(True)
        else:
            print(f"✗ {doc} 不存在")
            checks.append(False)

    return all(checks)


def check_files():
    """檢查所有必需檔案是否存在"""
    print("\n" + "=" * 70)
    print("檢查檔案...")
    print("=" * 70)

    required_files = [
        "graphrag_local/optimization/__init__.py",
        "graphrag_local/optimization/cache_manager.py",
        "graphrag_local/optimization/batch_processor.py",
        "graphrag_local/optimization/performance_monitor.py",
        "graphrag_local/adapters/lmstudio_optimized.py",
        "graphrag_local/tests/benchmark_phase3.py",
    ]

    checks = []
    for file_path in required_files:
        full_path = Path(__file__).parent.parent.parent / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"✓ {file_path} ({size_kb:.1f} KB)")
            checks.append(True)
        else:
            print(f"✗ {file_path} 不存在")
            checks.append(False)

    return all(checks)


def main():
    """主函數"""
    print("\n" + "=" * 70)
    print("Phase 3 效能優化驗證")
    print("=" * 70)

    results = {
        "檔案檢查": check_files(),
        "模組導入": check_imports(),
        "快取功能": test_cache_functionality(),
        "批次處理": test_batch_processor(),
        "效能監控": test_performance_monitor(),
        "文檔檢查": check_documentation(),
    }

    # 輸出總結
    print("\n" + "=" * 70)
    print("驗證總結")
    print("=" * 70)

    all_passed = True
    for name, passed in results.items():
        status = "✓ 通過" if passed else "✗ 失敗"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有檢查通過！Phase 3 已成功實作。")
        print("\n下一步:")
        print("  1. 運行基準測試: python graphrag_local/tests/benchmark_phase3.py")
        print("  2. 閱讀使用指南: docs/phase3_optimization_guide.md")
        print("  3. 整合到實際工作流程")
    else:
        print("⚠️  部分檢查失敗，請查看上述錯誤信息。")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
