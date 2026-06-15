"""Load morning_eat.xlsx into SQLite database (morning_eat.db)."""
import os
import sqlite3
import pandas as pd

os.environ.setdefault("DB_PATH", "./db/morning_eat.db")

db_path = os.getenv("DB_PATH")
xlsx_path = os.path.join(os.path.dirname(__file__), "morning_eat.xlsx")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS main_menu (
    id INTEGER PRIMARY KEY, class TEXT NOT NULL, name TEXT NOT NULL,
    price REAL NOT NULL, add_egg INTEGER NOT NULL, cheese INTEGER NOT NULL,
    kimchi INTEGER NOT NULL, roast INTEGER NOT NULL, cheese_milk INTEGER NOT NULL,
    danish INTEGER NOT NULL, combo TEXT NOT NULL, vegetarian INTEGER NOT NULL,
    recommended INTEGER NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS combo_menu (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, description TEXT NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS drink_item (
    id TEXT PRIMARY KEY, class TEXT NOT NULL, name TEXT NOT NULL, M REAL NOT NULL, L REAL)''')

xl = pd.ExcelFile(xlsx_path)

cursor.execute("DELETE FROM main_menu")
cursor.execute("DELETE FROM combo_menu")
cursor.execute("DELETE FROM drink_item")

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
print(f"Inserted {len(menu_df)} main_menu rows")

combo_df = xl.parse('food_combo', usecols=['id','name','price','desc'])
combo_df.columns = ['id','name','price','description']
combo_df.to_sql('combo_menu', conn, if_exists='append', index=False)
print(f"Inserted {len(combo_df)} combo_menu rows")

drink_df = xl.parse('drink_item', usecols=['id','class','name','M','L'])
drink_df.columns = ['id','class','name','M','L']
drink_df.to_sql('drink_item', conn, if_exists='append', index=False)
print(f"Inserted {len(drink_df)} drink_item rows")

conn.commit()
conn.close()
print(f"Done. SQLite populated from {xlsx_path}")