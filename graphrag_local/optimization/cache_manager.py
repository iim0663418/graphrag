"""
Intelligent Cache Manager for GraphRAG Local Optimization.

This module implements a multi-level caching system to reduce redundant LLM calls
during the GraphRAG indexing process. It supports hash-based deduplication,
persistent storage, and TTL-based expiration.

Phase 3: Performance Optimization
Target: Reduce LLM calls by 30%+ through intelligent caching
"""

import hashlib
import json
import logging
import os
import pickle
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance tracking."""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    deletes: int = 0
    size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
            "deletes": self.deletes,
            "size_bytes": self.size_bytes,
            "hit_rate": self.hit_rate,
        }


class HashBasedCache:
    """
    Hash-based cache for text processing results.

    Uses content hashing to detect duplicate inputs and return cached results,
    significantly reducing redundant LLM calls during indexing.
    """

    def __init__(
        self,
        cache_dir: str = ".cache/graphrag_local",
        ttl_seconds: Optional[int] = None,
        max_size_mb: int = 500,
        enable_persistence: bool = True,
    ):
        """
        Initialize the hash-based cache.

        Args:
            cache_dir: Directory to store cache database
            ttl_seconds: Time-to-live for cache entries (None = no expiration)
            max_size_mb: Maximum cache size in megabytes
            enable_persistence: Whether to persist cache to disk
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.ttl_seconds = ttl_seconds
        self.max_size_mb = max_size_mb
        self.enable_persistence = enable_persistence

        # Statistics tracking
        self.stats = CacheStats()

        # Initialize database
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()

        log.info(
            f"Initialized cache at {self.cache_dir} "
            f"(TTL={ttl_seconds}s, Max={max_size_mb}MB)"
        )

    def _init_database(self) -> None:
        """Initialize SQLite database for cache storage."""
        if not self.enable_persistence:
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                size_bytes INTEGER NOT NULL,
                metadata TEXT
            )
        """)

        # Create index for TTL-based cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_accessed_at
            ON cache(accessed_at)
        """)

        conn.commit()
        conn.close()

        # Load statistics
        self._update_stats()

    def _compute_hash(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Compute hash for text input with optional context.

        Args:
            text: Input text to hash
            context: Optional context dict (e.g., prompt template, model config)

        Returns:
            SHA256 hash string
        """
        # Combine text and context for hashing
        hash_input = text
        if context:
            # Sort context keys for consistent hashing
            context_str = json.dumps(context, sort_keys=True)
            hash_input = f"{text}|{context_str}"

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def get(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Retrieve cached result for given text.

        Args:
            text: Input text to look up
            context: Optional context for hash computation

        Returns:
            Cached result if found and not expired, None otherwise
        """
        key = self._compute_hash(text, context)

        if not self.enable_persistence:
            self.stats.misses += 1
            return None

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Fetch cached entry
        cursor.execute(
            "SELECT value, created_at, accessed_at FROM cache WHERE key = ?",
            (key,)
        )
        result = cursor.fetchone()

        if result is None:
            conn.close()
            self.stats.misses += 1
            return None

        value_blob, created_at, accessed_at = result

        # Check TTL expiration
        if self.ttl_seconds is not None:
            age = time.time() - created_at
            if age > self.ttl_seconds:
                # Expired, delete and return None
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                conn.close()
                self.stats.misses += 1
                self.stats.deletes += 1
                return None

        # Update access time
        cursor.execute(
            "UPDATE cache SET accessed_at = ? WHERE key = ?",
            (time.time(), key)
        )
        conn.commit()
        conn.close()

        # Deserialize and return
        self.stats.hits += 1
        return pickle.loads(value_blob)

    def set(
        self,
        text: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store result in cache.

        Args:
            text: Input text (cache key basis)
            value: Result to cache
            context: Optional context for hash computation
            metadata: Optional metadata to store with entry
        """
        if not self.enable_persistence:
            return

        key = self._compute_hash(text, context)

        # Serialize value
        value_blob = pickle.dumps(value)
        size_bytes = len(value_blob)

        # Check size limits
        if size_bytes > self.max_size_mb * 1024 * 1024:
            log.warning(f"Cache entry too large: {size_bytes} bytes, skipping")
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Insert or replace
        now = time.time()
        cursor.execute(
            """
            INSERT OR REPLACE INTO cache
            (key, value, created_at, accessed_at, size_bytes, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                value_blob,
                now,
                now,
                size_bytes,
                json.dumps(metadata) if metadata else None,
            )
        )

        conn.commit()
        conn.close()

        self.stats.writes += 1
        self._update_stats()

        # Check if we need to evict entries
        self._maybe_evict()

    def _update_stats(self) -> None:
        """Update cache statistics."""
        if not self.enable_persistence:
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(size_bytes) FROM cache")
        result = cursor.fetchone()
        self.stats.size_bytes = result[0] if result[0] else 0

        conn.close()

    def _maybe_evict(self) -> None:
        """Evict old entries if cache exceeds size limit."""
        if not self.enable_persistence:
            return

        max_bytes = self.max_size_mb * 1024 * 1024

        if self.stats.size_bytes <= max_bytes:
            return

        # Evict least recently accessed entries
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Calculate how much to delete (delete 20% when over limit)
        target_bytes = int(max_bytes * 0.8)

        cursor.execute(
            """
            DELETE FROM cache WHERE key IN (
                SELECT key FROM cache
                ORDER BY accessed_at ASC
                LIMIT (
                    SELECT COUNT(*) / 5 FROM cache
                )
            )
            """
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        self.stats.deletes += deleted
        self._update_stats()

        log.info(f"Evicted {deleted} cache entries, size now: {self.stats.size_bytes} bytes")

    def clear(self) -> None:
        """Clear all cache entries."""
        if not self.enable_persistence:
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache")
        conn.commit()
        conn.close()

        self.stats = CacheStats()
        log.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get current cache statistics."""
        return self.stats.to_dict()

    def export_stats(self, path: Optional[str] = None) -> str:
        """
        Export cache statistics to JSON file.

        Args:
            path: Optional path to save stats, defaults to cache_dir/stats.json

        Returns:
            Path to saved stats file
        """
        if path is None:
            path = str(self.cache_dir / "stats.json")

        stats = self.get_stats()
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2)

        log.info(f"Exported cache stats to {path}")
        return path


class EntityRelationshipCache:
    """
    Specialized cache for entity and relationship extraction results.

    This cache is optimized for GraphRAG's entity extraction workflow,
    storing parsed entities and relationships to avoid re-extraction.
    """

    def __init__(
        self,
        cache_dir: str = ".cache/graphrag_local/entities",
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize entity/relationship cache.

        Args:
            cache_dir: Directory for cache storage
            ttl_seconds: Time-to-live for entries
        """
        self.base_cache = HashBasedCache(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_size_mb=1000,  # Larger size for entity data
        )

    def get_entities(
        self,
        text: str,
        extraction_prompt: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached entities for text chunk.

        Args:
            text: Source text chunk
            extraction_prompt: Prompt template used for extraction

        Returns:
            List of extracted entities if cached, None otherwise
        """
        context = {"type": "entities", "prompt": extraction_prompt}
        return self.base_cache.get(text, context)

    def set_entities(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        extraction_prompt: str,
    ) -> None:
        """
        Cache extracted entities.

        Args:
            text: Source text chunk
            entities: Extracted entities
            extraction_prompt: Prompt template used
        """
        context = {"type": "entities", "prompt": extraction_prompt}
        metadata = {"entity_count": len(entities)}
        self.base_cache.set(text, entities, context, metadata)

    def get_relationships(
        self,
        text: str,
        extraction_prompt: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached relationships."""
        context = {"type": "relationships", "prompt": extraction_prompt}
        return self.base_cache.get(text, context)

    def set_relationships(
        self,
        text: str,
        relationships: List[Dict[str, Any]],
        extraction_prompt: str,
    ) -> None:
        """Cache extracted relationships."""
        context = {"type": "relationships", "prompt": extraction_prompt}
        metadata = {"relationship_count": len(relationships)}
        self.base_cache.set(text, relationships, context, metadata)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.base_cache.get_stats()

    def clear(self) -> None:
        """Clear all cached entities and relationships."""
        self.base_cache.clear()


class MultiLevelCache:
    """
    Multi-level caching system combining memory and disk caches.

    Provides fast in-memory L1 cache with persistent L2 disk cache fallback.
    """

    def __init__(
        self,
        cache_dir: str = ".cache/graphrag_local/multilevel",
        l1_max_entries: int = 1000,
        l2_max_size_mb: int = 500,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize multi-level cache.

        Args:
            cache_dir: Directory for L2 cache
            l1_max_entries: Maximum entries in L1 (memory) cache
            l2_max_size_mb: Maximum size of L2 (disk) cache in MB
            ttl_seconds: Time-to-live for entries
        """
        # L1: In-memory LRU cache
        self.l1_cache: Dict[str, Tuple[Any, float]] = {}
        self.l1_max_entries = l1_max_entries
        self.l1_access_times: Dict[str, float] = {}

        # L2: Disk-based persistent cache
        self.l2_cache = HashBasedCache(
            cache_dir=cache_dir,
            ttl_seconds=ttl_seconds,
            max_size_mb=l2_max_size_mb,
        )

        # Combined statistics
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0

    def get(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Retrieve from multi-level cache.

        Checks L1 first, then L2, promoting L2 hits to L1.

        Args:
            text: Input text
            context: Optional context

        Returns:
            Cached value or None
        """
        key = self._compute_key(text, context)

        # Check L1
        if key in self.l1_cache:
            value, timestamp = self.l1_cache[key]
            self.l1_access_times[key] = time.time()
            self.l1_hits += 1
            return value

        # Check L2
        value = self.l2_cache.get(text, context)
        if value is not None:
            # Promote to L1
            self._set_l1(key, value)
            self.l2_hits += 1
            return value

        self.misses += 1
        return None

    def set(
        self,
        text: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store in multi-level cache.

        Writes to both L1 and L2.

        Args:
            text: Input text
            value: Value to cache
            context: Optional context
        """
        key = self._compute_key(text, context)

        # Write to both levels
        self._set_l1(key, value)
        self.l2_cache.set(text, value, context)

    def _compute_key(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """Compute cache key."""
        if context:
            context_str = json.dumps(context, sort_keys=True)
            return hashlib.sha256(f"{text}|{context_str}".encode()).hexdigest()
        return hashlib.sha256(text.encode()).hexdigest()

    def _set_l1(self, key: str, value: Any) -> None:
        """Set value in L1 cache with LRU eviction."""
        # Check if we need to evict
        if len(self.l1_cache) >= self.l1_max_entries:
            # Remove least recently used
            lru_key = min(self.l1_access_times.items(), key=lambda x: x[1])[0]
            del self.l1_cache[lru_key]
            del self.l1_access_times[lru_key]

        # Add to cache
        self.l1_cache[key] = (value, time.time())
        self.l1_access_times[key] = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        total = self.l1_hits + self.l2_hits + self.misses
        hit_rate = ((self.l1_hits + self.l2_hits) / total * 100) if total > 0 else 0.0

        l2_stats = self.l2_cache.get_stats()

        return {
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "total_hits": self.l1_hits + self.l2_hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "l1_size": len(self.l1_cache),
            "l1_max_entries": self.l1_max_entries,
            "l2_stats": l2_stats,
        }

    def clear(self) -> None:
        """Clear both cache levels."""
        self.l1_cache.clear()
        self.l1_access_times.clear()
        self.l2_cache.clear()
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0
