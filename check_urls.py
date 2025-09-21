import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT title, facebook_url FROM events')
rows = c.fetchall()
print('Current event URLs:')
for row in rows:
    print(f'{row[0]}: {row[1]}')
conn.close()