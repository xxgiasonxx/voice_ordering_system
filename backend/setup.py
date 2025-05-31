from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from rag.CRUD_database import create_connection
# from rag.rag_morning_eat import create_prompt_template
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import logging
import redis
import os
load_dotenv()

def init_embedding():
    # 初始化嵌入模型
    try:
        embedding_model = OllamaEmbeddings(model="deepseek-r1:1.5b")
    except Exception as e:
        print(f"嵌入模型載入失敗：{e}")
        raise e
    return embedding_model
# 從 Chroma 載入向量資料庫
def load_menu_to_vectorstore(persist_directory: str = "./chroma_db", name: str = "morning_menu", embedding_model: OllamaEmbeddings = None):
    try:
        vectorstore = Chroma(
            collection_name=name,
            embedding_function=embedding_model,
            persist_directory=persist_directory
        )
        print("向量資料庫載入成功")
        return vectorstore
    except Exception as e:
        print(f"Chroma 資料庫載入失敗：{e}")
        print("請確認 ./chroma_db 存在，或重新跑 load_menu_to_chroma.py 生成資料庫")
        raise e

def create_order_id():
    """生成新的訂單 ID"""
    import random
    tz = timezone(timedelta(hours=8))  # UTC+8 時區
    now = datetime.now(tz)
    return f"ORD{now.strftime('%Y%m%d')}{str(random.randint(1000, 9999))}"

def init_order_state():
    # 建立 UTC+8 時區
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    return {
        "order_id": create_order_id(),  # "ORD202405201234",
        "order_time": now.isoformat(),# "2025-05-20T10:40:00+08:00",
        "table_number": "",
        "customer": {"name": "", "phone": ""},
        "items": [
        ],
        "total_price": 0,
        "payment": {"method": "現金", "status": "unpaid"},
        "order_type": "",
        "status": "start",
    }

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

cus_choice = {"加蛋": 10, "起司": 10, "泡菜": 10, '燒肉': 20, '起司牛奶': 5, '山型丹麥': 10}
embedding_model = init_embedding()
logger.info("embedding model initialized")
vectorstore = load_menu_to_vectorstore(persist_directory=os.getenv('CHROMADB_PATH'), name="morning_menu", embedding_model=embedding_model)
conn = create_connection(db_file=os.getenv('DB_PATH', "./db/database.db"))
logger.info("vectorstore and database connection initialized")
# rag_template, _ = create_prompt_template()
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD', None)
)
redis_client.ping()  # 確認 Redis 連線是否成功
logger.info("redis client initialized")