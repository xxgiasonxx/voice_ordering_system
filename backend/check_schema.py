import sqlite3
conn = sqlite3.connect("/app/backend/db/morning_eat.db")
c = conn.cursor()
for t in ["main_menu", "drink_item", "combo_menu"]:
    c.execute(f"PRAGMA table_info({t})")
    print(t, [r[1] for r in c.fetchall()])
conn.close()