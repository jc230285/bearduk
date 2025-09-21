from app import parse_event_date, load_events_from_db
from datetime import datetime

# Test date parsing
test_dates = [
    'Tomorrow at 19:00',
    'Sun, 21 Dec at 16:00',
    'September 10, 2025',
    'Fri, 28 Nov at 21:00',
    'Fri, 19 Dec at 20:00'
]

print('Date parsing results:')
for date_str in test_dates:
    parsed = parse_event_date(date_str)
    print(f'{date_str} -> {parsed}')

print(f'\nCurrent time: {datetime.now()}')

# Test loading events
events = load_events_from_db()
print(f'\nLoaded events: {len(events)}')
for event in events:
    print(f'  {event["title"]}: {event["date"]} -> {event["datetime_obj"]}')