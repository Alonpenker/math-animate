from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

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

def _get_registered_connection():
    if db_pool is None:
        raise RuntimeError("DB pool not initialized, Call init_db_pool() first.")
    conn = db_pool.getconn()
    try:
        register_vector(conn)
    except Exception:
        db_pool.putconn(conn, close=True)
        raise
    return conn

def get_cursor():
    conn = _get_registered_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        if db_pool:
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
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(JobsRepository._create())
        cursor.execute(PlansRepository._create())
        cursor.execute(ArtifactsRepository._create())
        cursor.execute(KnowledgeRepository._create())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)
