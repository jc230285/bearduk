from app import get_events

events = get_events()
print(f'Loaded {len(events)} events:')
for i, event in enumerate(events[:3]):
    print(f'- {event["title"]} on {event["date"]}')