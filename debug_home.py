from app import get_events, add_date_badges

print("Testing event loading...")

# Get events
events = get_events()
print(f"get_events() returned {len(events)} events")

# Add date badges
events_with_badges = add_date_badges(events)
print(f"add_date_badges() returned {len(events_with_badges)} events")

# Set upcoming events
upcoming_events = events_with_badges[:6]
print(f"upcoming_events has {len(upcoming_events)} events")

# Print details of events
for i, event in enumerate(upcoming_events):
    print(f"Event {i+1}: {event['title']} - {event['date']} - datetime_obj: {event.get('datetime_obj')}")