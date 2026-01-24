"""数据缓存服务"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """内存数据缓存"""

    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存
        ttl_seconds: 缓存过期时间（秒），默认 5 分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def _generate_key(self, prefix: str, **params) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, prefix: str, **params) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(prefix, **params)
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry['expires']:
                logger.debug(f"缓存命中: {key}")
                return entry['data']
            else:
                del self._cache[key]
        return None

    def set(self, prefix: str, data: Any, **params) -> None:
        """设置缓存"""
        key = self._generate_key(prefix, **params)
        self._cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.ttl)
        }
        logger.debug(f"缓存写入: {key}")

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def cleanup(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        expired = [k for k, v in self._cache.items() if now >= v['expires']]
        for key in expired:
            del self._cache[key]
        if expired:
            logger.info(f"清理 {len(expired)} 个过期缓存")


# 全局缓存实例
cache = DataCache(ttl_seconds=300)
