from flask import Flask, render_template, request
import psycopg2
import os
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Get a database connection"""
    return psycopg2.connect(DATABASE_URL)

def load_events_from_beard_events():
    """Load upcoming events from beard_events table"""
    print("=== DEBUG: Loading events from beard_events ===")
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get future events only, ordered by timestamp
    c.execute("""
        SELECT id, url, timestamp, name, responded, location, venueurl, duration, imageurl, updated
        FROM beard_events 
        WHERE timestamp > NOW()
        ORDER BY timestamp ASC
    """)
    
    rows = c.fetchall()
    conn.close()
    
    print(f"DEBUG: Found {len(rows)} raw rows from database")

    events = []
    for i, row in enumerate(rows):
        event_id, url, timestamp, name, responded, location, venueurl, duration, imageurl, updated = row
        print(f"DEBUG: Processing event {i+1}: {name} at {timestamp}")
        
        # Format the event data
        try:
            formatted_date = format_event_date(timestamp)
            print(f"DEBUG: Formatted date: {formatted_date}")
            
            event_data = {
                'id': event_id,
                'title': name or 'BEARD Event',
                'date': formatted_date,
                'location': location or 'TBA',
                'facebook_url': url,
                'venue_url': venueurl,
                'venue_image': imageurl,
                'going_count': responded or 0,
                'interested_count': 0,  # Not available in beard_events
                'friends_going': '',
                'is_upcoming': True,
                'datetime_obj': timestamp
            }
            events.append(event_data)
            print(f"DEBUG: Added event: {event_data['title']}")
        except Exception as e:
            print(f"DEBUG: Error processing event {name}: {e}")

    print(f"DEBUG: Final events list has {len(events)} events")
    return events

def format_event_date(timestamp):
    """Format timestamp to readable date string"""
    if not timestamp:
        return "Date TBA"
    
    try:
        # Format like "Friday 28 November 2025 from 21:00"
        day_name = timestamp.strftime("%A")
        day = timestamp.strftime("%d").lstrip('0')  # Safer approach for leading zeros
        month = timestamp.strftime("%B")
        year = timestamp.strftime("%Y")
        time = timestamp.strftime("%H:%M")
        
        return f"{day_name} {day} {month} {year} from {time}"
    except Exception as e:
        print(f"DEBUG: Date formatting error for {timestamp}: {e}")
        return str(timestamp)

def parse_event_date(date_str):
    """Parse various date formats - simplified version for beard_events timestamp"""
    try:
        # If it's already a datetime object, return it
        if isinstance(date_str, datetime):
            return date_str
        
        # Try parsing as ISO format
        return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
    except:
        # Fallback to current time if parsing fails
        return datetime.now()

def add_date_badges(events):
    """Add formatted date information to events"""
    print(f"DEBUG: Adding date badges to {len(events)} events")
    current_time = datetime.now()
    
    for event in events:
        event_date = event['datetime_obj']
        
        # Determine if it's today, tomorrow, this week, etc.
        days_until = (event_date.date() - current_time.date()).days
        
        if days_until == 0:
            event['date_badge'] = "TODAY"
            event['date_class'] = "today"
        elif days_until == 1:
            event['date_badge'] = "TOMORROW"
            event['date_class'] = "tomorrow"
        elif days_until <= 7:
            event['date_badge'] = "THIS WEEK"
            event['date_class'] = "this-week"
        elif days_until <= 30:
            event['date_badge'] = "THIS MONTH"
            event['date_class'] = "this-month"
        else:
            event['date_badge'] = "UPCOMING"
            event['date_class'] = "upcoming"
    
    return events

@app.route('/')
def index():
    print("=== DEBUG: Index route called ===")
    try:
        events = load_events_from_beard_events()
        print(f"DEBUG: Loaded {len(events)} events from database")
        
        events_with_badges = add_date_badges(events)
        print(f"DEBUG: Added badges to {len(events_with_badges)} events")
        
        print(f"DEBUG: Rendering template with {len(events_with_badges)} events")
        
        return render_template('index.html', 
                             upcoming_events=events_with_badges,
                             total_events=len(events_with_badges))
    except Exception as e:
        print(f"DEBUG: Error in index route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', 
                             upcoming_events=[], 
                             total_events=0,
                             error="Unable to load events")

@app.route('/debug_status')
def debug_status():
    """Debug endpoint showing system status and database contents"""
    try:
        from datetime import datetime
        
        # Check database
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get event counts
        c.execute("SELECT COUNT(*) FROM beard_events")
        total_events = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM beard_events WHERE timestamp > NOW()")
        future_events = c.fetchone()[0]
        
        # Get recent events
        c.execute("SELECT name, timestamp, location, responded FROM beard_events WHERE timestamp > NOW() ORDER BY timestamp ASC LIMIT 5")
        events_rows = c.fetchall()
        recent_events = [
            {
                'name': row[0],
                'timestamp': str(row[1]),
                'location': row[2],
                'responded': row[3]
            } for row in events_rows
        ]
        
        conn.close()
        
        # System info
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_events': total_events,
                'future_events': future_events,
                'database_connected': True,
                'recent_events': recent_events
            },
            'system': {
                'environment': os.environ.get('FLASK_ENV', 'not_set'),
                'port': os.environ.get('PORT', 'not_set')
            },
            'version': 'simplified-no-scraping'
        }
        
        return status_data
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)