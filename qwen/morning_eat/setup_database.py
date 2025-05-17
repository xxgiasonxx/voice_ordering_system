# 建立麥當勞菜單資料庫（SQLite）從 Excel 資料
import sqlite3
import pandas as pd

def create_menu_database(excel_file='morning_eat.xlsx'):
    # 讀取 Excel
    xl = pd.ExcelFile(excel_file)
    
    # 連接到 SQLite 資料庫
    conn = sqlite3.connect('morning_eat.db')
    cursor = conn.cursor()

    # 創建表格
    # 主餐表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main_menu (
            id INTEGER PRIMARY KEY,
            class TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            add_egg BOOLEAN NOT NULL,
            cheese BOOLEAN NOT NULL,
            kimchi BOOLEAN NOT NULL,
            roast BOOLEAN NOT NULL,
            cheese_milk BOOLEAN NOT NULL,
            danish BOOLEAN NOT NULL,
            combo TEXT NOT NULL,
            vegetarian BOOLEAN NOT NULL,
            recommended BOOLEAN NOT NULL
        )
    ''')

    # 套餐表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS combo_menu (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drink_item (
            id TEXT PRIMARY KEY,
            class TEXT NOT NULL,
            name TEXT NOT NULL,
            M REAL NOT NULL,
            L REAL
        )
    ''')



    # 插入資料
    # 主餐
    menu_df = xl.parse('food_item', usecols=['id', 'class', 'name', 'price', 'add_egg', 'cheese', 'kimchi', '燒肉', '起司牛奶', '山型丹麥', 'combo', '素食', '推薦'])
    menu_df['add_egg'] = menu_df['add_egg'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['cheese'] = menu_df['cheese'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['kimchi'] = menu_df['kimchi'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['roast'] = menu_df['燒肉'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['cheese_milk'] = menu_df['起司牛奶'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['danish'] = menu_df['山型丹麥'].apply(lambda x: 1 if x == '有' else 0)
    menu_df['combo'] = menu_df['combo'].apply(lambda x: "A/B/C/D" if x == 'A/B/C/D' else "無")
    menu_df['vegetarian'] = menu_df['素食'].apply(lambda x: 1 if x == '可' else 0)
    menu_df['recommended'] = menu_df['推薦'].apply(lambda x: 1 if x == '推' else 0)
    print(menu_df) # This will show the DataFrame with 14 columns before selection
    
    # Select the final desired columns, this also drops the original Chinese-named columns
    # that were used to create 'danish', 'vegetarian', and 'recommended'.
    final_column_names = ['id', 'class', 'name', 'price', 'add_egg', 'cheese', 'kimchi', 'roast', 'cheese_milk', 'danish', 'combo', 'vegetarian', 'recommended']
    menu_df = menu_df[final_column_names]
    menu_df.to_sql('main_menu', conn, if_exists='append', index=False)

    # 套餐
    combo_df = xl.parse('food_combo', usecols=['id', 'name', 'price', 'desc'])
    combo_df.columns = ['id', 'name', 'price', 'description']
    combo_df.to_sql('combo_menu', conn, if_exists='append', index=False)

    # 飲料
    drink_df = xl.parse('drink_item', usecols=['id', 'class', 'name', 'M', 'L'])
    drink_df.columns = ['id', 'class', 'name', 'M', 'L']
    drink_df.to_sql('drink_item', conn, if_exists='append', index=False)

    conn.commit()
    conn.close()
    print("晨間廚房菜單資料庫建立完成！")

if __name__ == "__main__":
    create_menu_database()