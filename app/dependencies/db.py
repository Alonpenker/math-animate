from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool

db_pool = None

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
