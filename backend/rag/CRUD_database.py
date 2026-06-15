import os
import sqlite3
from typing import Optional, Any

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def create_connection(db_file: str = None) -> Any:
    """
    Create a database connection.
    - If DB_URL env var is set: use PostgreSQL (psycopg2)
    - Otherwise: use SQLite (db_file path)
    """
    db_url = os.getenv("DB_URL")
    if db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn

    if db_file is None:
        db_file = os.getenv("DB_PATH", "./db/morning_eat.db")
    conn = sqlite3.connect(db_file)
    conn.row_factory = dict_factory
    return conn

def query_drink_menu(conn, id: str):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM drink_item WHERE id = {id}")
    result = cur.fetchone()
    if isinstance(result, dict):
        return result
    if result is None:
        return {}
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, result))

def query_main_menu(conn, id: str):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM main_menu WHERE id = {id}")
    result = cur.fetchone()
    if isinstance(result, dict):
        return result
    if result is None:
        return {}
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, result))

def query_combo_menu(conn, id: str):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM combo_menu WHERE id = '{id}'")
    result = cur.fetchone()
    if isinstance(result, dict):
        return result
    if result is None:
        return {}
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, result))

def query_name_to_price(conn, cls: str, name: str):
    cur = conn.cursor()
    table = "main_menu" if cls != "特調飲品" else "drink_item"
    cur.execute(f"SELECT * FROM {table} WHERE class = '{cls}' AND name = '{name}'")
    results = cur.fetchall()
    if not results:
        return []
    if isinstance(results[0], dict):
        return results
    return [dict(zip([desc[0] for desc in cur.description], row)) for row in results]