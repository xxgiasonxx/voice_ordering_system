# 實現 RAG 檢索，結合 Qwen3 0.6B 生成回應
import sqlite3
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 載入微調後的 Qwen3 0.6B
model_path = "./qwen3_finetuned"  # 假設你已微調
model = AutoModelForCausalLM.from_pretrained(model_path, load_in_4bit=True, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 初始化嵌入模型
embedding_model = HuggingFaceEmbeddings(model_name="Qwen/Qwen3-0.6B")

# 從資料庫載入菜單並轉成向量
def load_menu_to_vectorstore():
    conn = sqlite3.connect('mcdonalds_menu.db')
    cursor = conn.cursor()

    # 載入所有表格資料
    tables = ['menu', 'side_orders', 'drinks', 'snacks', 'mccafe', 'combos']
    documents = []

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        for row in rows:
            row_dict = dict(zip(columns, row))
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
                cursor.execute(f"SELECT name FROM menu WHERE id = {row_dict['main_course_id']}")
                main_name = cursor.fetchone()[0]
                cursor.execute(f"SELECT name FROM side_orders WHERE id = {row_dict['default_side_order_id']}")
                side_name = cursor.fetchone()[0]
                cursor.execute(f"SELECT name FROM drinks WHERE id = {row_dict['default_drink_id']}")
                drink_name = cursor.fetchone()[0]
                content = f"套餐: {row_dict['name']}\n主餐: {main_name}\n配餐: {side_name}\n飲料: {drink_name}\n價格: {row_dict['price']} 元\n升級選項: {row_dict['upgrade_options']}\n早餐套餐: {row_dict['is_breakfast_combo']}"

            documents.append(Document(page_content=content, metadata={"table": table, "name": row_dict['name']}))

    conn.close()

    # 存進 Chroma 向量資料庫
    vectorstore = Chroma.from_documents(documents, embedding_model, collection_name="mcdonalds_menu")
    return vectorstore

# RAG 檢索 + 生成回應
def rag_query(query, vectorstore):
    # 檢索相關菜單
    docs = vectorstore.similarity_search(query, k=3)  # 取前 3 個相關品項
    context = "\n\n".join([doc.page_content for doc in docs])

    # 建構 prompt
    system_prompt = "你是一個麥當勞點餐助手，根據用戶查詢和菜單資訊，生成自然、親切的回應。用台灣口語！如果用戶問套餐，提到主餐、配餐和飲料；如果問單點，提到價格和客製選項。"
    prompt = f"{system_prompt}\n\n菜單資訊:\n{context}\n\n用戶: {query}\n助手: "
    
    # 用 Qwen3 生成回應
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=512)
    response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    vectorstore = load_menu_to_vectorstore()
    test_queries = [
        "我要一個大麥克套餐",
        "有什麼飲料可以選？",
        "薯條可以無鹽嗎？",
        "麥香雞多少錢？"
    ]
    for query in test_queries:
        print(f"用戶: {query}")
        print(f"助手: {rag_query(query, vectorstore)}")
        print("-" * 50)