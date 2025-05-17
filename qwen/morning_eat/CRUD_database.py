import sqlite3
from sqlite3 import Error
from datetime import datetime
from typing import List, Tuple, Optional
from dataclasses import dataclass


def create_connection(db_file: str = "morning_eat.db") -> Optional[sqlite3.Connection]:
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def query_main_menu(conn: sqlite3.Connection, id: str) -> List[Tuple]:
    """Execute a query and return the results."""
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM main_menu WHERE id == {id}")
    return cur.fetchall()

def query_combo_menu(conn: sqlite3.Connection, id: str) -> List[Tuple]:
    """Execute a query and return the results."""
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM combo_menu WHERE id == {id}")
    return cur.fetchall()

def query_name_to_price(conn: sqlite3.Connection, cls: str, name: str) -> List[Tuple]:
    """Execute a query and return the results."""
    table = "main_menu" if cls != "特調飲品" else "drink_item"
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE class == '{cls}' AND name == '{name}'")
    return cur.fetchall()
