import urllib.request
import json

url = "http://ollama:11434/api/generate"

prompts = [
    "一加一等於多少",
    "你是早餐店員，客人要一份蛋餅，給他一句回應",
]

for prompt in prompts:
    data = {
        "model": "qwen3.5:0.8b",
        "prompt": prompt,
        "options": {"num_predict": 8192},
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"Prompt: {prompt}")
            print(f"Response: {repr(result.get('response', '')[:200])}")
            print(f"Done: {result.get('done')}, Eval count: {result.get('eval_count')}")
            print()
    except Exception as e:
        print(f"Error for '{prompt}': {e}")
        print()