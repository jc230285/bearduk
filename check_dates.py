import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT title, date FROM events')
rows = c.fetchall()
print('Current event dates:')
for row in rows:
    print(f'{row[0]}: {row[1]}')
conn.close()