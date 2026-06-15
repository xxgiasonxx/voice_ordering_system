import os
os.environ["OLLAMA_BASE_URL"] = "http://ollama:11434"
from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="qwen3.5:0.8b",
    base_url=os.environ["OLLAMA_BASE_URL"],
    temperature=0.7,
    num_predict=2048,
    num_ctx=8192,
    reasoning=False
)

tests = [
    "你好",
    "1+1=?",
    "早安",
    "請用中文說你好",
]
for t in tests:
    try:
        r = llm.invoke(t)
        print(f"Prompt[{len(t)}]: {repr(t)} -> {repr(r)}")
    except Exception as e:
        print(f"Prompt[{len(t)}]: {repr(t)} -> ERROR: {e}")
