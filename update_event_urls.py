#!/usr/bin/env python3
"""
Script to update Facebook event URLs to point to individual events instead of the generic events page
"""
import sqlite3

def update_event_urls():
    """Update Facebook URLs to point to individual event pages"""
    conn = sqlite3.connect('events.db')
    c = conn.cursor()

    # Known individual event URLs - update these as we find them
    url_updates = {
        'BEARD @ The Vaults': 'https://www.facebook.com/events/1365306694514142/',
        'BEARD @ Steamtown': 'https://www.facebook.com/events/1276300143600709/',
        'BEARD @ The Anglers': 'https://www.facebook.com/events/955296663193145/',
        # Add more URLs as they become available
        # 'Private Party': 'https://www.facebook.com/events/XXXXXXX/',
        # 'BEARD @ Local Pub': 'https://www.facebook.com/events/XXXXXXX/',
    }

    updated_count = 0
    for title, new_url in url_updates.items():
        c.execute('UPDATE events SET facebook_url = ? WHERE title = ?', (new_url, title))
        if c.rowcount > 0:
            updated_count += 1
            print(f"Updated {title}: {new_url}")

    conn.commit()
    conn.close()

    print(f"Updated {updated_count} event URLs")

if __name__ == '__main__':
    update_event_urls()