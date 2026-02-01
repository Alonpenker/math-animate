from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool

from app.repositories import *

db_pool = None

# TODO: move the connections to .env file
DB_HOST = "postgres"
DB_PORT = 5432
DB_NAME = "manim"
DB_USER = "manim"
DB_PASSWORD = "manim"

def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = SimpleConnectionPool(minconn=1,maxconn=10,
                                       host=DB_HOST,
                                       port=DB_PORT,
                                       dbname=DB_NAME,
                                       user=DB_USER,
                                       password=DB_PASSWORD)

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

