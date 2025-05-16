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
    conn = sqlite3.connect('morning_eat.db')
    cursor = conn.cursor()

    # 定義所有表格
    tables = ['main_menu', 'combo_menu']
    documents = []

    # 從每個表格載入資料並轉成 Document
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        for row in rows:
            row_dict = dict(zip(columns, row))
            content = ""

            if table == 'main_menu':
                content = f"id: {row_dict['id']}\n類別: {row_dict['class']}\n品項: {row_dict['name']}\n價格: {row_dict['price']} 元\n雙蛋: {row_dict['double_egg']}\n起司: {row_dict['cheese']}\n泡菜: {row_dict['kimchi']}\n山形丹麥: {row_dict['danish']}\n套餐: {row_dict['combo']}\n素食: {row_dict['vegetarian']}\n推薦: {row_dict['recommended']}"
            elif table == 'combo_menu':
                # 查詢主餐名稱
                content = f"id: {row_dict['id']}\n套餐: {row_dict['name']}套餐\n價格: {row_dict['price']} 元\n內容物: {row_dict['description']}"
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
            collection_name="morning_menu",
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
    embedding_model = HuggingFaceEmbeddings(model_name="ziqingyang/chinese-alpaca-2-7b-16k")
    
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