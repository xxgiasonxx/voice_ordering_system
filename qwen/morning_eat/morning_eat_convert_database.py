# File: load_menu_to_chroma.py
# 從 SQLite 載入麥當勞菜單並存進 Chroma 向量資料庫
import sqlite3
import json
import pickle
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
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
    conn = sqlite3.connect('morning_eat.db')
    cursor = conn.cursor()

    # 定義所有表格
    tables = ['main_menu', 'combo_menu', 'drink_item']
    table_names = {
        'main_menu': {
            'id': 'id',
            'class': '類別',
            'name': '品項名稱',
            'price': '價格',
            'add_egg': '加蛋',
            'cheese': '起司',
            'kimchi': '泡菜',
            'roast': '燒肉',
            'cheese_milk': '起司牛奶',
            'danish': '山型丹麥',
            'combo': '套餐',
            'vegetarian': '素食',
            'recommended': '推薦'
        },
        'combo_menu': {
            'id': 'id',
            'name': '套餐名稱',
            'price': '價格',
            'description': '內容物'
        },
        'drink_item': {
            'id': 'id',
            'name': '飲品名稱',
            'price': '價格',
            'M': 'M中杯',
            'L': 'L大杯',
        }
    }
    documents = []

    # 從每個表格載入資料並轉成 Document
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        # print(table, rows)
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            row_dict = dict(zip(columns, row))
            content = ""

            for key, value in row_dict.items():
                if value == 0:
                    continue
                if key in table_names[table]:
                    content += f"{table_names[table][key]}: {value}{' 元' if key == 'price' or key == 'M' or key == 'L' else ''}\n"
            doc = Document(page_content=content, metadata={"table": table, "class": row_dict.get('class', '套餐'), "name": row_dict['name']})
            documents.append(doc)

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
            collection_name="morning_menu",
            persist_directory=persist_directory
        )
        print(f"Chroma 向量資料庫已儲存至 {persist_directory}")
        test = vectorstore.similarity_search("蛋餅", k=10)
        print("測試查詢結果：")
        for doc in test:
            print(doc.page_content)
            print("---")
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
    embedding_model = OllamaEmbeddings(model="qwen3:0.6b")
    
    # 設定儲存選項
    use_json = True
    use_pkl = False
    persist_directory = "./chroma_db"

    # 載入並儲存至 Chroma
    vectorstore = load_menu_to_vectorstore(
        embedding_model=embedding_model,
        use_json=use_json,
        use_pkl=use_pkl,
        persist_directory=persist_directory
    )
    print("向量資料庫載入完成：", vectorstore)