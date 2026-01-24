"""缓存服务测试"""
import pytest
import time
from services.cache import DataCache

def test_cache_set_and_get():
    """测试缓存写入和读取"""
    cache = DataCache(ttl_seconds=1)

    cache.set('test', {'data': 'value'}, key='123')
    result = cache.get('test', key='123')

    assert result == {'data': 'value'}

def test_cache_expiration():
    """测试缓存过期"""
    cache = DataCache(ttl_seconds=1)

    cache.set('test', {'data': 'value'}, key='exp')
    time.sleep(1.1)  # 等待过期

    result = cache.get('test', key='exp')
    assert result is None

def test_cache_miss():
    """测试缓存未命中"""
    cache = DataCache()
    result = cache.get('nonexistent', key='miss')
    assert result is None

def test_cache_clear():
    """测试清空缓存"""
    cache = DataCache()
    cache.set('test', {'data': 'value'}, key='clear')
    cache.clear()

    result = cache.get('test', key='clear')
    assert result is None
