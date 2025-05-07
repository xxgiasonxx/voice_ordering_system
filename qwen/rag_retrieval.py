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
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 從資料庫載入菜單並轉成向量
def load_menu_to_vectorstore():
    conn = sqlite3.connect('mcdonalds_menu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, category, price, ingredients, customization_options FROM menu")
    rows = cursor.fetchall()
    conn.close()

    # 轉成 LangChain Document 格式
    documents = []
    for row in rows:
        name, category, price, ingredients, customization = row
        content = f"品項: {name}\n類別: {category}\n價格: {price} 元\n成分: {ingredients}\n客製選項: {customization}"
        documents.append(Document(page_content=content, metadata={"name": name}))

    # 存進 Chroma 向量資料庫
    vectorstore = Chroma.from_documents(documents, embedding_model, collection_name="mcdonalds_menu")
    return vectorstore

# RAG 檢索 + 生成回應
def rag_query(query, vectorstore):
    # 檢索相關菜單
    docs = vectorstore.similarity_search(query, k=3)  # 取前 3 個相關品項
    context = "\n\n".join([doc.page_content for doc in docs])

    # 建構 prompt
    system_prompt = "你是一個麥當勞點餐助手，根據用戶查詢和菜單資訊，生成自然、親切的回應。用台灣口語！"
    prompt = f"{system_prompt}\n\n菜單資訊:\n{context}\n\n用戶: {query}\n助手: "
    
    # 用 Qwen3 生成回應
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=512)
    response = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
    return response

if __name__ == "__main__":
    vectorstore = load_menu_to_vectorstore()
    test_queries = [
        "我要一個大麥克",
        "有什麼飲料？",
        "薯條可以無鹽嗎？",
        "麥香雞多少錢？"
    ]
    for query in test_queries:
        print(f"用戶: {query}")
        print(f"助手: {rag_query(query, vectorstore)}")
        print("-" * 50)