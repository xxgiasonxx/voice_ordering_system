"""Rebuild ChromaDB vectorstore with qwen3-embedding:0.6b (1024 dims)."""
import os
import shutil
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from rag.CRUD_database import create_connection

os.environ.setdefault("OLLAMA_BASE_URL", "http://ollama:11434")
os.environ.setdefault("CHROMADB_PATH", "./db/chroma_db")
os.environ.setdefault("DB_PATH", "./db/morning_eat.db")

base_url = os.getenv("OLLAMA_BASE_URL")
persist = os.getenv("CHROMADB_PATH")
db = os.getenv("DB_PATH")

emb = OllamaEmbeddings(model="qwen3-embedding:0.6b", base_url=base_url)
conn = create_connection(db)
c = conn.cursor()

tables = ['main_menu', 'combo_menu', 'drink_item']
table_names = {
    'main_menu': {
        'id': 'id', 'class': '類別', 'name': '品項名稱', 'price': '價格',
        'add_egg': '加蛋', 'cheese': '起司', 'kimchi': '泡菜',
        'roast': '燒肉', 'cheese_milk': '起司牛奶', 'danish': '山型丹麥',
        'combo': '套餐', 'vegetarian': '素食', 'recommended': '推薦'
    },
    'combo_menu': {
        'id': 'id', 'name': '套餐名稱', 'price': '價格', 'description': '內容物'
    },
    'drink_item': {
        'id': 'id', 'name': '飲品名稱', 'price': '價格', 'M': 'M中杯', 'L': 'L大杯',
    }
}

documents = []
for table in tables:
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    for row in rows:
        row_dict = dict(zip(columns, row))
        content = ""
        for key, value in row_dict.items():
            if value == 0:
                continue
            if key in table_names[table]:
                content += f"{table_names[table][key]}: {value}{' 元' if key == 'price' or key == 'M' or key == 'L' else ''}\n"
        documents.append(Document(
            page_content=content,
            metadata={"table": table, "class": row_dict.get('class', '套餐'), "name": row_dict['name']}
        ))

conn.close()
print(f"Total documents: {len(documents)}")
for doc in documents[:3]:
    print(doc.page_content)
    print("---")

if os.path.exists(persist):
    shutil.rmtree(persist)
    print(f"Deleted old: {persist}")

vs = Chroma.from_documents(
    documents=documents,
    embedding=emb,
    collection_name="morning_menu",
    persist_directory=persist,
)
test = vs.similarity_search("蛋餅", k=5)
print(f"Vectorstore rebuilt. Test query returned {len(test)} results.")
for doc in test:
    print(doc.page_content)
    print("---")
print(f"Done. Persisted at {persist}")