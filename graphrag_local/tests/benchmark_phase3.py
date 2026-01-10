#!/usr/bin/env python3
"""
Benchmark Script for Phase 3 Performance Optimization.

This script benchmarks the performance improvements from Phase 3 optimizations:
- Intelligent caching
- Batch processing
- Adaptive sizing

Target: 30%+ reduction in LLM calls and improved indexing speed.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graphrag_local.optimization.cache_manager import (
    HashBasedCache,
    MultiLevelCache,
    EntityRelationshipCache,
)
from graphrag_local.optimization.batch_processor import (
    BatchConfig,
    BatchProcessor,
    AdaptiveBatchProcessor,
    TextChunkBatcher,
    DedupBatchProcessor,
)
from graphrag_local.optimization.performance_monitor import (
    PerformanceMonitor,
    ComparisonAnalyzer,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


class BenchmarkSuite:
    """Comprehensive benchmark suite for Phase 3 optimizations."""

    def __init__(self, output_dir: str = ".benchmark_results"):
        """
        Initialize benchmark suite.

        Args:
            output_dir: Directory to save benchmark results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test data
        self.test_texts = self._generate_test_data()

        log.info(f"✓ Initialized benchmark suite with {len(self.test_texts)} test texts")

    def _generate_test_data(self, count: int = 1000) -> List[str]:
        """
        Generate test data for benchmarking.

        Args:
            count: Number of test texts to generate

        Returns:
            List of test text strings
        """
        texts = []

        # Base texts with variations
        base_texts = [
            "The quick brown fox jumps over the lazy dog.",
            "GraphRAG is a knowledge graph indexing system.",
            "Entity extraction identifies named entities in text.",
            "Relationship extraction finds connections between entities.",
            "Community detection groups related entities together.",
        ]

        for i in range(count):
            # Create variations with some duplicates (20% duplication rate)
            if i % 5 == 0 and i > 0:
                # Duplicate from earlier
                texts.append(texts[i // 5])
            else:
                base = base_texts[i % len(base_texts)]
                variation = f"{base} Sample {i}."
                texts.append(variation)

        return texts

    def benchmark_cache_performance(self) -> Dict[str, Any]:
        """
        Benchmark cache performance.

        Returns:
            Benchmark results
        """
        log.info("Running cache performance benchmark...")

        results = {}

        # Test 1: Hash-based cache
        cache = HashBasedCache(
            cache_dir=str(self.output_dir / "cache_test"),
            ttl_seconds=None,
            max_size_mb=100,
        )

        start = time.time()
        for text in self.test_texts:
            # Simulate LLM result
            result = f"processed: {text}"
            cache.set(text, result)

        write_time = time.time() - start

        start = time.time()
        hits = 0
        for text in self.test_texts:
            result = cache.get(text)
            if result is not None:
                hits += 1

        read_time = time.time() - start

        results["hash_cache"] = {
            "write_time_s": write_time,
            "read_time_s": read_time,
            "hit_rate": (hits / len(self.test_texts)) * 100,
            "stats": cache.get_stats(),
        }

        # Test 2: Multi-level cache
        ml_cache = MultiLevelCache(
            cache_dir=str(self.output_dir / "ml_cache_test"),
            l1_max_entries=500,
            l2_max_size_mb=100,
        )

        start = time.time()
        for text in self.test_texts:
            result = f"processed: {text}"
            ml_cache.set(text, result)

        ml_write_time = time.time() - start

        start = time.time()
        l1_hits = 0
        l2_hits = 0
        for text in self.test_texts:
            result = ml_cache.get(text)
            if result is not None:
                # Check which level hit
                if text[:20] in str(ml_cache.l1_cache):
                    l1_hits += 1
                else:
                    l2_hits += 1

        ml_read_time = time.time() - start

        results["multilevel_cache"] = {
            "write_time_s": ml_write_time,
            "read_time_s": ml_read_time,
            "l1_hits": l1_hits,
            "l2_hits": l2_hits,
            "stats": ml_cache.get_stats(),
        }

        log.info(f"✓ Cache benchmark complete")
        return results

    async def benchmark_batch_processing(self) -> Dict[str, Any]:
        """
        Benchmark batch processing performance.

        Returns:
            Benchmark results
        """
        log.info("Running batch processing benchmark...")

        results = {}

        # Mock LLM processing function
        def mock_llm_batch(texts: List[str]) -> List[str]:
            """Simulate batch LLM processing."""
            time.sleep(0.01 * len(texts))  # Simulate processing time
            return [f"LLM: {t}" for t in texts]

        # Test 1: No batching (baseline)
        start = time.time()
        baseline_results = []
        for text in self.test_texts[:100]:  # Use subset for speed
            result = mock_llm_batch([text])[0]
            baseline_results.append(result)
        baseline_time = time.time() - start

        results["baseline_no_batching"] = {
            "time_s": baseline_time,
            "calls": len(self.test_texts[:100]),
        }

        # Test 2: Static batch processing
        config = BatchConfig(
            min_batch_size=1,
            max_batch_size=16,
            max_wait_time_ms=50.0,
            adaptive_sizing=False,
        )
        processor = BatchProcessor(config=config)

        start = time.time()
        tasks = [
            processor.process(text, mock_llm_batch)
            for text in self.test_texts[:100]
        ]
        batch_results = await asyncio.gather(*tasks)
        await processor.flush(mock_llm_batch)
        batch_time = time.time() - start

        results["static_batching"] = {
            "time_s": batch_time,
            "speedup": baseline_time / batch_time if batch_time > 0 else 0,
            "stats": processor.get_stats(),
        }

        # Test 3: Adaptive batch processing
        adaptive_config = BatchConfig(
            min_batch_size=1,
            max_batch_size=32,
            max_wait_time_ms=50.0,
            adaptive_sizing=True,
        )
        adaptive_processor = AdaptiveBatchProcessor(config=adaptive_config)

        start = time.time()
        tasks = [
            adaptive_processor.process(text, mock_llm_batch)
            for text in self.test_texts[:100]
        ]
        adaptive_results = await asyncio.gather(*tasks)
        await adaptive_processor.flush(mock_llm_batch)
        adaptive_time = time.time() - start

        results["adaptive_batching"] = {
            "time_s": adaptive_time,
            "speedup": baseline_time / adaptive_time if adaptive_time > 0 else 0,
            "optimal_size": adaptive_processor.get_optimal_size(),
            "stats": adaptive_processor.get_stats(),
        }

        # Test 4: Deduplication
        dedup = DedupBatchProcessor()

        start = time.time()
        dedup_results = await dedup.process_batch(
            self.test_texts[:100],
            mock_llm_batch,
        )
        dedup_time = time.time() - start

        results["deduplication"] = {
            "time_s": dedup_time,
            "speedup": baseline_time / dedup_time if dedup_time > 0 else 0,
            "stats": dedup.get_stats(),
        }

        log.info(f"✓ Batch processing benchmark complete")
        return results

    async def benchmark_integrated_optimization(self) -> Dict[str, Any]:
        """
        Benchmark integrated caching + batching + deduplication.

        Returns:
            Benchmark results
        """
        log.info("Running integrated optimization benchmark...")

        monitor = PerformanceMonitor()

        # Setup
        cache = MultiLevelCache(
            cache_dir=str(self.output_dir / "integrated_cache"),
            l1_max_entries=500,
            l2_max_size_mb=100,
        )

        config = BatchConfig(
            min_batch_size=1,
            max_batch_size=16,
            max_wait_time_ms=100.0,
            adaptive_sizing=True,
            enable_cache_dedup=True,
        )

        processor = AdaptiveBatchProcessor(config=config, cache=cache)
        dedup = DedupBatchProcessor()

        # Mock processing function
        def mock_process(texts: List[str]) -> List[str]:
            time.sleep(0.01 * len(texts))
            return [f"processed: {t}" for t in texts]

        # Run benchmark
        with monitor.track("integrated_optimization"):
            # Process with deduplication first
            unique_texts = list(set(self.test_texts[:200]))

            tasks = []
            for text in self.test_texts[:200]:
                tasks.append(processor.process(text, mock_process))

            results = await asyncio.gather(*tasks)
            await processor.flush(mock_process)

        # Calculate metrics
        monitor.calculate_efficiency(
            total_items=len(self.test_texts[:200]),
            baseline_llm_calls=len(self.test_texts[:200]),
        )

        monitor.update_cache_metrics(
            cache_size_mb=cache.get_stats()["l2_stats"]["size_bytes"] / (1024 * 1024),
            cache_hit_rate=cache.get_stats()["hit_rate"],
        )

        return {
            "performance": monitor.get_summary(),
            "cache_stats": cache.get_stats(),
            "batch_stats": processor.get_stats(),
        }

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all benchmarks and generate comprehensive report.

        Returns:
            Complete benchmark results
        """
        log.info("=" * 70)
        log.info("PHASE 3 PERFORMANCE OPTIMIZATION BENCHMARK")
        log.info("=" * 70)

        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_data_size": len(self.test_texts),
        }

        # Run benchmarks
        results["cache"] = self.benchmark_cache_performance()

        # Run async benchmarks
        loop = asyncio.get_event_loop()
        results["batching"] = loop.run_until_complete(
            self.benchmark_batch_processing()
        )
        results["integrated"] = loop.run_until_complete(
            self.benchmark_integrated_optimization()
        )

        # Save results
        output_file = self.output_dir / "benchmark_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        log.info(f"✓ Saved benchmark results to {output_file}")

        # Print summary
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)

        print("\n📊 Cache Performance:")
        hash_cache = results["cache"]["hash_cache"]
        print(f"  Hash Cache Hit Rate: {hash_cache['hit_rate']:.1f}%")
        print(f"  Write Time: {hash_cache['write_time_s']:.2f}s")
        print(f"  Read Time: {hash_cache['read_time_s']:.2f}s")

        ml_cache = results["cache"]["multilevel_cache"]
        print(f"\n  Multi-Level Cache:")
        print(f"    L1 Hits: {ml_cache['l1_hits']}")
        print(f"    L2 Hits: {ml_cache['l2_hits']}")
        print(f"    Total Hit Rate: {ml_cache['stats']['hit_rate']:.1f}%")

        print("\n🚀 Batch Processing:")
        batching = results["batching"]
        print(f"  Static Batching Speedup: {batching['static_batching']['speedup']:.2f}x")
        print(f"  Adaptive Batching Speedup: {batching['adaptive_batching']['speedup']:.2f}x")
        print(f"  Deduplication Speedup: {batching['deduplication']['speedup']:.2f}x")
        print(f"  Optimal Batch Size: {batching['adaptive_batching']['optimal_size']}")

        print("\n⚡ Integrated Optimization:")
        perf = results["integrated"]["performance"]
        cache_stats = results["integrated"]["cache_stats"]
        print(f"  Cache Hit Rate: {cache_stats['hit_rate']:.1f}%")
        print(f"  Avg Batch Size: {perf['batching']['avg_batch_size']:.1f}")
        print(f"  Throughput: {perf['efficiency']['throughput_items_per_sec']:.2f} items/sec")

        # Target achievement
        print("\n🎯 Phase 3 Target Status:")
        # Estimate LLM call reduction based on cache hit rate and deduplication
        dedup_savings = batching['deduplication']['stats']['dedup_savings_rate']
        cache_hit_rate = cache_stats['hit_rate']
        estimated_reduction = (dedup_savings + cache_hit_rate) / 2

        target = 30.0
        if estimated_reduction >= target:
            print(f"  ✓ ACHIEVED: ~{estimated_reduction:.1f}% reduction (target: {target}%)")
        else:
            print(f"  ⚠ PARTIAL: ~{estimated_reduction:.1f}% reduction (target: {target}%)")
            print(f"    Note: Actual reduction may vary with real workload")

        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="Benchmark Phase 3 Performance Optimizations"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".benchmark_results",
        help="Directory to save benchmark results"
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=1000,
        help="Number of test texts to generate"
    )

    args = parser.parse_args()

    # Run benchmarks
    suite = BenchmarkSuite(output_dir=args.output_dir)
    results = suite.run_all_benchmarks()

    return 0


if __name__ == "__main__":
    sys.exit(main())
