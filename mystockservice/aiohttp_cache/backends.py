import asyncio
import pickle
import time
import warnings

import aiohttp.web

try:
    import aioredis
except ImportError:
    warnings.showwarning(
        "aioredis library not found. Redis cache backend not available")


class BaseCache(object):

    def __init__(self, expiration: int = 300):
        self.expiration = expiration

    async def get(self, key: str) -> object:
        raise NotImplementedError()

    async def delete(self, key: str):
        raise NotImplementedError()

    async def has(self, key: str) -> bool:
        raise NotImplementedError()

    async def clear(self):
        raise NotImplementedError()

    async def set(self, key: str, value: dict, expires: int = 3000):
        raise NotImplementedError()

    def make_key(self, request: aiohttp.web.Request) -> str:
        key = "{method}#{host}#{path}#{ctype}".format(method=request.method,
                                                      path=request.rel_url,
                                                      host=request.url.host,
                                                      ctype=request.content_type)
        return key

    def _calculate_expires(self, expires: int) -> int:
        return self.expiration if expires is None or expires < 0 else expires


class _Config:
    def __init__(self,
                 expiration: int = 300):
        self.expiration = expiration


# --------------------------------------------------------------------------
# REDIS BACKEND
# --------------------------------------------------------------------------
class RedisConfig(_Config):

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: str = None,
                 key_prefix: str = None):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.key_prefix = key_prefix or ''

        super(RedisConfig, self).__init__()


class RedisCache(BaseCache):

    def __init__(self,
                 config: RedisConfig,
                 *,
                 loop: asyncio.BaseEventLoop = None):
        """

        :param loop:
        :type loop:
        """
        BaseCache.__init__(self, config.expiration)
        _loop = loop or asyncio.get_event_loop()
        self._redis_pool = None
        self.key_prefix = config.key_prefix
        self.config = config

    async def init(self):
        self._redis_pool = await aioredis.create_redis_pool((self.config.host, self.config.port),
                                                            db=self.config.db,
                                                            password=self.config.password)

    def dump_object(self, value: dict) -> bytes:
        t = type(value)
        if t in (int, ):
            return str(value).encode('ascii')
        return b'!' + pickle.dumps(value)

    def load_object(self, value):
        """The reversal of :meth:`dump_object`.  This might be called with
        None.
        """
        if value is None:
            return None
        if value.startswith(b'!'):
            try:
                return pickle.loads(value[1:])
            except pickle.PickleError:
                return None
        try:
            return int(value)
        except ValueError:
            # before 0.8 we did not have serialization.  Still support that.
            return value

    async def get(self, key: str):
        # async with self._redis_pool.get() as redis:
        redis_value = await self._redis_pool.get(self.key_prefix + key)

        return self.load_object(redis_value)

    async def set(self, key: str, value: dict, expires: int = 3000):
        dump = self.dump_object(value)

        _expires = self._calculate_expires(expires)

        if _expires == 0:
            await self._redis_pool.set(name=self.key_prefix + key,
                                       value=dump)
        else:
            await self._redis_pool.setex(key=self.key_prefix + key,
                                         seconds=_expires,
                                         value=dump)

    async def delete(self, key: str):
        await self._redis_pool.delete(self.key_prefix + key)

    async def has(self, key: str) -> bool:
        return await self._redis_pool.exists(self.key_prefix + key)

    async def clear(self):
        if self.key_prefix:
            keys = await self._redis_pool.keys(self.key_prefix + '*')
            if keys:
                await self._redis_pool.delete(*keys)
        else:
            await self._redis_pool.flushdb()


# --------------------------------------------------------------------------
# MEMORY BACKEND
# --------------------------------------------------------------------------
class MemoryCache(BaseCache):

    def __init__(self,
                 *,
                 expiration=300):
        super().__init__(expiration=expiration)

        #
        # Cache format:
        # (cached object, expire date)
        #
        self._cache = {}

    async def get(self, key: str):
        # Update the keys
        self._update_expiration_key(key)

        try:
            cached = self._cache[key]

            return cached[0]
        except KeyError:
            return None

    async def set(self, key: str, value: dict, expires: int = 3000):
        _expires = self._calculate_expires(expires)

        self._cache[key] = (value, int(time.time()) + _expires)

    async def has(self, key: str):
        # Update the keys
        self._update_expiration_key(key)

        return key in self._cache

    async def delete(self, key: str):
        # Update the keys
        self._update_expiration_key(key)

        try:
            del self._cache[key]
        except KeyError:
            pass

    async def clear(self):
        self._cache = {}

    def _update_expiration_key(self, key: str):
        try:
            expiration = self._cache[key][1]

            if expiration < int(time.time()):
                del self._cache[key]
        except KeyError:
            pass


__all__ = ("MemoryCache", "RedisCache", "RedisConfig")
