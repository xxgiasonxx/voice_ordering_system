import sqlite3
conn = sqlite3.connect('/app/backend/db/morning_eat.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM main_menu')
print('main_menu rows:', c.fetchone()[0])
c.execute('SELECT COUNT(*) FROM drink_item')
print('drink_item rows:', c.fetchone()[0])
conn.close()