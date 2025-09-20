#!/usr/bin/env python3
"""
Clear database and refresh events to eliminate duplicates
"""

import sqlite3
import os
from app import manual_update_events, init_db

def clear_and_refresh():
    print("🗑️ Clearing database and refreshing events...")
    
    # Remove the database file
    if os.path.exists('events.db'):
        os.remove('events.db')
        print("✅ Removed old database")
    
    # Initialize fresh database
    init_db()
    print("✅ Created fresh database")
    
    # Add manual events
    events = manual_update_events()
    print(f"✅ Added {len(events)} fresh events")
    
    print("\n🎉 Database refreshed! All duplicates removed.")

if __name__ == "__main__":
    clear_and_refresh()