# File: load_menu_to_chroma.py
# 從 SQLite 載入麥當勞菜單並存進 Chroma 向量資料庫
import sqlite3
import json
import pickle
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document

def load_menu_to_vectorstore(embedding_model, use_json=False, use_pkl=False, persist_directory="./chroma_db"):
    """
    從 SQLite 資料庫載入麥當勞菜單，轉成向量並存進 Chroma 資料庫。
    
    Args:
        embedding_model: 用於向量化的嵌入模型（如 HuggingFaceEmbeddings）
        use_json (bool): 是否將資料存成 JSON（menu.json）
        use_pkl (bool): 是否將資料存成 Pickle（menu.pkl）
        persist_directory (str): Chroma 資料庫儲存路徑
    
    Returns:
        Chroma: 向量資料庫實例
    """
    # 連接到 SQLite 資料庫
    conn = sqlite3.connect('mcdonalds_menu.db')
    cursor = conn.cursor()

    # 定義所有表格
    tables = ['menu', 'side_orders', 'drinks', 'snacks', 'mccafe', 'combos']
    documents = []

    # 從每個表格載入資料並轉成 Document
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        for row in rows:
            row_dict = dict(zip(columns, row))
            content = ""

            if table == 'menu':
                content = f"品項: {row_dict['name']}\n類別: {row_dict['category']}\n價格: {row_dict['price']} 元\n描述: {row_dict['description']}"
            elif table == 'side_orders':
                content = f"配餐: {row_dict['name']}\n類別: {row_dict['category']}\n價格: {row_dict['price']}\n尺寸選項: {row_dict['size_options']}"
            elif table == 'drinks':
                content = f"飲料: {row_dict['name']}\n類別: {row_dict['category']}\n價格: {row_dict['price']}\n尺寸選項: {row_dict['size_options']}\n可熱飲: {row_dict['is_hot']}\n可冰飲: {row_dict['is_iced']}"
            elif table == 'snacks':
                content = f"甜點: {row_dict['name']}\n類別: {row_dict['category']}\n價格: {row_dict['price']} 元\n描述: {row_dict['description']}"
            elif table == 'mccafe':
                content = f"McCafe: {row_dict['name']}\n類別: {row_dict['category']}\n價格: {row_dict['price']}\n描述: {row_dict['description']}\n是飲料: {row_dict['is_drink']}\n可熱飲: {row_dict['is_hot']}\n可冰飲: {row_dict['is_iced']}"
            elif table == 'combos':
                # 查詢主餐名稱
                cursor.execute(f"SELECT name FROM menu WHERE id = {row_dict['main_course_id']}")
                result = cursor.fetchone()
                main_name = result[0] if result else "未知品項"

                # 查詢配餐名稱
                cursor.execute(f"SELECT name FROM side_orders WHERE id = {row_dict['default_side_order_id']}")
                result = cursor.fetchone()
                side_name = result[0] if result else "未知配餐"

                # 查詢飲料名稱
                cursor.execute(f"SELECT name FROM drinks WHERE id = {row_dict['default_drink_id']}")
                result = cursor.fetchone()
                drink_name = result[0] if result else "未知飲料"

                content = f"套餐: {row_dict['name']}\n主餐: {main_name}\n配餐: {side_name}\n飲料: {drink_name}\n價格: {row_dict['price']} 元\n升級選項: {row_dict['upgrade_options']}\n早餐套餐: {row_dict['is_breakfast_combo']}"

            documents.append(Document(page_content=content, metadata={"table": table, "name": row_dict['name']}))

    conn.close()
    print(f"已生成 {len(documents)} 筆菜單資料：")
    for doc in documents[:3]:  # 印前 3 筆確認
        print(doc.page_content)
        print("---")

    # 存成 JSON 或 Pickle（可選）
    if use_json:
        with open("menu.json", "w", encoding="utf-8") as f:
            json.dump(serialize_documents(documents), f, ensure_ascii=False, indent=2)
        print("已儲存 menu.json")
    if use_pkl:
        with open("menu.pkl", "wb") as f:
            pickle.dump(documents, f)
        print("已儲存 menu.pkl")

    # 存進 Chroma 向量資料庫
    try:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            collection_name="mcdonalds_menu",
            persist_directory=persist_directory
        )
        print(f"Chroma 向量資料庫已儲存至 {persist_directory}")
        return vectorstore
    except Exception as e:
        print(f"儲存 Chroma 資料庫失敗：{e}")
        raise e

def serialize_documents(documents):
    """將 Document 物件序列化為 JSON 格式"""
    return [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in documents
    ]

if __name__ == "__main__":
    # 初始化嵌入模型
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # 設定儲存選項
    use_json = False
    use_pkl = True
    persist_directory = "./chroma_db"

    # 載入並儲存至 Chroma
    vectorstore = load_menu_to_vectorstore(
        embedding_model=embedding_model,
        use_json=use_json,
        use_pkl=use_pkl,
        persist_directory=persist_directory
    )
    print("向量資料庫載入完成：", vectorstore)