"""
Performance Monitoring for GraphRAG Local Optimization.

This module provides comprehensive performance tracking and analysis tools
for monitoring indexing efficiency, LLM call reduction, and cache effectiveness.

Phase 3: Performance Optimization
"""

import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    # Timing metrics
    total_duration_s: float = 0.0
    llm_call_duration_s: float = 0.0
    embedding_duration_s: float = 0.0
    cache_lookup_duration_s: float = 0.0

    # Call count metrics
    total_llm_calls: int = 0
    total_embedding_calls: int = 0
    cached_llm_hits: int = 0
    cached_embedding_hits: int = 0

    # Batch metrics
    total_batches: int = 0
    avg_batch_size: float = 0.0
    max_batch_size: int = 0

    # Token metrics
    total_tokens_processed: int = 0
    total_tokens_generated: int = 0

    # Cache metrics
    cache_size_mb: float = 0.0
    cache_hit_rate: float = 0.0

    # Efficiency metrics
    llm_call_reduction: float = 0.0  # Percentage
    throughput_items_per_sec: float = 0.0

    # Memory metrics
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "timing": {
                "total_duration_s": round(self.total_duration_s, 2),
                "llm_call_duration_s": round(self.llm_call_duration_s, 2),
                "embedding_duration_s": round(self.embedding_duration_s, 2),
                "cache_lookup_duration_s": round(self.cache_lookup_duration_s, 2),
            },
            "calls": {
                "total_llm_calls": self.total_llm_calls,
                "total_embedding_calls": self.total_embedding_calls,
                "cached_llm_hits": self.cached_llm_hits,
                "cached_embedding_hits": self.cached_embedding_hits,
            },
            "batching": {
                "total_batches": self.total_batches,
                "avg_batch_size": round(self.avg_batch_size, 2),
                "max_batch_size": self.max_batch_size,
            },
            "tokens": {
                "total_processed": self.total_tokens_processed,
                "total_generated": self.total_tokens_generated,
            },
            "cache": {
                "size_mb": round(self.cache_size_mb, 2),
                "hit_rate": round(self.cache_hit_rate, 2),
            },
            "efficiency": {
                "llm_call_reduction": round(self.llm_call_reduction, 2),
                "throughput_items_per_sec": round(self.throughput_items_per_sec, 2),
            },
            "memory": {
                "peak_mb": round(self.peak_memory_mb, 2),
                "avg_mb": round(self.avg_memory_mb, 2),
            }
        }


class PerformanceMonitor:
    """
    Monitor and track performance metrics during GraphRAG indexing.

    Tracks LLM calls, cache hits, batch efficiency, and overall throughput.
    """

    def __init__(
        self,
        enable_memory_tracking: bool = True,
        enable_detailed_logging: bool = True,
    ):
        """
        Initialize performance monitor.

        Args:
            enable_memory_tracking: Track memory usage
            enable_detailed_logging: Enable detailed performance logs
        """
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_detailed_logging = enable_detailed_logging

        # Metrics
        self.metrics = PerformanceMetrics()

        # Timing trackers
        self._timers: Dict[str, float] = {}
        self._timer_stack: List[str] = []

        # Memory tracking
        if enable_memory_tracking:
            try:
                import psutil
                self._process = psutil.Process()
                self._memory_samples: List[float] = []
            except ImportError:
                log.warning("psutil not available, memory tracking disabled")
                self.enable_memory_tracking = False

        # Start time
        self._start_time = time.time()

        log.info("✓ Performance monitor initialized")

    @contextmanager
    def track(self, operation: str):
        """
        Context manager for tracking operation duration.

        Args:
            operation: Name of the operation to track

        Example:
            with monitor.track("entity_extraction"):
                extract_entities(text)
        """
        start = time.time()
        self._timer_stack.append(operation)

        try:
            yield
        finally:
            duration = time.time() - start
            self._timers[operation] = self._timers.get(operation, 0.0) + duration
            self._timer_stack.pop()

            if self.enable_detailed_logging:
                log.debug(f"{operation} took {duration:.2f}s")

            # Sample memory if enabled
            if self.enable_memory_tracking:
                self._sample_memory()

    def record_llm_call(
        self,
        duration_s: float,
        cached: bool = False,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
    ) -> None:
        """
        Record an LLM call.

        Args:
            duration_s: Call duration in seconds
            cached: Whether result came from cache
            tokens_in: Input tokens
            tokens_out: Generated tokens
        """
        self.metrics.total_llm_calls += 1
        self.metrics.llm_call_duration_s += duration_s

        if cached:
            self.metrics.cached_llm_hits += 1

        if tokens_in:
            self.metrics.total_tokens_processed += tokens_in

        if tokens_out:
            self.metrics.total_tokens_generated += tokens_out

    def record_embedding_call(
        self,
        duration_s: float,
        cached: bool = False,
        count: int = 1,
    ) -> None:
        """
        Record an embedding call.

        Args:
            duration_s: Call duration in seconds
            cached: Whether result came from cache
            count: Number of texts embedded
        """
        self.metrics.total_embedding_calls += count
        self.metrics.embedding_duration_s += duration_s

        if cached:
            self.metrics.cached_embedding_hits += count

    def record_batch(self, batch_size: int) -> None:
        """
        Record a batch operation.

        Args:
            batch_size: Number of items in batch
        """
        self.metrics.total_batches += 1
        self.metrics.max_batch_size = max(self.metrics.max_batch_size, batch_size)

        # Update average batch size
        total_items = (
            self.metrics.avg_batch_size * (self.metrics.total_batches - 1) +
            batch_size
        )
        self.metrics.avg_batch_size = total_items / self.metrics.total_batches

    def record_cache_lookup(self, duration_s: float) -> None:
        """Record cache lookup duration."""
        self.metrics.cache_lookup_duration_s += duration_s

    def _sample_memory(self) -> None:
        """Sample current memory usage."""
        if not self.enable_memory_tracking:
            return

        try:
            mem_info = self._process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            self._memory_samples.append(mem_mb)

            self.metrics.peak_memory_mb = max(self.metrics.peak_memory_mb, mem_mb)

            # Update average
            if self._memory_samples:
                self.metrics.avg_memory_mb = sum(self._memory_samples) / len(self._memory_samples)

        except Exception as e:
            log.warning(f"Memory sampling failed: {e}")

    def update_cache_metrics(
        self,
        cache_size_mb: float,
        cache_hit_rate: float,
    ) -> None:
        """
        Update cache-related metrics.

        Args:
            cache_size_mb: Current cache size in MB
            cache_hit_rate: Cache hit rate percentage
        """
        self.metrics.cache_size_mb = cache_size_mb
        self.metrics.cache_hit_rate = cache_hit_rate

    def calculate_efficiency(
        self,
        total_items: int,
        baseline_llm_calls: Optional[int] = None,
    ) -> None:
        """
        Calculate efficiency metrics.

        Args:
            total_items: Total number of items processed
            baseline_llm_calls: Expected LLM calls without optimization
        """
        # Calculate duration
        self.metrics.total_duration_s = time.time() - self._start_time

        # Calculate throughput
        if self.metrics.total_duration_s > 0:
            self.metrics.throughput_items_per_sec = (
                total_items / self.metrics.total_duration_s
            )

        # Calculate LLM call reduction
        if baseline_llm_calls:
            actual_calls = self.metrics.total_llm_calls
            reduction = ((baseline_llm_calls - actual_calls) / baseline_llm_calls * 100)
            self.metrics.llm_call_reduction = max(0.0, reduction)

    def get_metrics(self) -> PerformanceMetrics:
        """Get current metrics."""
        return self.metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = self.metrics.to_dict()

        # Add timer breakdown
        summary["timings_breakdown"] = {
            name: round(duration, 2)
            for name, duration in self._timers.items()
        }

        return summary

    def print_summary(self) -> None:
        """Print performance summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)

        print(f"\nTiming:")
        print(f"  Total Duration: {summary['timing']['total_duration_s']:.2f}s")
        print(f"  LLM Calls: {summary['timing']['llm_call_duration_s']:.2f}s")
        print(f"  Embeddings: {summary['timing']['embedding_duration_s']:.2f}s")
        print(f"  Cache Lookups: {summary['timing']['cache_lookup_duration_s']:.2f}s")

        print(f"\nCalls:")
        print(f"  Total LLM Calls: {summary['calls']['total_llm_calls']}")
        print(f"  Cached LLM Hits: {summary['calls']['cached_llm_hits']}")
        print(f"  Total Embeddings: {summary['calls']['total_embedding_calls']}")
        print(f"  Cached Embedding Hits: {summary['calls']['cached_embedding_hits']}")

        print(f"\nBatching:")
        print(f"  Total Batches: {summary['batching']['total_batches']}")
        print(f"  Avg Batch Size: {summary['batching']['avg_batch_size']:.1f}")
        print(f"  Max Batch Size: {summary['batching']['max_batch_size']}")

        print(f"\nCache:")
        print(f"  Size: {summary['cache']['size_mb']:.2f} MB")
        print(f"  Hit Rate: {summary['cache']['hit_rate']:.1f}%")

        print(f"\nEfficiency:")
        print(f"  LLM Call Reduction: {summary['efficiency']['llm_call_reduction']:.1f}%")
        print(f"  Throughput: {summary['efficiency']['throughput_items_per_sec']:.2f} items/sec")

        if self.enable_memory_tracking:
            print(f"\nMemory:")
            print(f"  Peak: {summary['memory']['peak_mb']:.2f} MB")
            print(f"  Average: {summary['memory']['avg_mb']:.2f} MB")

        print("\n" + "=" * 70 + "\n")

    def export_metrics(self, path: str) -> None:
        """
        Export metrics to JSON file.

        Args:
            path: Path to save metrics
        """
        summary = self.get_summary()

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        log.info(f"✓ Exported metrics to {path}")


class ComparisonAnalyzer:
    """
    Analyze and compare performance between baseline and optimized runs.
    """

    def __init__(self):
        """Initialize comparison analyzer."""
        self.baseline: Optional[Dict[str, Any]] = None
        self.optimized: Optional[Dict[str, Any]] = None

    def load_baseline(self, path: str) -> None:
        """Load baseline metrics from file."""
        with open(path, 'r') as f:
            self.baseline = json.load(f)
        log.info(f"✓ Loaded baseline metrics from {path}")

    def load_optimized(self, path: str) -> None:
        """Load optimized metrics from file."""
        with open(path, 'r') as f:
            self.optimized = json.load(f)
        log.info(f"✓ Loaded optimized metrics from {path}")

    def compare(self) -> Dict[str, Any]:
        """
        Compare baseline and optimized metrics.

        Returns:
            Comparison results showing improvements
        """
        if not self.baseline or not self.optimized:
            raise ValueError("Both baseline and optimized metrics must be loaded")

        def calculate_improvement(baseline_val: float, optimized_val: float) -> float:
            """Calculate improvement percentage."""
            if baseline_val == 0:
                return 0.0
            return ((baseline_val - optimized_val) / baseline_val) * 100

        comparison = {
            "duration_improvement": calculate_improvement(
                self.baseline["timing"]["total_duration_s"],
                self.optimized["timing"]["total_duration_s"]
            ),
            "llm_calls_reduction": calculate_improvement(
                self.baseline["calls"]["total_llm_calls"],
                self.optimized["calls"]["total_llm_calls"]
            ),
            "throughput_improvement": (
                (self.optimized["efficiency"]["throughput_items_per_sec"] -
                 self.baseline["efficiency"]["throughput_items_per_sec"]) /
                self.baseline["efficiency"]["throughput_items_per_sec"] * 100
            ),
            "cache_hit_rate": self.optimized["cache"]["hit_rate"],
            "avg_batch_size": self.optimized["batching"]["avg_batch_size"],
        }

        return comparison

    def print_comparison(self) -> None:
        """Print comparison summary."""
        comparison = self.compare()

        print("\n" + "=" * 70)
        print("BASELINE vs OPTIMIZED COMPARISON")
        print("=" * 70)

        print(f"\nPerformance Improvements:")
        print(f"  Duration Reduction: {comparison['duration_improvement']:.1f}%")
        print(f"  LLM Calls Reduction: {comparison['llm_calls_reduction']:.1f}%")
        print(f"  Throughput Increase: {comparison['throughput_improvement']:.1f}%")

        print(f"\nOptimization Features:")
        print(f"  Cache Hit Rate: {comparison['cache_hit_rate']:.1f}%")
        print(f"  Avg Batch Size: {comparison['avg_batch_size']:.1f}")

        # Target check
        print(f"\nPhase 3 Target Status:")
        target_reduction = 30.0
        if comparison['llm_calls_reduction'] >= target_reduction:
            print(f"  ✓ ACHIEVED: {comparison['llm_calls_reduction']:.1f}% reduction (target: {target_reduction}%)")
        else:
            print(f"  ✗ MISSED: {comparison['llm_calls_reduction']:.1f}% reduction (target: {target_reduction}%)")

        print("\n" + "=" * 70 + "\n")
