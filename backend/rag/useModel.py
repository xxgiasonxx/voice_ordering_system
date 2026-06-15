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
        from langchain_community.llms import Qwen
        llm = OllamaLLM(model="gemma3:4b", temperature=0.7, top_k=30, top_p=0.9)
        return llm
    if model == "qwen2.5:1.5b":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        llm = OllamaLLM(
                model="qwen2.5:1.5b",
                base_url=base_url,
                )
        return llm
    
        
