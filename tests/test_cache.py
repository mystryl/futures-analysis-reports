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

def test_cache_cleanup():
    """测试清理过期缓存"""
    cache = DataCache(ttl_seconds=1)

    # 添加多个缓存项
    cache.set('test1', {'data': 'value1'}, key='key1')
    cache.set('test2', {'data': 'value2'}, key='key2')
    cache.set('test3', {'data': 'value3'}, key='key3')

    # 等待缓存过期
    import time
    time.sleep(1.1)

    # 添加新的未过期缓存
    cache.set('test4', {'data': 'value4'}, key='key4')

    # 执行清理
    cache.cleanup()

    # 验证过期的缓存已被清理
    assert cache.get('test1', key='key1') is None
    assert cache.get('test2', key='key2') is None
    assert cache.get('test3', key='key3') is None

    # 验证未过期的缓存仍然存在
    assert cache.get('test4', key='key4') == {'data': 'value4'}
