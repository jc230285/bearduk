#!/usr/bin/env python3
"""
Test what data is being passed to the template
"""

from app import get_events

def test_template_data():
    print("🔍 Testing template data...")
    
    events = get_events()
    print(f"Total events from get_events(): {len(events)}")
    
    upcoming_events = [e for e in events if e.get('is_upcoming', True)][:6]
    past_events = [e for e in events if not e.get('is_upcoming', False)][:2]
    
    print(f"\n📅 UPCOMING EVENTS ({len(upcoming_events)}):")
    for i, event in enumerate(upcoming_events):
        print(f"  {i+1}. {event['title']} on {event['date']} at {event['location']}")
    
    print(f"\n📜 PAST EVENTS ({len(past_events)}):")
    for i, event in enumerate(past_events):
        print(f"  {i+1}. {event['title']} on {event['date']} at {event['location']}")
    
    # If not enough past events, add some dummy ones
    if len(past_events) < 2:
        dummy_past = [
            {'date': 'September 10, 2025', 'title': 'BEARD @ Local Pub', 'location': 'Southampton'},
            {'date': 'August 25, 2025', 'title': 'BEARD @ Brewery Event', 'location': 'Portsmouth'}
        ]
        past_events.extend(dummy_past[:2 - len(past_events)])
        
        print(f"\n📜 PAST EVENTS WITH DUMMIES ({len(past_events)}):")
        for i, event in enumerate(past_events):
            print(f"  {i+1}. {event['title']} on {event['date']} at {event['location']}")

if __name__ == "__main__":
    test_template_data()