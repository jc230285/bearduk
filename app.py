from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import os
from datetime import datetime, timedelta
import re

app = Flask(__name__)

DATABASE = 'events.db'
FACEBOOK_URL = 'https://www.facebook.com/bearduk/events'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  date TEXT NOT NULL,
                  location TEXT,
                  facebook_url TEXT,
                  is_upcoming BOOLEAN DEFAULT 1,
                  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Add facebook_url column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE events ADD COLUMN facebook_url TEXT')
    except:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

def scrape_facebook_events():
    """Scrape events from Facebook using Selenium with automatic driver management"""
    try:
        # Try selenium scraping with automatic driver management
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        import time
        import re
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        # Use Chrome with timeout protection
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)  # 30 second timeout
        
        driver.get("https://www.facebook.com/bearduk/events")
        time.sleep(10)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        events = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for date patterns - Updated to match Facebook's actual format
            # Matches: "Fri, Nov 28 at 9:00 PM GMT" and "Fri, 28 Nov at 21:00 GMT"
            date_pattern1 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)\s+(GMT|BST)'
            date_pattern2 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(GMT|BST)'
            
            date_match = re.match(date_pattern1, line) or re.match(date_pattern2, line)
            
            if date_match and i + 2 < len(lines):
                event_date = line
                event_title = lines[i + 1] if i + 1 < len(lines) else ""
                event_location = lines[i + 2] if i + 2 < len(lines) else ""
                
                # Check if this looks like a BEARD event
                if 'beard' in event_title.lower() or '@' in event_title:
                    # Create Facebook event URL
                    facebook_url = f"https://www.facebook.com/bearduk/events"
                    
                    events.append({
                        'date': event_date,
                        'title': event_title,
                        'location': event_location,
                        'is_upcoming': True,
                        'facebook_url': facebook_url
                    })
                    
                i += 3
            else:
                i += 1
        
        driver.quit()
        
        # Remove duplicates
        seen = set()
        unique_events = []
        for event in events:
            event_key = (event['date'], event['title'])
            if event_key not in seen:
                seen.add(event_key)
                unique_events.append(event)
        
        return unique_events
        
    except ImportError:
        return []
    except Exception as e:
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return []

def manual_update_events():
    """Manual function to update events with known data"""
    manual_events = [
        {
            'date': 'Fri, 28 Nov at 21:00', 
            'title': 'BEARD @ The Vaults', 
            'location': 'The Vaults, Southsea', 
            'is_upcoming': True,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'Fri, 19 Dec at 20:00', 
            'title': 'BEARD @ Steamtown', 
            'location': 'Steam Town Brew Co, Eastleigh', 
            'is_upcoming': True,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'Sun, 21 Dec at 16:00', 
            'title': 'BEARD @ The Anglers', 
            'location': 'Event by BEARD', 
            'is_upcoming': True,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'Tomorrow at 19:00', 
            'title': 'Private Party', 
            'location': 'Event by BEARD', 
            'is_upcoming': True,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'September 10, 2025', 
            'title': 'BEARD @ Local Pub', 
            'location': 'Southampton', 
            'is_upcoming': False,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'August 25, 2025', 
            'title': 'BEARD @ Brewery Event', 
            'location': 'Portsmouth', 
            'is_upcoming': False,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        }
    ]
    save_events_to_db(manual_events)
    return manual_events

def save_events_to_db(events):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Clear old events
    c.execute("DELETE FROM events WHERE scraped_at < datetime('now', '-30 days')")
    
    for event in events:
        # More comprehensive duplicate check: date + time + title + location
        c.execute('''SELECT id FROM events WHERE date = ? AND title = ? AND location = ?''', 
                  (event['date'], event['title'], event['location']))
        existing = c.fetchone()
        
        if existing:
            # Update existing event with latest data
            c.execute('''UPDATE events SET is_upcoming = ?, scraped_at = CURRENT_TIMESTAMP WHERE id = ?''',
                      (event.get('is_upcoming', True), existing[0]))
        else:
            # Insert new event
            c.execute('''INSERT INTO events (title, date, location, facebook_url, is_upcoming) VALUES (?, ?, ?, ?, ?)''',
                      (event['title'], event['date'], event['location'], event.get('facebook_url', ''), event.get('is_upcoming', True)))
    
    conn.commit()
    conn.close()

def parse_event_date(date_str):
    """Parse Facebook date format and return a datetime object"""
    try:
        # Handle "Tomorrow at X:XX" format
        if "Tomorrow" in date_str:
            tomorrow = datetime.now() + timedelta(days=1)
            time_match = re.search(r'at (\d{1,2}):(\d{2})', date_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)
        
        # Handle "Fri, 28 Nov at 21:00" format
        date_match = re.search(r'(\w{3}),?\s*(\d{1,2})\s*(\w{3})\s*at\s*(\d{1,2}):(\d{2})', date_str)
        if date_match:
            day = int(date_match.group(2))
            month_str = date_match.group(3)
            hour = int(date_match.group(4))
            minute = int(date_match.group(5))
            
            # Map month abbreviations
            months = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = months.get(month_str, 1)
            year = datetime.now().year
            
            # If the date seems to be in the past, assume it's next year
            event_date = datetime(year, month, day, hour, minute)
            if event_date < datetime.now():
                event_date = datetime(year + 1, month, day, hour, minute)
            
            return event_date
        
        # Handle other date formats
        try:
            return datetime.strptime(date_str, "%B %d, %Y")
        except:
            pass
        
        # Default fallback
        return datetime.now() + timedelta(days=30)
    except Exception:
        return datetime.now() + timedelta(days=30)

def load_events_from_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT title, date, location, facebook_url, is_upcoming FROM events")
    rows = c.fetchall()
    conn.close()
    
    events = []
    current_time = datetime.now()
    
    for row in rows:
        event_date = parse_event_date(row[1])
        is_future = event_date > current_time
        
        # Only include future events
        if is_future:
            events.append({
                'title': row[0],
                'date': row[1],
                'location': row[2],
                'facebook_url': row[3] or 'https://www.facebook.com/bearduk/events',
                'is_upcoming': bool(row[4]),
                'datetime_obj': event_date
            })
    
    # Sort by date (earliest first)
    events.sort(key=lambda x: x['datetime_obj'])
    
    return events

def get_events():
    try:
        init_db()
        
        # Check if we need to scrape (every 6 hours)
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM events WHERE scraped_at > datetime('now', '-6 hours')")
        recent_count = c.fetchone()[0]
        conn.close()
        
        if recent_count == 0:
            try:
                scraped_events = scrape_facebook_events()
                if scraped_events:
                    save_events_to_db(scraped_events)
                else:
                    manual_events = manual_update_events()
                    save_events_to_db(manual_events)
            except Exception as scrape_error:
                # If scraping fails, ensure we have some manual events
                manual_events = manual_update_events()
                save_events_to_db(manual_events)
        
        return load_events_from_db()
    except Exception as e:
        # If everything fails, return manual events directly
        return [
            {
                'title': 'BEARD @ The Vaults', 
                'date': 'Fri, 28 Nov at 21:00', 
                'location': 'The Vaults, Southsea',
                'facebook_url': 'https://www.facebook.com/bearduk/events',
                'is_upcoming': True
            },
            {
                'title': 'BEARD @ Steamtown', 
                'date': 'Fri, 19 Dec at 20:00', 
                'location': 'Steam Town Brew Co, Eastleigh',
                'facebook_url': 'https://www.facebook.com/bearduk/events',
                'is_upcoming': True
            }
        ]

@app.route('/')
def home():
    try:
        events = get_events()
        # All events are now already filtered to be upcoming and sorted by date
        upcoming_events = events[:6]  # Show first 6 upcoming events
        
        return render_template('index.html', upcoming_events=upcoming_events, past_events=[])
    except Exception as e:
        # If event loading fails, show site with manual events
        manual_events = [
            {
                'title': 'BEARD @ The Vaults', 
                'date': 'Fri, 28 Nov at 21:00', 
                'location': 'The Vaults, Southsea',
                'facebook_url': 'https://www.facebook.com/bearduk/events'
            },
            {
                'title': 'BEARD @ Steamtown', 
                'date': 'Fri, 19 Dec at 20:00', 
                'location': 'Steam Town Brew Co, Eastleigh',
                'facebook_url': 'https://www.facebook.com/bearduk/events'
            }
        ]
        return render_template('index.html', upcoming_events=manual_events, past_events=[])

@app.route('/update_events')
def update_events():
    """Manual endpoint to trigger event scraping"""
    try:
        events = scrape_facebook_events()
        if not events:
            events = manual_update_events()
        save_events_to_db(events)
        return f"Updated {len(events)} events successfully!"
    except Exception as e:
        return f"Error updating events: {e}"

@app.route('/events_json')
def events_json():
    """Return events as JSON for API access"""
    events = get_events()
    return {'events': events}

@app.route('/test_scraping')
def test_scraping():
    """Test endpoint to show live Facebook scraping output with debugging info"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import time
        import re
        from datetime import datetime
        
        # Initialize response data
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'chrome_setup': 'initializing',
            'page_load': 'pending',
            'raw_text_sample': '',
            'found_lines': 0,
            'detected_events': [],
            'errors': []
        }
        
        try:
            # Setup Chrome with debugging info
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.binary_location = "/usr/bin/google-chrome"
            
            driver = webdriver.Chrome(options=chrome_options)
            response_data['chrome_setup'] = 'success'
            
            # Load Facebook page
            driver.get("https://www.facebook.com/bearduk/events")
            response_data['page_load'] = 'loaded'
            
            time.sleep(10)
            
            # Get page text
            page_text = driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            response_data['found_lines'] = len(lines)
            response_data['raw_text_sample'] = '\n'.join(lines[:50])  # First 50 lines as sample
            
            # Process for events
            events = []
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Look for date patterns - Updated to match Facebook's actual format
                date_pattern1 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)\s+(GMT|BST)'
                date_pattern2 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(GMT|BST)'
                
                date_match = re.match(date_pattern1, line) or re.match(date_pattern2, line)
                
                if date_match and i + 2 < len(lines):
                    event_date = line
                    event_title = lines[i + 1] if i + 1 < len(lines) else ""
                    event_location = lines[i + 2] if i + 2 < len(lines) else ""
                    
                    # Check if this looks like a BEARD event
                    if 'beard' in event_title.lower() or '@' in event_title:
                        facebook_url = f"https://www.facebook.com/bearduk/events"
                        
                        events.append({
                            'date': event_date,
                            'title': event_title,
                            'location': event_location,
                            'is_upcoming': True,
                            'facebook_url': facebook_url,
                            'line_number': i
                        })
                        
                    i += 3
                else:
                    i += 1
            
            driver.quit()
            
            response_data['detected_events'] = events
            response_data['status'] = 'completed'
            response_data['events_found'] = len(events)
            
        except Exception as selenium_error:
            response_data['errors'].append(f"Selenium error: {str(selenium_error)}")
            response_data['status'] = 'selenium_failed'
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
        
        return response_data
        
    except ImportError as import_error:
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'import_error',
            'error': f"Missing dependencies: {str(import_error)}",
            'available_modules': ['selenium' in str(import_error)]
        }
    except Exception as general_error:
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'general_error',
            'error': str(general_error)
        }

@app.route('/debug_status')
def debug_status():
    """Debug endpoint showing system status and database contents"""
    try:
        from datetime import datetime
        import os
        
        # Check database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Get recent scraping info
        c.execute("SELECT COUNT(*) FROM events WHERE scraped_at > datetime('now', '-6 hours')")
        recent_scrapes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM events")
        total_events = c.fetchone()[0]
        
        # Get all events with details
        c.execute("SELECT title, date, location, facebook_url, is_upcoming, scraped_at FROM events ORDER BY scraped_at DESC LIMIT 10")
        recent_events = [
            {
                'title': row[0],
                'date': row[1], 
                'location': row[2],
                'facebook_url': row[3],
                'is_upcoming': row[4],
                'scraped_at': row[5]
            } for row in c.fetchall()
        ]
        
        conn.close()
        
        # System info
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_events': total_events,
                'recent_scrapes_6h': recent_scrapes,
                'database_file_exists': os.path.exists(DATABASE),
                'recent_events': recent_events
            },
            'system': {
                'chrome_binary_exists': os.path.exists('/usr/bin/google-chrome'),
                'environment': os.environ.get('FLASK_ENV', 'not_set'),
                'port': os.environ.get('PORT', 'not_set')
            },
            'facebook_url': FACEBOOK_URL,
            'scraping_interval': '6 hours'
        }
        
        return status_data
        
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'status': 'error'
        }

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'BEARD website is running'
    }

if __name__ == '__main__':
    # Production-ready configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)