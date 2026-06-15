"""Load xlsx into SQLite, then migrate to PostgreSQL using raw SQL."""
import os
import sqlite3
import pandas as pd

db_path = '/app/backend/db/morning_eat.db'
xlsx_path = '/app/backend/morning_eat.xlsx'

# Step 1: Load xlsx into SQLite
print("=== Step 1: Loading xlsx into SQLite ===")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DELETE FROM main_menu")
cursor.execute("DELETE FROM combo_menu")
cursor.execute("DELETE FROM drink_item")

xl = pd.ExcelFile(xlsx_path)

menu_df = xl.parse('food_item', usecols=['id','class','name','price','add_egg','cheese','kimchi','燒肉','起司牛奶','山型丹麥','combo','素食','推薦'])
menu_df['add_egg']    = menu_df['add_egg'].apply(lambda x: 1 if x == '有' else 0)
menu_df['cheese']     = menu_df['cheese'].apply(lambda x: 1 if x == '有' else 0)
menu_df['kimchi']     = menu_df['kimchi'].apply(lambda x: 1 if x == '有' else 0)
menu_df['roast']      = menu_df['燒肉'].apply(lambda x: 1 if x == '有' else 0)
menu_df['cheese_milk'] = menu_df['起司牛奶'].apply(lambda x: 1 if x == '有' else 0)
menu_df['danish']     = menu_df['山型丹麥'].apply(lambda x: 1 if x == '有' else 0)
menu_df['combo']      = menu_df['combo'].apply(lambda x: "A/B/C/D" if x == 'A/B/C/D' else "無")
menu_df['vegetarian']  = menu_df['素食'].apply(lambda x: 1 if x == '可' else 0)
menu_df['recommended'] = menu_df['推薦'].apply(lambda x: 1 if x == '推' else 0)
cols = ['id','class','name','price','add_egg','cheese','kimchi','roast','cheese_milk','danish','combo','vegetarian','recommended']
menu_df[cols].to_sql('main_menu', conn, if_exists='append', index=False)

combo_df = xl.parse('food_combo', usecols=['id','name','price','desc'])
combo_df.columns = ['id','name','price','description']
combo_df.to_sql('combo_menu', conn, if_exists='append', index=False)

drink_df = xl.parse('drink_item', usecols=['id','class','name','M','L'])
drink_df.columns = ['id','class','name','M','L']
drink_df.to_sql('drink_item', conn, if_exists='append', index=False)

conn.commit()
cursor.execute('SELECT COUNT(*) FROM main_menu')
print(f"SQLite main_menu: {cursor.fetchone()[0]} rows")
cursor.execute('SELECT COUNT(*) FROM combo_menu')
print(f"SQLite combo_menu: {cursor.fetchone()[0]} rows")
cursor.execute('SELECT COUNT(*) FROM drink_item')
print(f"SQLite drink_item: {cursor.fetchone()[0]} rows")

# Step 2: Migrate to PostgreSQL using raw SQL
print("\n=== Step 2: Migrating to PostgreSQL ===")
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@postgres:5432/morning_eat")
pg_conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
pg_cur = pg_conn.cursor()

# Create tables
pg_cur.execute("DROP TABLE IF EXISTS main_menu CASCADE")
pg_cur.execute("DROP TABLE IF EXISTS combo_menu CASCADE")
pg_cur.execute("DROP TABLE IF EXISTS drink_item CASCADE")

pg_cur.execute("""CREATE TABLE main_menu (
    id INTEGER PRIMARY KEY,
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

pg_cur.execute("""CREATE TABLE combo_menu (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT NOT NULL
)""")

pg_cur.execute("""CREATE TABLE drink_item (
    id TEXT PRIMARY KEY,
    class TEXT NOT NULL,
    name TEXT NOT NULL,
    M REAL NOT NULL,
    L REAL
)""")

pg_conn.commit()
print("PostgreSQL tables created.")

# Read from SQLite and insert to PostgreSQL
cursor.execute("SELECT * FROM main_menu")
cols = [desc[0] for desc in cursor.description]
for row in cursor.fetchall():
    row_dict = dict(zip(cols, row))
    pg_cur.execute("""INSERT INTO main_menu (id,class,name,price,add_egg,cheese,kimchi,roast,cheese_milk,danish,combo,vegetarian,recommended)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (row_dict['id'], row_dict['class'], row_dict['name'], row_dict['price'],
         row_dict['add_egg'], row_dict['cheese'], row_dict['kimchi'], row_dict['roast'],
         row_dict['cheese_milk'], row_dict['danish'], row_dict['combo'],
         row_dict['vegetarian'], row_dict['recommended']))

cursor.execute("SELECT * FROM combo_menu")
cols = [desc[0] for desc in cursor.description]
for row in cursor.fetchall():
    row_dict = dict(zip(cols, row))
    pg_cur.execute("""INSERT INTO combo_menu (id,name,price,description) VALUES (%s,%s,%s,%s)""",
        (row_dict['id'], row_dict['name'], row_dict['price'], row_dict['description']))

cursor.execute("SELECT * FROM drink_item")
cols = [desc[0] for desc in cursor.description]
for row in cursor.fetchall():
    row_dict = dict(zip(cols, row))
    pg_cur.execute("""INSERT INTO drink_item (id,class,name,M,L) VALUES (%s,%s,%s,%s,%s)""",
        (row_dict['id'], row_dict['class'], row_dict['name'], row_dict['M'], row_dict['L']))

pg_conn.commit()

# Verify
pg_cur.execute('SELECT COUNT(*) FROM main_menu')
print(f"PostgreSQL main_menu: {pg_cur.fetchone()[0]} rows")
pg_cur.execute('SELECT COUNT(*) FROM combo_menu')
print(f"PostgreSQL combo_menu: {pg_cur.fetchone()[0]} rows")
pg_cur.execute('SELECT COUNT(*) FROM drink_item')
print(f"PostgreSQL drink_item: {pg_cur.fetchone()[0]} rows")

conn.close()
pg_conn.close()
print("\nMigration complete!")