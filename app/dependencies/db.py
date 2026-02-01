from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool

from app.configs.app_settings import settings
from app.repositories import *

db_pool = None

def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = SimpleConnectionPool(minconn=1,maxconn=10,
                                       dsn=settings.database_url)

def close_db_pool():
    global db_pool
    if db_pool:
        db_pool.closeall()
        db_pool = None

def get_cursor():
    if db_pool is None:
        raise RuntimeError("DB pool not initialized, Call init_db_pool() first.")
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        db_pool.putconn(conn)

@contextmanager
def get_worker_cursor():
    return get_cursor()

def init_db_tables() -> None:
    if db_pool is None:
        raise RuntimeError("DB pool not initialized, Call init_db_pool() first.")
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        cursor.execute(JobsRepository._create())
        cursor.execute(PlansRepository._create())
        cursor.execute(ArtifactsRepository._create())
        conn.commit()
    finally:
        cursor.close()
        db_pool.putconn(conn)

