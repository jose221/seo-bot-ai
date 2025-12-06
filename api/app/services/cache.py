import os
from typing import Dict, Any, Optional, Callable

import numpy as np
import pandas as pd

from app.helpers import encode_to_base64_key

# Definir la raíz del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Ruta del directorio de caché relativa a la raíz del proyecto
cache_dir = os.path.join(project_root, 'storage', 'cache')

import os
import requests
from dotenv import load_dotenv
import json

from app.helpers import serialize_response_data

# Carga las variables de entorno del archivo .env
load_dotenv()


class CacheProvider:
    def __init__(self):
        self.base_url = os.getenv("HERANDRO_API_URL")

    def upload_data(self, key, data, ttl=0):
        url = f"{self.base_url}/cache/upload/"
        params = {'key': key}
        if ttl is not None:
            params['ttl'] = ttl

        serialized_data = serialize_response_data(data)
        req = {"result": serialized_data}

        try:
            response = requests.post(url, data=json.dumps(req, ensure_ascii=False), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:

            print(f"Error uploading data: {e}")
            print(f"Error uploading data: {e.response}")
            return None

    def get_data(self, key):
        url = f"{self.base_url}/cache/{key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            if response.status_code == 404:
                return []
            data = response.json().get('data', {})
            return data.get('result', []) if len(data.get('result', [])) > 0 else (data.get('data', {})).get('result',
                                                                                                             [])
        except requests.exceptions.RequestException as e:
            print(f"Error getting data: {e}")
            return None

    async def get_data_async(self, key):
        import httpx
        url = f"{self.base_url}/cache/{key}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            if response.status_code == 404:
                return []
            data = response.json().get('data', {})
            return data.get('result', [])
        except httpx.HTTPStatusError as e:
            print(f"Error getting data asynchronously: {e}")
            return None

    def delete_data(self, key):
        url = f"{self.base_url}/cache/{key}"
        try:
            response = requests.delete(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error deleting data: {e}")
            return None

    def search_delete(self, table):
        url = f"{self.base_url}/cache/search-delete/"
        query = {
            "pattern": f"%{table}%"
        }

        try:
            response = requests.delete(url, params=query)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error deleting data: {e}")
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
