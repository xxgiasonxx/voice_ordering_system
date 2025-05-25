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
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=10,
            max_retries=2,
        )
        return llm
    if model == "qwen3:4b":
        from langchain_community.llms import Qwen
        llm = OllamaLLM(model="gemma3:4b", temperature=0.7, top_k=30, top_p=0.9)
        return llm
    
        