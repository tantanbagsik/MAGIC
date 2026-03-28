import redis
import json
from typing import Optional, Any
from config import config

class RedisCache:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.default_ttl = 3600
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(str(data))
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception:
            return False
    
    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            return False

cache = RedisCache()
