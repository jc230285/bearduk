import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()
c.execute('SELECT id, title, date, going_count FROM events ORDER BY date DESC')
events = c.fetchall()
print('All events in database:')
for event in events:
    print(f'ID: {event[0]}, Title: {event[1]}, Date: {event[2]}, Going: {event[3]}')
conn.close()