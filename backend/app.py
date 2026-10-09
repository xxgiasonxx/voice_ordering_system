import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from blueprint.order import order
from blueprint.asr_stream import audioSSE
from blueprint.token import token
from blueprint.payment import payment
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:80", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(order, prefix="/order")
app.include_router(token)
app.include_router(audioSSE)
app.include_router(payment)


@app.on_event("startup")
async def init_database():
    """Postgres 沒有菜單資料時（第一次啟動或 volume 被清空）自動執行遷移，不用每次手動"""
    if not os.getenv("DB_URL"):
        return
    import logging
    import runpy
    from rag.CRUD_database import create_connection
    logger = logging.getLogger(__name__)
    conn = create_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM main_menu")
        if cur.fetchone()["count"] > 0:
            return
    except Exception:
        pass  # 資料表不存在
    finally:
        conn.close()
    logger.info("Menu tables missing, running debug_and_migrate.py ...")
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_and_migrate.py"), run_name="__main__")
    logger.info("Database initialized")

@app.on_event("startup")
async def preload_models():
    from blueprint.asr_stream import get_asr_model
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Preloading ASR model...")
    get_asr_model()
    logger.info("ASR model preloaded")

@app.get('/menu')
async def get_menu():
    """Return all menu items from PostgreSQL."""
    from rag.CRUD_database import create_connection
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, class, name, price, add_egg, cheese, kimchi, roast, cheese_milk, danish, combo, vegetarian, recommended FROM main_menu ORDER BY id")
    main_items = list(cur.fetchall())

    cur.execute("SELECT id, name, price, description FROM combo_menu ORDER BY id")
    combo_items = list(cur.fetchall())

    cur.execute('SELECT id, class, name, "M", "L" FROM drink_item ORDER BY id')
    drink_items = list(cur.fetchall())

    conn.close()
    return {"main": main_items, "combos": combo_items, "drinks": drink_items}
