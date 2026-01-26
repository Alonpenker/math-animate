import sqlite3

db_pool = None

def init_db(database='app.db'):
    global db_conn
    if db_conn is None:
        db_conn = sqlite3.connect(database, check_same_thread=False)

def close_db():
    global db_conn
    if db_conn:
        db_conn.close()
        db_conn = None

def get_cursor():
    if db_conn is None:
        raise RuntimeError("DB connection not initialized. Call init_db() first.")
    
    cursor = db_conn.cursor()
    try:
        yield cursor
        db_conn.commit()
    finally:
        cursor.close()