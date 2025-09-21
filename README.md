# BEARD UK Band Website

🎸 **High-energy pub-rock band website with automated Facebook event scraping, social media follower tracking, and 80s synthwave aesthetics**

## Features

### 🎯 Core Features
- **📅 Automated Event Scraping** - Real-time Facebook event integration with duplicate prevention
- **👥 Social Media Follower Tracking** - Live Facebook and Instagram follower counts
- **🎨 80s Synthwave Theme** - Purple/red neon aesthetics with CRT effects and scanlines
- **📱 Mobile Responsive** - Clean mobile experience with adaptive navigation
- **🔄 Real-time Updates** - Automatic event refresh and follower count updates
- **🎯 Future-focused** - Only displays upcoming gigs in chronological order

### 🤖 Automation Features
- **One Record Per Day** - Follower tracking maintains maximum one record per platform per day
- **Duplicate Event Prevention** - Shows events with highest going_count when duplicates exist
- **HTML Parsing Fallback** - Works without API keys using direct HTML parsing
- **Database Optimization** - Efficient storage with automatic cleanup

## Tech Stack

- **Flask 2.3.3** - Python web framework
- **BeautifulSoup 4.12.2** - HTML parsing for social media scraping
- **Requests 2.31.0** - HTTP client for web scraping
- **SQLite** - Event and follower data storage
- **CSS3** - 80s synthwave animations and effects
- **HTML5** - Semantic markup with accessibility features

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/jc230285/bearduk.git
cd bearduk

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (optional - auto-creates on first run)
python -c "from app import init_db; init_db()"

# Run the application
python app.py
```

Visit `http://localhost:5000` to see the website.

### Docker Deployment

```bash
# Build the image
docker build -t bearduk-website .

# Run the container
docker run -p 5000:5000 bearduk-website
```

### Coolify Deployment

1. **Connect Repository**: Add this GitHub repo to your Coolify instance
2. **Auto-deploy**: Coolify will automatically detect the Dockerfile
3. **Environment**: Production-ready with Gunicorn WSGI server
4. **Health Checks**: Built-in monitoring and auto-restart

## Social Media Follower Tracking

### Manual Updates
```bash
# Update follower counts manually
python update_followers.py
```

### Features
- **Facebook & Instagram Support** - Tracks followers for both platforms
- **HTML Parsing** - No API keys required, uses direct HTML scraping
- **Daily Limits** - Maximum one record per platform per day
- **Historical Data** - Maintains follower count history with timestamps

### Facebook Scraper Implementation

The Facebook follower scraper uses BeautifulSoup to parse HTML content. Here's how it works:

```python
def get_facebook_followers(page_id, access_token=None, html_content=None):
    """Get follower count from Facebook Graph API or HTML parsing"""

    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Look for followers link with specific pattern
        followers_link = soup.find('a', href=re.compile(r'followers'))

        if followers_link:
            strong_tag = followers_link.find('strong')
            if strong_tag:
                count_text = strong_tag.get_text().strip()
                return int(count_text.replace(',', ''))

        return None
```

**HTML Structure to Monitor:**
- Facebook follower counts are typically in: `a[href*="followers"] strong`
- The count appears as plain text within a `<strong>` tag
- Format: `"X,XXX followers"` (commas for thousands)

**When Facebook Changes:**
1. Inspect the Facebook page HTML
2. Find the new selector for follower count
3. Update the `soup.find()` parameters in `get_facebook_followers()`
4. Test with real HTML content

### Instagram Scraper Implementation

The Instagram follower scraper handles multiple HTML patterns:

```python
def get_instagram_followers(username, access_token=None, html_content=None):
    """Get follower count from Instagram Basic Display API or HTML parsing"""

    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Method 1: Look for span with title attribute
        count_span = soup.find('span', title=re.compile(r'^\d+$'))
        if count_span and count_span.get('title'):
            return int(count_span['title'].replace(',', ''))

        # Method 2: Alternative pattern with parent elements
        follower_text = soup.find(text=re.compile(r'followers'))
        if follower_text:
            parent = follower_text.parent
            if parent:
                count_span = parent.find_previous('span', class_=re.compile(r'html-span'))
                if count_span:
                    count_text = count_span.get_text().strip()
                    return int(count_text.replace(',', ''))

        return None
```

**HTML Patterns to Monitor:**
1. `<span title="1234">1,234</span>` - Title attribute contains count
2. Text "followers" with nearby span containing the number
3. Class-based selectors that may change with Instagram updates

**When Instagram Changes:**
1. Check browser dev tools for new HTML structure
2. Update the `soup.find()` patterns
3. Add new fallback methods if needed
4. Test with current Instagram page HTML

## Event Management

### Automatic Event Scraping
Events are scraped from Facebook with duplicate prevention:
- Uses `ROW_NUMBER() OVER` window function to select highest going_count
- Filters for upcoming events only
- Handles Facebook's dynamic HTML structure

### Manual Event Updates
```bash
python update_events.py
```

### Database Schema
```sql
-- Events table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    location TEXT,
    facebook_url TEXT,
    is_upcoming BOOLEAN DEFAULT 1,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    going_count INTEGER DEFAULT 0,
    interested_count INTEGER DEFAULT 0
);

-- Social media followers table
CREATE TABLE social_media_followers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    username TEXT NOT NULL,
    follower_count INTEGER NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

- `GET /` - Main website with events and follower counts
- `GET /update_events` - Trigger manual event scraping
- `GET /events_json` - Get events as JSON
- `GET /follower_counts` - Get current follower counts as JSON

## Theme Features

### Visual Design
- **Hero Section**: Local background image with CRT scanlines and flicker effects
- **Navigation**: Glowing purple/red hover effects
- **Typography**: Impact font with neon glow effects
- **Animations**: Synthwave gradients and retro CRT effects
- **Color Palette**: Deep purples (#660066, #cc0066) and magentas (#ff00ff, #ff0066)

### Responsive Design
- Mobile-first approach with adaptive layouts
- Touch-friendly navigation
- Optimized for all screen sizes

## File Structure

```
bearduk/
├── app.py                 # Flask application with event management
├── update_followers.py    # Social media follower tracking
├── requirements.txt       # Python dependencies
├── events.db             # SQLite database (auto-created)
├── Dockerfile            # Docker configuration
├── .dockerignore         # Docker ignore file
├── templates/
│   └── index.html        # Main template with follower display
├── static/
│   ├── style.css         # 80s theme styles
│   └── hero-background.jpg # Hero background image
└── README.md             # This file
```

## Deployment Options

### Production Platforms
- **Coolify** - Recommended (auto-detects Dockerfile)
- **Heroku** - Traditional PaaS deployment
- **DigitalOcean App Platform** - Managed container deployment
- **Railway** - Git-based deployment
- **Docker** - Manual container deployment

### Environment Variables
```bash
# Optional: Facebook Graph API (fallback to HTML parsing)
FACEBOOK_ACCESS_TOKEN=your_token_here
FACEBOOK_PAGE_ID=your_page_id

# Optional: Instagram Basic Display API
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_USERNAME=your_username
```

## Maintenance & Troubleshooting

### Facebook Scraper Maintenance
When Facebook updates their HTML structure:

1. **Inspect the page**: Use browser dev tools to find follower count element
2. **Update selectors**: Modify `soup.find()` calls in `get_facebook_followers()`
3. **Test thoroughly**: Use real HTML content to verify parsing works
4. **Add fallbacks**: Include multiple selector patterns for resilience

### Instagram Scraper Maintenance
When Instagram changes their layout:

1. **Check multiple patterns**: Instagram uses different structures for different account types
2. **Update regex patterns**: Modify `re.compile()` patterns for finding counts
3. **Test on real pages**: Verify with actual Instagram profile HTML
4. **Monitor rate limits**: Instagram may block aggressive scraping

### Database Maintenance
```bash
# Clean up old follower records (optional)
python -c "
import sqlite3
conn = sqlite3.connect('events.db')
c = conn.cursor()
# Keep only last 30 days of follower data
c.execute('DELETE FROM social_media_followers WHERE scraped_at < datetime('now', '-30 days')')
conn.commit()
conn.close()
"
```

### Performance Optimization
- Follower updates run efficiently with daily limits
- Event scraping uses database indexes for fast queries
- Static assets are cached for better performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (especially scrapers)
5. Submit a pull request

## License

This project is open source. Feel free to use and modify as needed.