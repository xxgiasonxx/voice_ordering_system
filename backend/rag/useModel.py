import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
load_dotenv()

def useModel(model):
    if model == "gemini_api":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=1.0,
            max_tokens=None,
            timeout=10,
            max_retries=2,
        )
        return llm
    if model == "qwen3:4b":
        llm = OllamaLLM(model="gemma3:4b", temperature=0.7, top_k=30, top_p=0.9)
        return llm
    # 其他名稱一律視為 Ollama 模型，例如 qwen3:1.7b、qwen3:0.6b
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    llm = OllamaLLM(
            model=model,
            base_url=base_url,
            num_ctx=8192,  # prompt 約 6k tokens，Ollama 預設 4096 會截斷掉格式說明
            num_predict=300,  # 小模型偶爾會無限重複輸出，限制長度避免卡住
            reasoning=False,  # 關閉 Qwen3 思考模式，否則每次回應多等好幾秒
            temperature=0.1,  # 點餐要穩定一致，不需要創意
            )
    return llm
    
        
