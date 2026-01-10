"""
Batch Processor for GraphRAG Local Optimization.

This module implements intelligent batching strategies to reduce the number of
individual LLM calls by aggregating multiple requests into batch operations.

Phase 3: Performance Optimization
Target: Reduce LLM API calls by 30%+ through intelligent batching
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

log = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    min_batch_size: int = 1
    max_batch_size: int = 32
    max_wait_time_ms: float = 100.0  # Maximum wait time before processing partial batch
    adaptive_sizing: bool = True
    enable_cache_dedup: bool = True


@dataclass
class BatchStats:
    """Statistics for batch processing performance."""
    total_requests: int = 0
    total_batches: int = 0
    total_items_processed: int = 0
    total_cache_hits: int = 0
    total_wait_time_ms: float = 0.0
    batches_by_size: Dict[int, int] = field(default_factory=dict)

    @property
    def avg_batch_size(self) -> float:
        """Calculate average batch size."""
        return (self.total_items_processed / self.total_batches) if self.total_batches > 0 else 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.total_items_processed
        return (self.total_cache_hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "total_items_processed": self.total_items_processed,
            "total_cache_hits": self.total_cache_hits,
            "avg_batch_size": self.avg_batch_size,
            "cache_hit_rate": self.cache_hit_rate,
            "total_wait_time_ms": self.total_wait_time_ms,
            "batches_by_size": self.batches_by_size,
        }


class BatchProcessor:
    """
    Intelligent batch processor for LLM requests.

    Accumulates individual requests and processes them in optimized batches,
    reducing the total number of LLM API calls.
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        cache: Optional[Any] = None,
    ):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
            cache: Optional cache for deduplication
        """
        self.config = config or BatchConfig()
        self.cache = cache

        # Pending requests queue
        self._queue: List[Tuple[str, asyncio.Future]] = []
        self._queue_lock = asyncio.Lock()

        # Timer for batch timeout
        self._timer_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = BatchStats()

        log.info(
            f"Initialized BatchProcessor with config: "
            f"min={self.config.min_batch_size}, "
            f"max={self.config.max_batch_size}, "
            f"wait={self.config.max_wait_time_ms}ms"
        )

    async def process(
        self,
        item: str,
        batch_fn: Callable[[List[str]], List[R]],
        context: Optional[Dict[str, Any]] = None,
    ) -> R:
        """
        Process a single item through batching.

        Args:
            item: Input item to process
            batch_fn: Function that processes a batch of items
            context: Optional context for cache lookup

        Returns:
            Processing result for the item
        """
        self.stats.total_requests += 1

        # Check cache first
        if self.cache and self.config.enable_cache_dedup:
            cached = self.cache.get(item, context)
            if cached is not None:
                self.stats.total_cache_hits += 1
                return cached

        # Add to queue
        future: asyncio.Future = asyncio.Future()

        async with self._queue_lock:
            self._queue.append((item, future))

            # Start timer if this is the first item
            if len(self._queue) == 1:
                asyncio.create_task(self._start_timer(batch_fn, context))

            # Process immediately if batch is full
            if len(self._queue) >= self.config.max_batch_size:
                await self._process_batch(batch_fn, context)

        # Wait for result
        return await future

    async def _start_timer(
        self,
        batch_fn: Callable[[List[str]], List[R]],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Start timeout timer for batch processing."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        async def timer():
            await asyncio.sleep(self.config.max_wait_time_ms / 1000.0)
            async with self._queue_lock:
                if self._queue:
                    await self._process_batch(batch_fn, context)

        self._timer_task = asyncio.create_task(timer())

    async def _process_batch(
        self,
        batch_fn: Callable[[List[str]], List[R]],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Process accumulated batch.

        Args:
            batch_fn: Batch processing function
            context: Optional context
        """
        if not self._queue:
            return

        # Cancel timer
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        # Extract batch
        batch_size = min(len(self._queue), self.config.max_batch_size)
        batch = self._queue[:batch_size]
        self._queue = self._queue[batch_size:]

        items = [item for item, _ in batch]
        futures = [future for _, future in batch]

        # Update statistics
        self.stats.total_batches += 1
        self.stats.total_items_processed += len(items)
        self.stats.batches_by_size[len(items)] = self.stats.batches_by_size.get(len(items), 0) + 1

        try:
            # Process batch
            start_time = time.time()
            results = await asyncio.get_event_loop().run_in_executor(
                None, batch_fn, items
            )
            elapsed_ms = (time.time() - start_time) * 1000

            self.stats.total_wait_time_ms += elapsed_ms

            # Validate results
            if len(results) != len(items):
                raise ValueError(
                    f"Batch function returned {len(results)} results "
                    f"for {len(items)} items"
                )

            # Set results and cache
            for item, result, future in zip(items, results, futures):
                if self.cache and self.config.enable_cache_dedup:
                    self.cache.set(item, result, context)
                future.set_result(result)

            log.debug(f"Processed batch of {len(items)} items in {elapsed_ms:.2f}ms")

        except Exception as e:
            # Set exception for all futures
            log.error(f"Batch processing failed: {e}")
            for future in futures:
                if not future.done():
                    future.set_exception(e)

    async def flush(
        self,
        batch_fn: Callable[[List[str]], List[R]],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Force process all pending items.

        Args:
            batch_fn: Batch processing function
            context: Optional context
        """
        async with self._queue_lock:
            while self._queue:
                await self._process_batch(batch_fn, context)

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return self.stats.to_dict()

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = BatchStats()


class AdaptiveBatchProcessor(BatchProcessor):
    """
    Adaptive batch processor that dynamically adjusts batch size
    based on processing performance.
    """

    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        cache: Optional[Any] = None,
    ):
        """Initialize adaptive batch processor."""
        super().__init__(config, cache)

        # Adaptive sizing parameters
        self._recent_batch_times: List[float] = []
        self._max_history = 10
        self._current_optimal_size = self.config.max_batch_size

    async def _process_batch(
        self,
        batch_fn: Callable[[List[str]], List[R]],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Process batch with adaptive sizing."""
        # Process batch normally
        start_time = time.time()
        await super()._process_batch(batch_fn, context)
        elapsed = time.time() - start_time

        # Update adaptive sizing if enabled
        if self.config.adaptive_sizing:
            self._update_optimal_size(elapsed)

    def _update_optimal_size(self, batch_time: float) -> None:
        """
        Update optimal batch size based on processing time.

        Args:
            batch_time: Time taken to process the batch
        """
        self._recent_batch_times.append(batch_time)

        # Keep only recent history
        if len(self._recent_batch_times) > self._max_history:
            self._recent_batch_times.pop(0)

        # Need at least 3 samples to adapt
        if len(self._recent_batch_times) < 3:
            return

        # Calculate average time per item
        avg_time = sum(self._recent_batch_times) / len(self._recent_batch_times)

        # If processing is fast, try larger batches
        if avg_time < 0.5 and self._current_optimal_size < self.config.max_batch_size:
            self._current_optimal_size = min(
                self._current_optimal_size + 4,
                self.config.max_batch_size
            )
            log.debug(f"Increased optimal batch size to {self._current_optimal_size}")

        # If processing is slow, try smaller batches
        elif avg_time > 2.0 and self._current_optimal_size > self.config.min_batch_size:
            self._current_optimal_size = max(
                self._current_optimal_size - 4,
                self.config.min_batch_size
            )
            log.debug(f"Decreased optimal batch size to {self._current_optimal_size}")

    def get_optimal_size(self) -> int:
        """Get current optimal batch size."""
        return self._current_optimal_size


class TextChunkBatcher:
    """
    Specialized batcher for text chunks during GraphRAG indexing.

    Optimizes batch processing for entity extraction and embedding generation.
    """

    def __init__(
        self,
        max_batch_tokens: int = 8000,
        max_batch_size: int = 32,
        tokenizer: Optional[Callable[[str], int]] = None,
    ):
        """
        Initialize text chunk batcher.

        Args:
            max_batch_tokens: Maximum total tokens per batch
            max_batch_size: Maximum number of chunks per batch
            tokenizer: Function to count tokens in text
        """
        self.max_batch_tokens = max_batch_tokens
        self.max_batch_size = max_batch_size
        self.tokenizer = tokenizer or self._default_tokenizer

    def _default_tokenizer(self, text: str) -> int:
        """Default token counter (approximation)."""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def create_batches(
        self,
        chunks: List[str],
    ) -> List[List[str]]:
        """
        Create optimal batches from text chunks.

        Groups chunks to maximize batch size while respecting token limits.

        Args:
            chunks: List of text chunks to batch

        Returns:
            List of batches (each batch is a list of chunks)
        """
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_tokens = 0

        for chunk in chunks:
            chunk_tokens = self.tokenizer(chunk)

            # Check if adding this chunk would exceed limits
            if (
                current_batch and
                (
                    len(current_batch) >= self.max_batch_size or
                    current_tokens + chunk_tokens > self.max_batch_tokens
                )
            ):
                # Start new batch
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(chunk)
            current_tokens += chunk_tokens

        # Add final batch
        if current_batch:
            batches.append(current_batch)

        log.debug(
            f"Created {len(batches)} batches from {len(chunks)} chunks "
            f"(avg size: {len(chunks) / len(batches):.1f})"
        )

        return batches

    async def process_chunks(
        self,
        chunks: List[str],
        processor_fn: Callable[[List[str]], List[R]],
    ) -> List[R]:
        """
        Process text chunks in optimal batches.

        Args:
            chunks: Text chunks to process
            processor_fn: Function to process each batch

        Returns:
            List of results in same order as input chunks
        """
        batches = self.create_batches(chunks)
        results: List[R] = []

        for batch in batches:
            batch_results = await asyncio.get_event_loop().run_in_executor(
                None, processor_fn, batch
            )
            results.extend(batch_results)

        return results


class DedupBatchProcessor:
    """
    Batch processor with built-in deduplication.

    Identifies duplicate inputs in a batch and processes each unique
    input only once, then maps results back to original positions.
    """

    def __init__(self):
        """Initialize deduplication batch processor."""
        self.stats = {
            "total_items": 0,
            "unique_items": 0,
            "dedup_savings": 0,
        }

    async def process_batch(
        self,
        items: List[str],
        processor_fn: Callable[[List[str]], List[R]],
    ) -> List[R]:
        """
        Process batch with deduplication.

        Args:
            items: Input items (may contain duplicates)
            processor_fn: Function to process unique items

        Returns:
            Results mapped back to original item positions
        """
        # Track original positions
        unique_items: List[str] = []
        item_to_idx: Dict[str, int] = {}
        original_to_unique: List[int] = []

        for item in items:
            if item not in item_to_idx:
                item_to_idx[item] = len(unique_items)
                unique_items.append(item)
            original_to_unique.append(item_to_idx[item])

        # Update statistics
        self.stats["total_items"] += len(items)
        self.stats["unique_items"] += len(unique_items)
        self.stats["dedup_savings"] += len(items) - len(unique_items)

        # Process unique items only
        unique_results = await asyncio.get_event_loop().run_in_executor(
            None, processor_fn, unique_items
        )

        # Map results back to original positions
        results = [unique_results[idx] for idx in original_to_unique]

        log.debug(
            f"Processed {len(unique_items)} unique items from {len(items)} total "
            f"(saved {len(items) - len(unique_items)} duplicate calls)"
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        total = self.stats["total_items"]
        savings_rate = (
            (self.stats["dedup_savings"] / total * 100)
            if total > 0 else 0.0
        )

        return {
            **self.stats,
            "dedup_savings_rate": savings_rate,
        }
