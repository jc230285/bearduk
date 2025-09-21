import sqlite3

conn = sqlite3.connect('events.db')
c = conn.cursor()

# Check schema
print('Events table schema:')
c.execute('PRAGMA table_info(events)')
for row in c.fetchall():
    print(row)

# Check total count
c.execute('SELECT COUNT(*) FROM events')
total = c.fetchone()[0]
print(f'\nTotal events: {total}')

# Check sample data
print('\nSample events:')
c.execute('SELECT * FROM events LIMIT 3')
for row in c.fetchall():
    print(row)

conn.close()