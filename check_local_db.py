import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM events')
print('Local event count:', c.fetchone()[0])

c.execute('SELECT title, date FROM events LIMIT 3')
print('Sample events:')
for row in c.fetchall():
    print(row)

conn.close()