#!/usr/bin/env python3
"""
Test the updated Flask app with selenium scraping
"""

from app import get_events

def test_updated_app():
    print("🧪 Testing updated Flask app with Selenium scraping...")
    
    events = get_events()
    print(f"📊 Found {len(events)} total events")
    
    if events:
        print("\n🎉 Events found:")
        for i, event in enumerate(events[:10]):
            print(f"  {i+1}. {event['title']} on {event['date']} at {event['location']}")
    else:
        print("❌ No events found")
    
    return events

if __name__ == "__main__":
    test_updated_app()