class FakeRedisClient:
    def __init__(self):
        self.storage = {}

    async def set(self, name: str, value: dict, ex=None):
        self.storage[name] = value

    async def get(self, key: str) -> dict:
        return self.storage.get(key)

    async def incr(self, key: str) -> int:
        self.storage[key] = self.storage.get(key, 0) + 1
        return self.storage[key]

    async def delete(self, key) -> None:
        self.storage.pop(key, None)

    async def scan_iter(self, match=None):
        for key in list(self.storage):
            yield key

    async def expire(self, name: str, time: int = 60) -> bool:
        return True


fake_redis = FakeRedisClient()

def override_redis_client():
    return fake_redis