import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@postgres:5432/morning_eat')
cur = conn.cursor()
cur.execute('SELECT id, class, name FROM main_menu LIMIT 5')
for row in cur.fetchall():
    print(row)
cur.execute('SELECT COUNT(*) FROM main_menu WHERE class = %s', ('id',))
print('Rows with class=id:', cur.fetchone()[0])
conn.close()