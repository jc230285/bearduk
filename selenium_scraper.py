#!/usr/bin/env python3
"""
Working selenium-based Facebook event scraper for BEARD
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
from datetime import datetime

def scrape_facebook_events_selenium():
    """Scrape BEARD events using selenium"""
    events = []
    
    try:
        print("🚗 Setting up Chrome driver for scraping...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🌐 Loading Facebook events page...")
        driver.get("https://www.facebook.com/bearduk/events")
        
        # Wait for page to load
        time.sleep(8)
        
        # Get all text from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        print(f"📄 Found {len(lines)} lines of text")
        
        # Parse events from the lines
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for date patterns like "Fri, 28 Nov at 21:00 GMT"
            date_pattern = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(GMT|BST)'
            date_match = re.match(date_pattern, line)
            
            if date_match and i + 2 < len(lines):
                event_date = line
                event_title = lines[i + 1] if i + 1 < len(lines) else ""
                event_location = lines[i + 2] if i + 2 < len(lines) else ""
                
                # Check if this looks like a BEARD event
                if 'beard' in event_title.lower() or '@' in event_title:
                    event = {
                        'date': event_date,
                        'title': event_title,
                        'location': event_location,
                        'is_upcoming': True
                    }
                    events.append(event)
                    print(f"✅ Found event: {event_title} on {event_date}")
                    
                i += 3  # Skip the lines we just processed
            else:
                i += 1
        
        driver.quit()
        print(f"🎉 Successfully scraped {len(events)} events!")
        
        return events
        
    except Exception as e:
        print(f"❌ Selenium scraping error: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def update_app_with_selenium():
    """Update the main app to use selenium scraping"""
    events = scrape_facebook_events_selenium()
    
    if events:
        # Save to database (reuse existing function)
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import save_events_to_db
        save_events_to_db(events)
        
        print(f"💾 Saved {len(events)} events to database!")
        
        for event in events:
            print(f"- {event['title']} on {event['date']} at {event['location']}")
            
        return events
    else:
        print("❌ No events found with selenium")
        return []

if __name__ == "__main__":
    print("🔥 Testing Selenium Facebook Scraping")
    print("=" * 50)
    
    events = update_app_with_selenium()
    
    if events:
        print("\n🎯 SUCCESS! Selenium scraping works!")
        print("You can now integrate this into your Flask app.")
    else:
        print("\n❌ Selenium scraping failed or found no events")
        print("Consider sticking with manual event updates.")