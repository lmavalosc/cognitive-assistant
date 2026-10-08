import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from cognitive_assistant.settings import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None
_redis_client_loop: Optional[asyncio.AbstractEventLoop] = None
_in_memory_fallback_store: Dict[str, tuple[str, Optional[float]]] = {}
_in_memory_lock: Optional[asyncio.Lock] = None
_in_memory_lock_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_in_memory_lock() -> asyncio.Lock:
    global _in_memory_lock, _in_memory_lock_loop
    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    if _in_memory_lock is None or _in_memory_lock_loop != current_loop:
        _in_memory_lock = asyncio.Lock()
        _in_memory_lock_loop = current_loop
    return _in_memory_lock


def get_redis_client() -> aioredis.Redis:
    """Devuelve la instancia del cliente asíncrono de Redis, adaptándose al event loop activo."""
    global _redis_client, _redis_client_loop
    current_loop = None
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    # Recrear cliente si el event loop cambió o quedó huérfano
    if _redis_client is not None and _redis_client_loop != current_loop:
        _redis_client = None

    if _redis_client is None:
        url = settings.redis_url
        logger.debug("Inicializando conexión asíncrona a Redis en %s", url)
        _redis_client = aioredis.from_url(
            url,
            socket_timeout=3.0,
            socket_connect_timeout=3.0,
            decode_responses=True,
            retry_on_timeout=True,
        )
        _redis_client_loop = current_loop
    return _redis_client


async def check_redis_health() -> bool:
    """Verifica si el servicio Redis está activo y responde a PING."""
    try:
        client = get_redis_client()
        pong = await client.ping()
        return bool(pong)
    except Exception as exc:
        logger.warning("Fallo en health check de Redis: %s", exc)
        return False


async def redis_set_json(key: str, data: Any, ttl_seconds: Optional[int] = 86400) -> bool:
    """
    Almacena un objeto serializado a JSON en Redis.
    Si Redis no está accesible, utiliza el almacén de fallback en memoria RAM.
    """
    serialized = json.dumps(data)
    try:
        client = get_redis_client()
        await client.set(key, serialized, ex=ttl_seconds)
        return True
    except Exception as exc:
        logger.warning("Redis no disponible para clave '%s' (%s). Usando fallback en memoria.", key, exc)
        async with _get_in_memory_lock():
            expire_at = time.time() + ttl_seconds if ttl_seconds else None
            _in_memory_fallback_store[key] = (serialized, expire_at)
        return False


async def redis_get_json(key: str) -> Optional[Any]:
    """
    Recupera y deserializa un objeto JSON desde Redis.
    Si la clave no existe en Redis o Redis falla, consulta el almacén de memoria RAM.
    """
    try:
        client = get_redis_client()
        val = await client.get(key)
        if val is not None:
            return json.loads(val)
    except Exception as exc:
        logger.warning("Error al consultar clave '%s' en Redis (%s). Consultando fallback en memoria.", key, exc)

    # Fallback en memoria
    async with _get_in_memory_lock():
        item = _in_memory_fallback_store.get(key)
        if item is not None:
            data_str, expire_at = item
            if expire_at is not None and time.time() > expire_at:
                del _in_memory_fallback_store[key]
                return None
            return json.loads(data_str)
    return None


async def redis_delete_key(key: str) -> bool:
    """Elimina una clave tanto de Redis como del almacén de memoria RAM."""
    deleted_any = False
    try:
        client = get_redis_client()
        res = await client.delete(key)
        deleted_any = bool(res)
    except Exception:
        pass

    async with _get_in_memory_lock():
        if key in _in_memory_fallback_store:
            del _in_memory_fallback_store[key]
            deleted_any = True

    return deleted_any
