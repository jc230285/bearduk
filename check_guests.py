import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT title, going_count, interested_count, friends_going FROM events')
rows = c.fetchall()
print('Current database values:')
for row in rows:
    print(f'{row[0]}: going={row[1]}, interested={row[2]}, friends={row[3]}')
conn.close()