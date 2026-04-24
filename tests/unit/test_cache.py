"""Unit tests for CacheManager"""

import threading
import pytest
from app.utils.cache import CacheManager


@pytest.fixture
def cache():
    """Fresh CacheManager for each test"""
    c = CacheManager()
    yield c
    c.clear()


class TestCacheBasicOperations:

    def test_set_and_get(self, cache):
        data = {"title": "Test", "overview": "Overview"}
        cache.set("registration", data)
        assert cache.get("registration") == data

    def test_get_missing_key_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_size_empty(self, cache):
        assert cache.size() == 0

    def test_size_after_set(self, cache):
        cache.set("registration", {"title": "T"})
        cache.set("documents", {"title": "D"})
        assert cache.size() == 2

    def test_has_existing_key(self, cache):
        cache.set("faq", {"title": "FAQ"})
        assert cache.has("faq") is True

    def test_has_missing_key(self, cache):
        assert cache.has("missing") is False

    def test_clear_empties_cache(self, cache):
        cache.set("registration", {"title": "T"})
        cache.clear()
        assert cache.size() == 0
        assert cache.get("registration") is None

    def test_populate_bulk(self, cache):
        data = {
            "registration": {"title": "Reg"},
            "documents": {"title": "Docs"},
            "faq": {"title": "FAQ"},
        }
        cache.populate(data)
        assert cache.size() == 3
        assert cache.get("registration") == {"title": "Reg"}
        assert cache.get("documents") == {"title": "Docs"}

    def test_overwrite_existing_key(self, cache):
        cache.set("faq", {"title": "Old"})
        cache.set("faq", {"title": "New"})
        assert cache.get("faq") == {"title": "New"}


class TestCacheThreadSafety:

    def test_concurrent_writes(self, cache):
        """Multiple threads writing should not corrupt the cache"""
        errors = []

        def write(key, value):
            try:
                cache.set(key, {"title": value})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write, args=(f"key_{i}", f"val_{i}")) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert cache.size() == 50

    def test_concurrent_reads_and_writes(self, cache):
        """Reads and writes happening simultaneously should not raise"""
        cache.populate({f"cat_{i}": {"title": str(i)} for i in range(10)})
        errors = []

        def read():
            try:
                for i in range(10):
                    cache.get(f"cat_{i}")
            except Exception as e:
                errors.append(e)

        def write():
            try:
                for i in range(10, 20):
                    cache.set(f"cat_{i}", {"title": str(i)})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read) for _ in range(5)]
        threads += [threading.Thread(target=write) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
