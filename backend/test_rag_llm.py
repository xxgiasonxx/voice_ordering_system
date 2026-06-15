"""Test RAG with qwen3.5:0.8b LLM."""
import os
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("CHROMADB_PATH", "./db/chroma_db")
os.environ.setdefault("DB_PATH", "./db/morning_eat.db")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("LLM_MODEL", "qwen3.5:0.8b")

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from rag.rag_morning_eat import rag_query
from rag.CRUD_database import create_connection

base_url = os.getenv("OLLAMA_BASE_URL")

emb = OllamaEmbeddings(model="nomic-embed-text", base_url=base_url)
vs = Chroma(collection_name="morning_menu", embedding_function=emb, persist_directory=os.getenv("CHROMADB_PATH"))
conn = create_connection(os.getenv("DB_PATH"))

order_state = {"items": [], "total_price": 0, "status": "start"}
cus_choice = {"加蛋": 10, "起司": 10, "泡菜": 10}

resp, new_state = rag_query("我要一份原味蛋餅", [], vs, order_state, cus_choice, conn)
print("Response:", resp)
print("Order:", new_state["items"])