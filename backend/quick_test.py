import os
os.environ["OLLAMA_BASE_URL"] = "http://ollama:11434"
from langchain_ollama import OllamaLLM, OllamaEmbeddings

llm = OllamaLLM(
    model="qwen2.5:1.5b",
    base_url=os.environ["OLLAMA_BASE_URL"],
    temperature=0.7,
    options={"num_predict": 2048},
)

embed = OllamaEmbeddings(
    model="qwen3-embedding:0.6b",
    base_url=os.environ["OLLAMA_BASE_URL"],
)

tests = [
    "你是早餐店的員工，客人說要一份蛋餅",
    "菜單上有什麼",
]
print("=== LLM Test ===")
for p in tests:
    try:
        r = llm.invoke(p)
        print(f"OK: {repr(r[:80] if r else 'EMPTY')}")
    except Exception as e:
        print(f"ERR: {e}")

print("\n=== Embedding Test ===")
try:
    e = embed.embed_query("你好")
    print(f"Embedding dim: {len(e)}")
except Exception as e:
    print(f"ERR: {e}")