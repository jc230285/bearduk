#!/usr/bin/env python3
"""
Manual event update script for BEARD band website
Run this to manually refresh events from Facebook or update with custom data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import manual_update_events

if __name__ == "__main__":
    print("Updating events...")
    events = manual_update_events()
    print(f"Successfully updated {len(events)} events!")
    for event in events:
        print(f"- {event['title']} on {event['date']} at {event['location']}")