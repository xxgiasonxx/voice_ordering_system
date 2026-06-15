"""Migrate data from SQLite (morning_eat.db) to PostgreSQL."""
import os
import sqlite3

import psycopg2
from psycopg2.extras import RealDictCursor

SQLITE_DB = os.path.join(os.path.dirname(__file__), "db", "morning_eat.db")  # resolves to /app/backend/db/... inside container
DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/morning_eat")

def get_pg_conn():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def get_sqlite_conn():
    return sqlite3.connect(SQLITE_DB)

def create_pg_tables(pg_conn):
    cur = pg_conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS main_menu (
        id SERIAL PRIMARY KEY,
        class TEXT NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        add_egg INTEGER NOT NULL DEFAULT 0,
        cheese INTEGER NOT NULL DEFAULT 0,
        kimchi INTEGER NOT NULL DEFAULT 0,
        roast INTEGER NOT NULL DEFAULT 0,
        cheese_milk INTEGER NOT NULL DEFAULT 0,
        danish INTEGER NOT NULL DEFAULT 0,
        combo TEXT NOT NULL DEFAULT '無',
        vegetarian INTEGER NOT NULL DEFAULT 0,
        recommended INTEGER NOT NULL DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS combo_menu (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS drink_item (
        id TEXT PRIMARY KEY,
        class TEXT NOT NULL,
        name TEXT NOT NULL,
        M REAL NOT NULL,
        L REAL
    )""")

    pg_conn.commit()
    print("PostgreSQL tables created.")

def migrate_table(pg_conn, sqlite_conn, table_name, cols, transform_fn=None):
    pg_cur = pg_conn.cursor()
    sqlite_cur = sqlite_conn.cursor()

    sqlite_cur.execute(f"SELECT {','.join(cols)} FROM {table_name}")
    rows = sqlite_cur.fetchall()
    if not rows:
        print(f"No rows in {table_name}, skipping.")
        return

    pg_cur.execute(f"DELETE FROM {table_name}")

    for row in rows:
        vals = list(row)
        if transform_fn:
            vals = transform_fn(vals)
        placeholders = ','.join(['%s'] * len(vals))
        pg_cur.execute(f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({placeholders})", vals)

    pg_conn.commit()
    print(f"Migrated {len(rows)} rows to {table_name}.")

def main():
    print("Starting SQLite → PostgreSQL migration...")
    print(f"SQLite DB: {SQLITE_DB}")
    print(f"PostgreSQL: {DB_URL}")

    sqlite_conn = get_sqlite_conn()
    pg_conn = get_pg_conn()

    create_pg_tables(pg_conn)

    migrate_table(pg_conn, sqlite_conn, "main_menu",
        ['id','class','name','price','add_egg','cheese','kimchi','roast','cheese_milk','danish','combo','vegetarian','recommended'])

    migrate_table(pg_conn, sqlite_conn, "combo_menu",
        ['id','name','price','description'])

    migrate_table(pg_conn, sqlite_conn, "drink_item",
        ['id','class','name','M','L'])

    sqlite_conn.close()
    pg_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    main()