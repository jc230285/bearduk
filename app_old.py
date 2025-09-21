from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime, timedelta
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')
FACEBOOK_URL = 'https://www.facebook.com/bearduk/events'

# Initialize background scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def get_db_connection():
    """Get a database connection"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create events table
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        location TEXT,
        facebook_url TEXT,
        is_upcoming BOOLEAN DEFAULT true,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        going_count INTEGER DEFAULT 0,
        interested_count INTEGER DEFAULT 0,
        friends_going TEXT DEFAULT ''
    )''')

    # Create social media followers table
    c.execute('''CREATE TABLE IF NOT EXISTS social_media_followers (
        id SERIAL PRIMARY KEY,
        platform TEXT NOT NULL,
        username TEXT NOT NULL,
        follower_count INTEGER NOT NULL,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create indexes for better performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_upcoming ON events(is_upcoming, date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_events_scraped_at ON events(scraped_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_social_followers_platform ON social_media_followers(platform, username)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_social_followers_scraped_at ON social_media_followers(scraped_at)')

    conn.commit()
    conn.close()

def setup_background_tasks():
    """Set up background tasks for event and follower checking"""
    # Run initial checks on startup
    print("Running startup checks...")
    check_events_background()
    check_followers_background()

    # Schedule event checking - run daily at 2 AM
    scheduler.add_job(
        func=check_events_background,
        trigger=CronTrigger(hour=2),  # Daily at 2 AM
        id='daily_event_check',
        name='Daily Event Check',
        replace_existing=True
    )

    # Schedule follower checking - run daily at 3 AM
    scheduler.add_job(
        func=check_followers_background,
        trigger=CronTrigger(hour=3),  # Daily at 3 AM
        id='daily_follower_check',
        name='Daily Follower Check',
        replace_existing=True
    )

    print("Background tasks scheduled")

def check_events_background():
    """Background task to check for new events"""
    try:
        print("Running background event check...")
        events = scrape_facebook_events()
        if events:
            save_events_to_db(events)
            print(f"Background event check completed: {len(events)} events updated")
        else:
            print("Background event check: No events found")
    except Exception as e:
        print(f"Background event check failed: {e}")

def check_followers_background():
    """Background task to update follower counts"""
    try:
        print("Running background follower check...")
        from update_followers import update_all_followers
        update_all_followers()
        print("Background follower check completed")
    except Exception as e:
        print(f"Background follower check failed: {e}")

def scrape_facebook_events():
    """Scrape events from Facebook using Selenium as primary method, requests as fallback"""
    try:
        # Try Selenium first (more reliable for Facebook)
        return scrape_facebook_events_selenium()
    except Exception as e:
        print(f"Selenium scraping failed: {e}")
        try:
            # Fallback to requests if Selenium fails
            return scrape_facebook_events_requests()
        except Exception as e2:
            print(f"Requests scraping also failed: {e2}")
            return []

def scrape_facebook_events_requests():
    """Scrape Facebook events using requests with proper headers"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        from datetime import datetime
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        response = requests.get(FACEBOOK_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for event data in various formats
        events = []
        
        # Try to find events in the page content
        page_text = soup.get_text()
        
        # Look for event patterns in the text
        lines = page_text.split('\n')
        current_event = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for event titles (usually contain "BEARD @")
            if 'BEARD @' in line and len(line) < 100:
                if current_event:
                    events.append(current_event)
                current_event = {'title': line, 'facebook_url': FACEBOOK_URL}
            
            # Look for dates
            elif current_event and not current_event.get('date'):
                # Multiple date patterns
                date_patterns = [
                    r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+\d{1,2}:\d{2}',
                    r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
                    r'Tomorrow at \d{1,2}:\d{2}',
                    r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
                    r'\b\d{4}-\d{2}-\d{2}',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        current_event['date'] = match.group()
                        break
            
            # Look for locations
            elif current_event and not current_event.get('location'):
                # Common location patterns
                if any(loc in line.lower() for loc in ['southsea', 'eastleigh', 'portsmouth', 'brew', 'pub', 'bar', 'venue']):
                    if len(line) < 100:  # Reasonable location length
                        current_event['location'] = line
        
        # Add the last event if it exists
        if current_event:
            events.append(current_event)
        
        # Filter out incomplete events
        complete_events = []
        for event in events:
            if event.get('title') and event.get('date'):
                complete_events.append(event)
        
        return complete_events
        
    except Exception as e:
        print(f"Requests scraping error: {e}")
        raise

def scrape_facebook_events_selenium():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        import re
        from datetime import datetime

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        
        # Additional Docker-specific options
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--disable-setuid-sandbox")

        # Set Chrome binary location based on environment
        import platform
        if platform.system() == "Windows":
            chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        else:
            chrome_options.binary_location = "/usr/bin/google-chrome"

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)

        driver.get("https://www.facebook.com/bearduk/events")
        time.sleep(15)  # Increased wait time

        # Wait for events to load and try to load more content
        try:
            # Wait for page to be ready
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content
            time.sleep(10)

            # Try to scroll down multiple times to load more events
            for i in range(5):  # Increased from 3 to 5
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased wait time

                # Try to click "See more" buttons if they exist
                try:
                    see_more_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'See more')]/parent::*")
                    for button in see_more_buttons:
                        try:
                            button.click()
                            time.sleep(2)
                        except:
                            pass
                except:
                    pass

                # Also try other load more patterns
                try:
                    load_more_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'Load more')]/parent::*")
                    for button in load_more_buttons:
                        try:
                            button.click()
                            time.sleep(2)
                        except:
                            pass
                except:
                    pass

            with open('/app/debug.log', 'a') as f:
                f.write("Finished extended scrolling and loading more content\n")

        except Exception as e:
            with open('/app/debug.log', 'a') as f:
                f.write(f"Error during extended page loading: {e}\n")

        events = []

        # Method 1: Try to find event containers using CSS selectors
        try:
            print("Starting Method 1: Individual page scraping")
            with open('/app/debug.log', 'a') as f:
                f.write("Starting Method 1: Individual page scraping\n")

            # First, collect all event URLs from the page
            event_urls = []
            event_containers = driver.find_elements(By.CSS_SELECTOR, "[role='link'][href*='/events/']")

            with open('/app/debug.log', 'a') as f:
                f.write(f"Found {len(event_containers)} event containers\n")

            for container in event_containers[:20]:  # Check more containers
                try:
                    href = container.get_attribute('href')
                    if href and '/events/' in href and 'bearduk' not in href:
                        event_id_match = re.search(r'/events/(\d+)', href)
                        if event_id_match and href not in event_urls:
                            event_urls.append(href)
                except Exception as e:
                    continue

            with open('/app/debug.log', 'a') as f:
                f.write(f"Found {len(event_urls)} unique event URLs: {event_urls[:5]}...\n")

            # Now visit each event URL to get complete details
            for url in event_urls[:10]:  # Limit to 10 events to avoid timeout
                try:
                    with open('/app/debug.log', 'a') as f:
                        f.write(f"Visiting event URL: {url}\n")

                    # Open event in new tab
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get(url)
                    time.sleep(3)  # Wait for event page to load

                    # Extract event details from the individual event page
                    try:
                        # Wait for the event page to load
                        time.sleep(3)

                        # Try multiple selectors for event title
                        title_selectors = [
                            "h1[data-testid='event-permalink-event-name']",
                            "h1",
                            "[role='main'] h1",
                            "[data-testid='event-title']",
                            ".event-title",
                            "[role='main'] [dir='auto']",
                            "span[dir='auto']",
                            "title"
                        ]

                        event_title = ""
                        for selector in title_selectors:
                            try:
                                title_element = driver.find_element(By.CSS_SELECTOR, selector)
                                title_text = title_element.text.strip()
                                if title_text and len(title_text) > 3 and title_text != "Events":
                                    event_title = title_text
                                    break
                            except:
                                continue

                        # Try multiple selectors for event date/time
                        date_selectors = [
                            "[data-testid='event-permalink-event-time']",
                            "[role='main'] time",
                            "time",
                            ".event-time",
                            "[data-testid*='time']"
                        ]

                        event_date = ""
                        for selector in date_selectors:
                            try:
                                date_element = driver.find_element(By.CSS_SELECTOR, selector)
                                date_text = date_element.text.strip()
                                if date_text and len(date_text) > 3:
                                    event_date = date_text
                                    break
                            except:
                                continue

                        # Try multiple selectors for event location
                        location_selectors = [
                            "[data-testid='event-permalink-event-location']",
                            "[role='main'] [data-testid*='location']",
                            ".event-location",
                            "[data-testid*='location']"
                        ]

                        event_location = ""
                        for selector in location_selectors:
                            try:
                                location_element = driver.find_element(By.CSS_SELECTOR, selector)
                                location_text = location_element.text.strip()
                                if location_text and len(location_text) > 3:
                                    event_location = location_text
                                    break
                            except:
                                continue

                        # If we still don't have good data, try parsing the page title
                        if not event_title or event_title == "Events":
                            try:
                                page_title = driver.title
                                if page_title and "Events" not in page_title:
                                    event_title = page_title.split(" | ")[0].strip()
                            except:
                                pass

                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Extracted from {url}: title='{event_title}', date='{event_date}', location='{event_location}'\n")

                        # Only add if we have at least a title
                        if event_title and ('beard' in event_title.lower() or '@' in event_title or 'BEARD' in event_title):
                            event_id_match = re.search(r'/events/(\d+)', url)
                            event_id = event_id_match.group(1) if event_id_match else ""

                            # Check for duplicates
                            is_duplicate = False
                            for existing_event in events:
                                if existing_event['title'] == event_title:
                                    is_duplicate = True
                                    break

                            if not is_duplicate:
                                events.append({
                                    'date': event_date or "Date TBD",
                                    'title': event_title,
                                    'location': event_location or "Location TBD",
                                    'is_upcoming': True,
                                    'facebook_url': url,
                                    'event_id': event_id,
                                    'source': 'individual_page'
                                })
                                with open('/app/debug.log', 'a') as f:
                                    f.write(f"Added event from individual page: {event_title}\n")

                    except Exception as e:
                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Error extracting from {url}: {e}\n")

                    # Close the tab and switch back
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    with open('/app/debug.log', 'a') as f:
                        f.write(f"Error visiting {url}: {e}\n")
                    # Make sure we're back on the main tab
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            with open('/app/debug.log', 'a') as f:
                f.write(f"Individual page method failed: {e}\n")

        # Method 2: Fallback to the original line-by-line parsing if needed
        if len(events) < 3:
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]

                i = 0
                while i < len(lines) and len(events) < 6:
                    line = lines[i]

                    # Look for date patterns - Updated to match Facebook's actual format
                    date_pattern1 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)\s+(GMT|BST)'
                    date_pattern2 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(GMT|BST)'
                    date_pattern3 = r'(Today|Tomorrow)\s+at\s+(\d{1,2}:\d{2})'
                    date_pattern4 = r'Sun,\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})'

                    date_match = (re.match(date_pattern1, line) or re.match(date_pattern2, line) or
                                re.match(date_pattern3, line) or re.match(date_pattern4, line))

                    if date_match and i + 2 < len(lines):
                        event_date = line
                        event_title = lines[i + 1] if i + 1 < len(lines) else ""
                        event_location = lines[i + 2] if i + 2 < len(lines) else ""

                        # Check if this looks like a BEARD event
                        if ('beard' in event_title.lower() or '@' in event_title or 'BEARD' in event_title):
                            # Check if we already have this event
                            is_duplicate = False
                            for existing_event in events:
                                if (existing_event['title'] == event_title and
                                    existing_event['date'] == event_date):
                                    is_duplicate = True
                                    break

                            if not is_duplicate:
                                events.append({
                                    'date': event_date,
                                    'title': event_title,
                                    'location': event_location,
                                    'is_upcoming': True,
                                    'facebook_url': 'https://www.facebook.com/bearduk/events'
                                })

                        i += 3
                    else:
                        i += 1

            except Exception as e:
                print(f"Fallback parsing failed: {e}")

        driver.quit()

        # Remove duplicates based on title and date
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
        print(f"Scraping error: {e}")
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return []

def add_date_badges(events):
    """Add date badges to events based on how soon they are"""
    from datetime import datetime, timedelta
    
    current_time = datetime.now()
    today = current_time.date()
    
    for event in events:
        try:
            # Parse the event date
            if 'datetime_obj' in event:
                event_datetime = event['datetime_obj']
                event_date = event_datetime.date()
            else:
                # Try to parse from date string
                event_datetime = parse_event_date(event['date'])
                if event_datetime:
                    event_date = event_datetime.date()
                else:
                    continue
            
            days_diff = (event_date - today).days
            
            if days_diff == 0:
                event['date_badge'] = 'Today'
                event['badge_class'] = 'today'
            elif days_diff == 1:
                event['date_badge'] = 'Tomorrow'
                event['badge_class'] = 'tomorrow'
            elif 2 <= days_diff <= 7:
                event['date_badge'] = f'In {days_diff} days'
                event['badge_class'] = 'soon'
            elif 8 <= days_diff <= 30:
                weeks = days_diff // 7
                event['date_badge'] = f'In {weeks} week{"s" if weeks > 1 else ""}'
                event['badge_class'] = 'upcoming'
            elif 31 <= days_diff <= 60:
                event['date_badge'] = 'In about a month'
                event['badge_class'] = 'upcoming'
            elif days_diff > 60:
                months = days_diff // 30
                event['date_badge'] = f'In {months} month{"s" if months > 1 else ""}'
                event['badge_class'] = 'upcoming'
            else:
                # Past events
                event['date_badge'] = None
                event['badge_class'] = None
            
            # Add full date format like "Friday 28 November 2025 from 21:00-23:00"
            if event_datetime:
                day_name = event_datetime.strftime('%A')  # Full day name
                day = event_datetime.day
                month_name = event_datetime.strftime('%B')  # Full month name
                year = event_datetime.year
                start_time = event_datetime.strftime('%H:%M')
                
                # Assume 2-hour duration for end time (can be adjusted)
                end_datetime = event_datetime + timedelta(hours=2)
                end_time = end_datetime.strftime('%H:%M')
                
                event['full_date'] = f'{day_name} {day} {month_name} {year} from {start_time}-{end_time}'
            else:
                event['full_date'] = event['date']  # Fallback to original date
                
        except Exception as e:
            # If date parsing fails, don't add badge
            event['date_badge'] = None
            event['badge_class'] = None
            event['full_date'] = event.get('date', 'Date TBA')
    
    return events

def add_manual_events():
    """Add the missing events that aren't on Facebook"""
    manual_events = [
        {
            'title': 'BEARD @ The Vaults',
            'date': 'Fri, 28 Nov at 21:00 GMT',
            'location': 'The Vaults, Southsea',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        },
        {
            'title': 'BEARD @ Steamtown',
            'date': 'Fri, 19 Dec at 20:00 GMT',
            'location': 'Steam Town Brew Co, Eastleigh',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        },
        {
            'title': 'Private Party',
            'date': 'Sat, 20 Sep at 19:00 BST',
            'location': 'Event by BEARD',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        },
        {
            'title': 'BEARD @ The Anglers',
            'date': 'Sun, 21 Dec at 16:00 GMT',
            'location': 'Event by BEARD',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        },
        {
            'title': 'BEARD @ Local Pub',
            'date': 'October 15, 2025',
            'location': 'Local Pub, Hampshire',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        },
        {
            'title': 'BEARD @ Brewery Event', 
            'date': 'November 5, 2025',
            'location': 'Brewery, Hampshire',
            'facebook_url': 'https://www.facebook.com/events/1135497524746252/'
        }
    ]
    
    try:
        save_events_to_db(manual_events)
        return f"Added {len(manual_events)} manual events"
    except Exception as e:
        return f"Error adding manual events: {e}"
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
            'date': 'October 15, 2025', 
            'title': 'BEARD @ Local Pub', 
            'location': 'Southampton', 
            'is_upcoming': False,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        },
        {
            'date': 'November 5, 2025', 
            'title': 'BEARD @ Brewery Event', 
            'location': 'Portsmouth', 
            'is_upcoming': False,
            'facebook_url': 'https://www.facebook.com/bearduk/events'
        }
    ]
    save_events_to_db(manual_events)
    return manual_events

def save_events_to_db(events):
    conn = get_db_connection()
    c = conn.cursor()

    # Clear old events (PostgreSQL syntax)
    c.execute("DELETE FROM events WHERE scraped_at < NOW() - INTERVAL '30 days'")

    for event in events:
        # Normalize the date for duplicate checking
        normalized_date = normalize_date_for_comparison(event['date'])

        # Find existing events with similar normalized dates, titles, and locations
        c.execute('''SELECT id, date FROM events WHERE title = ? AND location = ?''',
                  (event['title'], event['location']))
        existing_events = c.fetchall()

        found_duplicate = False
        for existing_id, existing_date in existing_events:
            existing_normalized = normalize_date_for_comparison(existing_date)
            if existing_normalized == normalized_date:
                # Update existing event with latest data (keep the better formatted date)
                c.execute('''UPDATE events SET date = %s, is_upcoming = %s, scraped_at = CURRENT_TIMESTAMP WHERE id = %s''',
                          (event['date'], event.get('is_upcoming', True), existing_id))
                found_duplicate = True
                break

        if not found_duplicate:
            # Insert new event
            c.execute('''INSERT INTO events (title, date, location, facebook_url, is_upcoming) VALUES (%s, %s, %s, %s, %s)''',
                      (event['title'], event['date'], event['location'], event.get('facebook_url', ''), event.get('is_upcoming', True)))

    conn.commit()
    conn.close()

def normalize_date_for_comparison(date_str):
    """Normalize date strings for duplicate comparison by extracting day, month, year, hour, minute"""
    try:
        # Handle "Fri, 28 Nov at 21:00" format
        date_match = re.search(r'(\d{1,2})\s*(\w{3})\s*at\s*(\d{1,2}):(\d{2})', date_str)
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2)
            hour = int(date_match.group(3))
            minute = int(date_match.group(4))

            # Map month abbreviations
            months = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }

            month = months.get(month_str, 1)
            year = datetime.now().year

            # If the date seems to be in the past, assume it's next year
            event_date = datetime(year, month, day, hour, minute)
            if event_date < datetime.now() - timedelta(days=90):  # More than 3 months ago
                year += 1

            return f"{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}"

        # Handle "Friday 28 November 2025 from 21:00-23:00" format
        date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str)
        if date_match:
            day = int(date_match.group(1))
            month_str = date_match.group(2)
            year = int(date_match.group(3))

            months = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
            }

            month = months.get(month_str, 1)
            return f"{year}-{month:02d}-{day:02d}"

        # Handle "Tomorrow at X:XX" format
        if "Tomorrow" in date_str:
            tomorrow = datetime.now() + timedelta(days=1)
            time_match = re.search(r'at (\d{1,2}):(\d{2})', date_str)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                return f"{tomorrow.year}-{tomorrow.month:02d}-{tomorrow.day:02d}-{hour:02d}-{minute:02d}"
            return f"{tomorrow.year}-{tomorrow.month:02d}-{tomorrow.day:02d}-19-00"

        return date_str  # Fallback to original string

    except Exception:
        return date_str

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

        # Handle "Fri, 28 Nov at 21:00" format (no year)
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

            # Create the event date for this year
            event_date = datetime(year, month, day, hour, minute)

            # If the date is more than 3 months in the past, assume it's next year
            # If it's within 3 months (past or future), keep it as this year
            three_months_ago = datetime.now() - timedelta(days=90)
            if event_date < three_months_ago:
                event_date = datetime(year + 1, month, day, hour, minute)

            return event_date

        # Handle "September 10, 2025" format (with year)
        date_with_year_match = re.search(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
        if date_with_year_match:
            month_str = date_with_year_match.group(1)
            day = int(date_with_year_match.group(2))
            year = int(date_with_year_match.group(3))

            months = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }

            month = months.get(month_str, 1)
            return datetime(year, month, day, 19, 0)  # Default to 19:00 if no time

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
    conn = get_db_connection()
    c = conn.cursor()
    # Select the event with the highest going_count for each unique title+date+location combination
    c.execute("""
        SELECT title, date, location, facebook_url, going_count, interested_count, is_upcoming
        FROM events
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY title, date, location ORDER BY going_count DESC, id ASC) as rn
                FROM events
            )
            WHERE rn = 1
        )
    """)
    rows = c.fetchall()
    conn.close()

    events = []
    current_time = datetime.now()

    for row in rows:
        event_date = parse_event_date(row[1])
        is_future = event_date > current_time
        is_recent_past = event_date > current_time - timedelta(days=30)  # Include events from last 30 days

        # Include only future events
        if is_future:
            events.append({
                'title': row[0],
                'date': row[1],
                'location': row[2],
                'facebook_url': row[3] or 'https://www.facebook.com/bearduk/events',
                'venue_url': None,  # Not in database
                'venue_image': None,  # Not in database
                'going_count': row[4] or 0,
                'interested_count': row[5] or 0,
                'friends_going': '',  # Not in database
                'is_upcoming': bool(row[6]),
                'datetime_obj': event_date
            })

    # Sort by date (earliest first)
    events.sort(key=lambda x: x['datetime_obj'])

    return events

def get_follower_counts():
    """Get the latest follower counts for all social media platforms"""
    conn = get_db_connection()
    c = conn.cursor()

    # Get latest follower count for each platform/username combination
    c.execute('''
        SELECT platform, username, follower_count
        FROM social_media_followers
        WHERE (platform, username, scraped_at) IN (
            SELECT platform, username, MAX(scraped_at)
            FROM social_media_followers
            GROUP BY platform, username
        )
    ''')

    followers = {}
    for row in c.fetchall():
        platform, username, count = row
        followers[platform] = count

    conn.close()
    return followers

def combine_scraped_and_manual_events(scraped_events):
    """Return only scraped events - no manual fallbacks"""
    return scraped_events

def get_events():
    try:
        init_db()
        
        # Check if we need to scrape (every 6 hours)
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM events WHERE scraped_at > NOW() - INTERVAL '6 hours'")
        result = c.fetchone()
        recent_count = result[0] if result else 0
        conn.close()
        
        if recent_count == 0:
            try:
                scraped_events = scrape_facebook_events()
                if scraped_events:
                    # Save only scraped events (no manual fallbacks)
                    save_events_to_db(scraped_events)
                # If no events scraped, don't add anything
            except Exception as scrape_error:
                # If scraping fails, don't add manual events
                pass
        
        return load_events_from_db()
    except Exception as e:
        # If database operations fail, return empty list
        return []

@app.route('/')
def home():
    try:
        events = get_events()
        # Add date badges to events
        events = add_date_badges(events)
        # All events are now already filtered to be upcoming and sorted by date
        upcoming_events = events[:6]  # Show first 6 upcoming events

        # Get follower counts
        follower_counts = get_follower_counts()

        return render_template('index.html', upcoming_events=upcoming_events, past_events=[], follower_counts=follower_counts)
    except Exception as e:
        # If event loading fails, show empty list
        return render_template('index.html', upcoming_events=[], past_events=[], follower_counts={})

@app.route('/update_events')
def update_events():
    """Manual endpoint to trigger event scraping"""
    try:
        events = scrape_facebook_events()
        if not events:
            # If scraping fails, add the manual events that aren't on Facebook
            add_manual_events()
            events = load_events_from_db()  # Reload to get all events
        else:
            save_events_to_db(events)
        return f"Updated {len(events)} events successfully!"
    except Exception as e:
        return f"Error updating events: {e}"

@app.route('/events_json')
def events_json():
    """Return events as JSON for API access"""
    events = get_events()
    return {'events': events}

@app.route('/update_followers', methods=['GET', 'POST'])
def update_followers():
    """Update social media follower counts"""
    try:
        facebook_html = None
        instagram_html = None
        if request.method == 'POST':
            facebook_html = request.form.get('facebook_html')
            instagram_html = request.form.get('instagram_html')

        from update_followers import update_all_followers
        update_all_followers(facebook_html, instagram_html)
        return {'status': 'success', 'message': 'Follower counts updated successfully'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

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
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1200")  # Increased height for more content
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--accept-lang=en-US,en")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Speed up loading
            chrome_options.add_argument("--disable-dev-tools")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Set Chrome binary location based on environment
            import platform
            if platform.system() == "Windows":
                chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            else:
                chrome_options.binary_location = "/usr/bin/google-chrome"
            
            driver = webdriver.Chrome(options=chrome_options)
            response_data['chrome_setup'] = 'success'
            
            # Make the browser look more like a real user
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
            
            # Load Facebook page
            driver.get("https://www.facebook.com/bearduk/events")
            response_data['page_load'] = 'loaded'
            
            time.sleep(10)
            
            # Get page text
            page_text = driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            response_data['found_lines'] = len(lines)
            response_data['raw_text_sample'] = '\n'.join(lines[:50])  # First 50 lines as sample
            
            # Process for events using improved parsing
            events = []

            # Method 1: Try to find event containers using CSS selectors
            try:
                # Try multiple CSS selectors for Facebook events - look for larger containers
                selectors = [
                    "[role='article']",  # Event articles
                    "[data-pagelet='Events'] [role='article']",  # Events pagelet articles
                    "[data-testid='event-card']",  # Event cards
                    ".event",  # Generic event class
                    "[role='link'][href*='/events/']",  # Event links (fallback)
                ]

                all_containers = []
                for selector in selectors:
                    try:
                        containers = driver.find_elements(By.CSS_SELECTOR, selector)
                        all_containers.extend(containers)
                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Selector '{selector}' found {len(containers)} elements\n")
                    except Exception as e:
                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Selector '{selector}' failed: {e}\n")
                        continue

                with open('/app/debug.log', 'a') as f:
                    f.write(f"Total containers found: {len(all_containers)}\n")

                for container in all_containers[:30]:  # Limit to first 30 to avoid duplicates
                    try:
                        # Get all text from this container
                        container_text = container.text.strip()
                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Container text: {container_text[:200]}...\n")

                        # Look for event links within this container
                        event_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/events/']")
                        for link in event_links[:3]:  # Limit per container
                            href = link.get_attribute('href')
                            if href and '/events/' in href:
                                with open('/app/debug.log', 'a') as f:
                                    f.write(f"Found event link in container: {href}\n")

                                # Parse the container text for event information
                                lines = [line.strip() for line in container_text.split('\n') if line.strip()]

                                # Look for date patterns in the container
                                date_line = None
                                title_line = None
                                location_line = None

                                for line in lines:
                                    # Check for date patterns
                                    date_patterns = [
                                        r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)?\s*(GMT|BST)?',
                                        r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)?\s*(GMT|BST)?',
                                        r'(Today|Tomorrow)\s+at\s+(\d{1,2}:\d{2})',
                                        r'Sun,\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})'
                                    ]

                                    if not date_line:
                                        for pattern in date_patterns:
                                            if re.match(pattern, line):
                                                date_line = line
                                                break

                                    # Look for title (contains BEARD or @)
                                    if not title_line and ('beard' in line.lower() or '@' in line or 'BEARD' in line):
                                        title_line = line

                                    # Look for location (usually after title)
                                    if title_line and not location_line and line and len(line) > 3:
                                        # Skip if it looks like a date or title
                                        if not any(re.match(p, line) for p in date_patterns) and 'beard' not in line.lower():
                                            location_line = line

                                if date_line and title_line:
                                    # Extract Facebook event ID from URL
                                    event_id_match = re.search(r'/events/(\d+)', href)
                                    event_id = event_id_match.group(1) if event_id_match else ""

                                    # Check for duplicates
                                    is_duplicate = False
                                    for existing_event in events:
                                        if (existing_event['title'] == title_line and
                                            existing_event['date'] == date_line):
                                            is_duplicate = True
                                            break

                                    if not is_duplicate:
                                        events.append({
                                            'date': date_line,
                                            'title': title_line,
                                            'location': location_line or "",
                                            'is_upcoming': True,
                                            'facebook_url': f"https://www.facebook.com/events/{event_id}",
                                            'event_id': event_id,
                                            'line_number': 0,
                                            'source': 'css_container'
                                        })
                                        with open('/app/debug.log', 'a') as f:
                                            f.write(f"Added event from CSS container: {title_line}\n")

                    except Exception as e:
                        with open('/app/debug.log', 'a') as f:
                            f.write(f"Error processing container: {e}\n")
                        continue

            except Exception as e:
                with open('/app/debug.log', 'a') as f:
                    f.write(f"CSS selector method failed: {e}\n")

            # Method 2: Fallback to the original line-by-line parsing if needed
            if len(events) < 6:
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    lines = [line.strip() for line in page_text.split('\n') if line.strip()]

                    with open('/app/debug.log', 'a') as f:
                        f.write(f"Fallback parsing: found {len(lines)} lines of text\n")

                    i = 0
                    while i < len(lines) and len(events) < 10:
                        line = lines[i]

                        # Look for date patterns - Updated to match Facebook's actual format
                        date_pattern1 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)\s+(GMT|BST)'
                        date_pattern2 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(GMT|BST)'
                        date_pattern3 = r'(Today|Tomorrow)\s+at\s+(\d{1,2}:\d{2})'
                        date_pattern4 = r'Sun,\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})'
                        date_pattern5 = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+at\s+(\d{1,2}:\d{2})\s+(AM|PM)?\s*(GMT|BST)?'

                        date_match = (re.match(date_pattern1, line) or re.match(date_pattern2, line) or
                                    re.match(date_pattern3, line) or re.match(date_pattern4, line) or
                                    re.match(date_pattern5, line))

                        if date_match and i + 1 < len(lines):
                            event_date = line
                            event_title = lines[i + 1] if i + 1 < len(lines) else ""
                            event_location = lines[i + 2] if i + 2 < len(lines) else ""

                            with open('/app/debug.log', 'a') as f:
                                f.write(f"Found potential event: {event_date} - {event_title} - {event_location}\n")

                            # Check if this looks like a BEARD event (more inclusive check)
                            title_lower = event_title.lower()
                            location_lower = event_location.lower()
                            is_beard_event = (
                                'beard' in title_lower or
                                '@' in event_title or
                                'BEARD' in event_title or
                                'beard' in location_lower or
                                'private party' in title_lower or
                                'anglers' in location_lower or
                                'vaults' in location_lower or
                                'steamtown' in location_lower
                            )

                            if is_beard_event:
                                # Check if we already have this event
                                is_duplicate = False
                                for existing_event in events:
                                    if (existing_event['title'] == event_title and
                                        existing_event['date'] == event_date):
                                        is_duplicate = True
                                        break

                                if not is_duplicate:
                                    events.append({
                                        'date': event_date,
                                        'title': event_title,
                                        'location': event_location,
                                        'is_upcoming': True,
                                        'facebook_url': 'https://www.facebook.com/bearduk/events',
                                        'line_number': i,
                                        'source': 'line_by_line'
                                    })
                                    with open('/app/debug.log', 'a') as f:
                                        f.write(f"Added event from fallback: {event_title}\n")

                            i += 3
                        else:
                            i += 1

                except Exception as e:
                    with open('/app/debug.log', 'a') as f:
                        f.write(f"Fallback parsing failed: {e}\n")

            with open('/app/debug.log', 'a') as f:
                f.write(f"Total events found: {len(events)}\n")

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
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get recent scraping info
        c.execute("SELECT COUNT(*) FROM events WHERE scraped_at > NOW() - INTERVAL '6 hours'")
        result = c.fetchone()
        recent_scrapes = result[0] if result else 0
        
        c.execute("SELECT COUNT(*) FROM events")
        result = c.fetchone()
        total_events = result[0] if result else 0
        
        # Get all events with details
        c.execute("SELECT title, date, location, facebook_url, is_upcoming, scraped_at FROM events ORDER BY scraped_at DESC LIMIT 10")
        events_rows = c.fetchall()
        recent_events = [
            {
                'title': row[0],
                'date': row[1], 
                'location': row[2],
                'facebook_url': row[3],
                'is_upcoming': row[4],
                'scraped_at': str(row[5])
            } for row in events_rows
        ]
        
        conn.close()
        
        # System info
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_events': total_events,
                'recent_scrapes_6h': recent_scrapes,
                'database_connected': True,
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

# Set up background tasks when the module is imported
setup_background_tasks()

if __name__ == '__main__':
    # Production-ready configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)