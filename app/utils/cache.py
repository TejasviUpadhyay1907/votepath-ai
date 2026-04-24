"""In-memory cache manager for response data"""

import threading
from typing import Dict, Optional


class CacheManager:
    """Thread-safe in-memory cache for election response data"""
    
    def __init__(self):
        """Initialize cache with empty dictionary and lock"""
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def set(self, category: str, data: Dict) -> None:
        """
        Store data in cache (thread-safe)
        
        Args:
            category: Intent category key
            data: Response data to cache
        """
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
        with self._lock:
            return self._cache.get(category)
    
    def populate(self, data: Dict[str, Dict]) -> None:
        """
        Bulk populate cache with data
        
        Args:
            data: Dictionary mapping categories to response data
        """
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
