# 建立麥當勞菜單資料庫（SQLite）
import sqlite3
import pandas as pd

def create_menu_database():
    # 連接到 SQLite 資料庫（若不存在則創建）
    conn = sqlite3.connect('mcdonalds_menu.db')
    cursor = conn.cursor()

    # 創建菜單表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            ingredients TEXT,
            customization_options TEXT
        )
    ''')

    # 插入台灣麥當勞菜單範例資料
    menu_items = [
        ('大麥克', '漢堡', 99.0, '牛肉、生菜、酸黃瓜、洋蔥、芝麻麵包、美乃滋', '去酸黃瓜、無美乃滋'),
        ('麥香雞', '漢堡', 79.0, '雞肉、生菜、麵包、美乃滋', '無美乃滋'),
        ('麥香魚', '漢堡', 79.0, '魚排、生菜、塔塔醬、麵包', '無塔塔醬'),
        ('薯條', '點心', 45.0, '馬鈴薯、鹽', '多炸、無鹽、多胡椒'),
        ('麥克雞塊', '點心', 69.0, '雞肉', '糖醋醬、蜂蜜芥末醬'),
        ('可口可樂', '飲料', 35.0, '可樂、冰塊', '去冰、少冰、正常冰'),
        ('檸檬風味紅茶', '飲料', 35.0, '紅茶、檸檬香料、冰塊', '去冰、少冰、正常冰'),
        ('冰美式咖啡', '飲料', 55.0, '咖啡、冰塊', '去冰、加糖'),
        ('玉米湯', '湯品', 49.0, '玉米、奶油', '無'),
        ('巧克力聖代', '甜點', 39.0, '巧克力醬、冰淇淋', '無巧克力醬')
    ]

    cursor.executemany('''
        INSERT INTO menu (name, category, price, ingredients, customization_options)
        VALUES (?, ?, ?, ?, ?)
    ''', menu_items)

    conn.commit()
    conn.close()
    print("麥當勞菜單資料庫建立完成！")

if __name__ == "__main__":
    create_menu_database()