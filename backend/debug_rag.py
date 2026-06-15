import os
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("CHROMADB_PATH", "./db/chroma_db")
os.environ.setdefault("DB_PATH", "./db/morning_eat.db")
os.environ.setdefault("LLM_MODEL", "qwen3.5:0.8b")

from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from rag.CRUD_database import create_connection
from rag.rag_morning_eat import create_prompt_template

base_url = os.getenv("OLLAMA_BASE_URL")

emb = OllamaEmbeddings(model="nomic-embed-text", base_url=base_url)
vs = Chroma(collection_name="morning_menu", embedding_function=emb, persist_directory=os.getenv("CHROMADB_PATH"))
conn = create_connection(os.getenv("DB_PATH"))

query = "我要一份原味蛋餅"
order_state = {"items": [], "total_price": 0, "status": "start"}
cus_choice = {"加蛋": 10, "起司": 10, "泡菜": 10}

# Step 1: RAG search
docs = vs.similarity_search(query, k=50)
context = "\n\n".join([doc.page_content for doc in docs])
print("=== RAG context ===")
print(context[:500])
print()

# Step 2: Prompt
prompt, ex_json = create_prompt_template()
print("=== Prompt (truncated) ===")
print(prompt.template[-300:])
print()

# Step 3: LLM call
llm = OllamaLLM(model="qwen3.5:0.8b", base_url=base_url)
chain = prompt | llm
raw = chain.invoke({
    "json": ex_json,
    "history": [],
    "context": context,
    "order_state": order_state,
    "query": query,
})
print("=== RAW LLM Response ===")
print(raw)
print()
