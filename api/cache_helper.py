import os
import json

REDIS_URL = os.environ.get('REDIS_URL')

class MockCache:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ttl=3600):
        self.data[key] = value
        return True
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
        return True
    
    def ping(self):
        return True

def get_cache():
    if REDIS_URL:
        try:
            import redis
            client = redis.from_url(REDIS_URL, decode_responses=True)
            client.ping()
            return RedisCache(client)
        except Exception:
            pass
    return MockCache()

class RedisCache:
    def __init__(self, client):
        self.client = client
    
    def get(self, key):
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key, value, ttl=3600):
        self.client.setex(key, ttl, json.dumps(value))
        return True
    
    def delete(self, key):
        self.client.delete(key)
        return True
    
    def ping(self):
        return self.client.ping()
