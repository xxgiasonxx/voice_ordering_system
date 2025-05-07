from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client["menu_db"]
collection = db["items"]

# 初始化菜單
initial_items = [
    {"name": "大麥克", "synonyms": ["麥克漢堡", "大漢堡"]},
    {"name": "雞塊", "synonyms": []},
    {"name": "芒果冰沙", "synonyms": ["芒果冰"]},
    {"name": "草莓奶昔", "synonyms": ["草莓飲料"]}
]
collection.delete_many({})
collection.insert_many(initial_items)

print("菜單初始化完成")