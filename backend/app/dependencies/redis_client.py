from contextlib import contextmanager

import redis

from app.configs.app_settings import settings

TERMINAL_JOB_TTL_SECONDS = 3 * 24 * 3600  # 3 days

redis_pool = None


def init_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(settings.redis_url)


def close_redis_pool():
    global redis_pool
    if redis_pool:
        redis_pool.disconnect()
        redis_pool = None


def get_redis_client():
    if redis_pool is None:
        raise RuntimeError("Redis pool not initialized, call init_redis_pool() first.")
    r = redis.Redis(connection_pool=redis_pool)
    yield r


@contextmanager
def get_worker_redis():
    if redis_pool is None:
        raise RuntimeError("Redis pool not initialized, call init_redis_pool() first.")
    r = redis.Redis(connection_pool=redis_pool)
    yield r
