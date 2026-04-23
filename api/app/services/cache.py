import json
from typing import Dict, Any, Optional, Callable

import numpy as np
import pandas as pd
import redis
import redis.asyncio as aioredis

from app.helpers import encode_to_base64_key, serialize_response_data
from app.core.config import settings

# Definir la raíz del proyecto
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
cache_dir = os.path.join(project_root, 'storage', 'cache')


def _build_redis_url() -> str:
    password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


class CacheProvider:
    def __init__(self):
        self._client: redis.Redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )

    def upload_data(self, key: str, data, ttl: int = 0):
        serialized_data = serialize_response_data(data)
        payload = json.dumps({"result": serialized_data}, ensure_ascii=False)
        try:
            if ttl and ttl > 0:
                self._client.setex(key, ttl, payload)
            else:
                self._client.set(key, payload)
            return {"status": "ok", "key": key}
        except redis.RedisError as e:
            print(f"Error uploading data to Redis: {e}")
            return None

    def get_data(self, key: str):
        try:
            raw = self._client.get(key)
            if raw is None:
                return []
            data = json.loads(raw)
            return data.get("result", [])
        except redis.RedisError as e:
            print(f"Error getting data from Redis: {e}")
            return None

    async def get_data_async(self, key: str):
        try:
            async_client = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
            async with async_client:
                raw = await async_client.get(key)
            if raw is None:
                return []
            data = json.loads(raw)
            return data.get("result", [])
        except Exception as e:
            print(f"Error getting data asynchronously from Redis: {e}")
            return None

    def delete_data(self, key: str):
        try:
            deleted = self._client.delete(key)
            return {"status": "ok", "deleted": deleted}
        except redis.RedisError as e:
            print(f"Error deleting data from Redis: {e}")
            return None

    def search_delete(self, table: str):
        pattern = f"*{table}*"
        try:
            keys = self._client.keys(pattern)
            deleted = self._client.delete(*keys) if keys else 0
            return {"status": "ok", "deleted": deleted, "pattern": pattern}
        except redis.RedisError as e:
            print(f"Error in search_delete from Redis: {e}")
            return None


class Cache:

    def __init__(self, table_name: str, relations: Optional[list[str]] = None):
        self.cacheProvider = CacheProvider()  # Inicializar CacheProvider aquí
        self.table = table_name
        self.relationsTable = relations

    def convert_non_serializable(self, obj):
        """
        Convierte los tipos de datos no serializables (como int64) a tipos serializables por JSON.
        """
        if isinstance(obj, dict):
            return {k: self.convert_non_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_non_serializable(element) for element in obj]
        elif isinstance(obj, np.integer):
            return str(obj)
        else:
            return obj

    def getCacheKey(self, params: Dict[str, Any]):
        # Ordenamos las claves para garantizar consistencia
        sorted_data = json.dumps(self.convert_non_serializable(params), sort_keys=True)
        #hash_object = hashlib.sha256(sorted_data.encode(), usedforsecurity=False)
        return encode_to_base64_key(sorted_data)

    def saveToCache(self, data, cache_key: str, ttl: int = 0):
        """Saves data to a cache file based on the cache key."""
        self.cacheProvider.upload_data(key=cache_key, data=data, ttl=ttl)

    def loadFromCache(self, params: Dict[str, Any], prefix='', ttl: Optional[int] = 0, cache: Optional[bool] = True,
                      callback: Optional[Callable] = None, *args, **kwargs):
        #called = get_call_stack()
        """agregamos de que funcion ha sido llamado"""
        #params.setdefault('called', called)
        """Loads data from a cache file if it exists, otherwise executes a callback."""
        disabled = True if cache is False else False
        cache_key = f" {self.table}_{prefix}_{self.getCacheKey(params)}"
        data = None if disabled is True else self.cacheProvider.get_data(cache_key)
        if data is not None and len(data) > 0 and disabled is False:
            return self.to_dataframe(res=data)
        elif callback:
            print("NOT FOUND not loaded will search in callback")
            res = callback(*args, **kwargs)
            if (
                    (isinstance(res, pd.DataFrame) and not res.empty) or
                    (isinstance(res, dict) and bool(res)) or
                    (isinstance(res, list) and len(res) > 0) or
                    (isinstance(res, np.ndarray) and res.size > 0) or
                    (res is not None)
            ):
                self.saveToCache(data=res, cache_key=cache_key, ttl=ttl)
            return self.to_dataframe(res=res)
        return pd.DataFrame([])  # Return an empty DataFrame if no cache and no callback response

    async def loadFromCacheAsync(self, params: Dict[str, Any], prefix='', ttl: Optional[int] = 1200,
                                 callback_async: Optional[Callable] = None,
                                 *args, **kwargs):
        """Loads data from a cache file if it exists, otherwise executes a callback."""
        cache_key = self.table + prefix + self.getCacheKey(params)
        data = self.cacheProvider.get_data(cache_key)

        if data is not None and len(data) > 0:
            print("Loaded data from:", cache_key)
            return data

        elif callback_async:
            res = await callback_async(*args, **kwargs)
            if (
                    (isinstance(res, pd.DataFrame) and not res.empty) or
                    (isinstance(res, dict) and bool(res)) or
                    (isinstance(res, list) and len(res) > 0) or
                    (isinstance(res, np.ndarray) and res.size > 0) or
                    (res is not None)
            ):
                self.saveToCache(data=res, cache_key=cache_key, ttl=ttl)
            return res
        return pd.DataFrame([])  # Return an empty DataFrame if no cache and no callback response

    def removeCacheTable(self, table: str):
        self.cacheProvider.search_delete(table=table)

    def checkCache(self, table: str = None):
        if table is None:
            table = self.table
        self.removeCacheTable(table)
        if self.relationsTable is not None:
            for index, relation in self.relationsTable:
                self.removeCacheTable(relation)

    def to_dataframe(self, res):
        try:
            return pd.DataFrame(res)
        except:
            return res
