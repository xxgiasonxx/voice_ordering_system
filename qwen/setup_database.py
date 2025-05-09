# 建立麥當勞菜單資料庫（SQLite）從 Excel 資料
import sqlite3
import pandas as pd

def create_menu_database(excel_file='mcdonalds_menu_data.xlsx'):
    # 讀取 Excel
    xl = pd.ExcelFile(excel_file)
    
    # 連接到 SQLite 資料庫
    conn = sqlite3.connect('mcdonalds_menu.db')
    cursor = conn.cursor()

    # 創建表格
    # 主餐表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    # 配餐表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS side_orders (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price TEXT,  -- 存多種價格 (如 "45 (中) / 60 (大)")
            size_options TEXT
        )
    ''')

    # 飲料表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drinks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price TEXT,
            size_options TEXT,
            is_hot INTEGER,
            is_iced INTEGER
        )
    ''')

    # 甜點表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snacks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL,
            description TEXT
        )
    ''')

    # McCafe 表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mccafe (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price TEXT,
            is_drink INTEGER,
            is_hot INTEGER,
            is_iced INTEGER,
            description TEXT
        )
    ''')

    #快樂兒童餐
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS happy_meals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            main_choice_product_id INTEGER,
            side_choice_side_order_id INTEGER,
            drink_choice_drink_id INTEGER,
            toy_description TEXT,
            price REAL,
            FOREIGN KEY (main_choice_product_id) REFERENCES menu(id),
            FOREIGN KEY (side_choice_side_order_id) REFERENCES side_orders(id),
            FOREIGN KEY (drink_choice_drink_id) REFERENCES drinks(id)
        )
    ''')

    # 套餐表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            main_course_id INTEGER,
            default_side_order_id INTEGER,
            default_drink_id INTEGER,
            price REAL,
            upgrade_options TEXT,
            is_breakfast_combo INTEGER,
            FOREIGN KEY (main_course_id) REFERENCES menu(id),
            FOREIGN KEY (default_side_order_id) REFERENCES side_orders(id),
            FOREIGN KEY (default_drink_id) REFERENCES drinks(id)
        )
    ''')

    # 插入資料
    # 主餐
    menu_df = xl.parse('MainCourses', usecols=['ProductID', 'ProductName', 'Category', 'Description', 'PriceSingle'])
    menu_df.columns = ['id', 'name', 'category', 'description', 'price']
    menu_df.to_sql('menu', conn, if_exists='append', index=False)

    # 配餐
    side_df = xl.parse('Side_Orders', usecols=['SideOrderID', 'SideOrderName', 'Category', 'Price_Single (NT$)', 'SizeOptions'])
    side_df.columns = ['id', 'name', 'category', 'price', 'size_options']
    side_df.to_sql('side_orders', conn, if_exists='append', index=False)

    # 飲料
    drink_df = xl.parse('Drinks', usecols=['DrinkID', 'DrinkName', 'Category', 'Price_Single (NT$)', 'SizeOptions', 'Is_Hot', 'Is_Iced'])
    drink_df.columns = ['id', 'name', 'category', 'price', 'size_options', 'is_hot', 'is_iced']
    drink_df.to_sql('drinks', conn, if_exists='append', index=False)

    # 甜點
    snack_df = xl.parse('Snacks_Desserts', usecols=['SnackID', 'SnackName', 'Category', 'Price_Single (NT$)', 'Description'])
    snack_df.columns = ['id', 'name', 'category', 'price', 'description']
    snack_df.to_sql('snacks', conn, if_exists='append', index=False)

    # McCafe
    mccafe_df = xl.parse('McCafé_Items', usecols=['McCafeID', 'McCafeItemName', 'Category', 'Price_Single (NT$)', 'Is_Drink', 'Is_Hot', 'Is_Iced', 'Description'])
    mccafe_df.columns = ['id', 'name', 'category', 'price', 'is_drink', 'is_hot', 'is_iced', 'description']
    mccafe_df.to_sql('mccafe', conn, if_exists='append', index=False)

    #快樂兒童餐
    happy_meal_df = xl.parse('Happy_Meals', usecols=['HappyMealID', 'HappyMealName', 'MainChoiceProductID ', 'SideChoiceSideOrderID', 'DrinkChoiceDrinkID', 'ToyDescription', 'Price_HappyMeal (NT$)'])
    happy_meal_df.columns = ['id', 'name', 'main_choice_product_id', 'side_choice_side_order_id', 'drink_choice_drink_id', 'toy_description', 'price']
    happy_meal_df.to_sql('happy_meals', conn, if_exists='append', index=False)

    # 套餐
    combo_df = xl.parse('Combos', usecols=['ComboID', 'ComboName', 'MainCourseID (FK)', 'DefaultSideOrderID (FK)', 'DefaultDrinkID (FK)', 'Price_Combo (NT$)', 'UpgradeOptions', 'Is_BreakfastCombo'])
    combo_df.columns = ['id', 'name', 'main_course_id', 'default_side_order_id', 'default_drink_id', 'price', 'upgrade_options', 'is_breakfast_combo']
    combo_df.to_sql('combos', conn, if_exists='append', index=False)

    conn.commit()
    conn.close()
    print("麥當勞菜單資料庫建立完成！")

if __name__ == "__main__":
    create_menu_database()