"""In-memory cache manager for response data

This module provides a thread-safe, in-memory cache for election response data.
The cache is populated at startup from the best available data source and serves
all subsequent requests without additional I/O.

Design decisions:
- Thread-safe: Uses threading.Lock for concurrent access in FastAPI's async environment
- Simple: Plain dictionary for O(1) lookups - no expiration or eviction needed
- Startup-populated: Loaded once at startup, never modified during runtime
- Fast: Enables sub-500ms response times required by performance criteria

Cache lifecycle:
1. Startup: populate() called with data from Sheets/GCS/fallback
2. Runtime: get() called for each /ask request (read-only)
3. Testing: clear() available for test isolation

Why in-memory cache?
- Election data changes infrequently (not real-time)
- Dataset is small (~8 categories, ~2KB each)
- Eliminates external dependencies (Redis, Memcached)
- Simplifies deployment and reduces latency
"""

import threading
from typing import Dict, Optional


class CacheManager:
    """Thread-safe in-memory cache for election response data"""

    def __init__(self):
        """Initialize cache with empty dictionary and lock"""
        # WHY: Using a simple dict for O(1) lookups. Threading lock ensures
        # thread-safety in FastAPI's async environment where multiple requests
        # may access cache simultaneously.
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def set(self, category: str, data: Dict) -> None:
        """
        Store data in cache (thread-safe)

        Args:
            category: Intent category key
            data: Response data to cache
        """
        # WHY: Lock prevents race conditions when multiple threads write simultaneously
        with self._lock:
            self._cache[category] = data

    def get(self, category: str) -> Optional[Dict]:
        """
        Retrieve data from cache (thread-safe)

        Args:
            category: Intent category key

        Returns:
            Optional[Dict]: Cached data or None if not found
        """
        # WHY: Lock ensures we don't read while another thread is writing
        # Returns None for cache misses rather than raising exceptions
        with self._lock:
            return self._cache.get(category)

    def populate(self, data: Dict[str, Dict]) -> None:
        """
        Bulk populate cache with data

        Args:
            data: Dictionary mapping categories to response data
        """
        # WHY: Bulk update is more efficient than individual set() calls
        # Used at startup to load all categories at once from data source
        with self._lock:
            self._cache.update(data)

    def clear(self) -> None:
        """Clear all cached data (for testing)"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """
        Get number of cached entries

        Returns:
            int: Number of items in cache
        """
        with self._lock:
            return len(self._cache)

    def has(self, category: str) -> bool:
        """
        Check if category exists in cache

        Args:
            category: Intent category key

        Returns:
            bool: True if category is cached
        """
        with self._lock:
            return category in self._cache


# Global cache instance
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """
    Get global cache instance (singleton pattern)

    Returns:
        CacheManager: Global cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance
