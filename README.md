# BEARD UK Band Website

🎸 **High-energy pub-rock band website with automated Facebook event scraping and 80s synthwave aesthetics**

## Features

- **� Automated Event Scraping** - Real-time Facebook event integration using Selenium
- **🎨 80s Synthwave Theme** - Purple/red neon aesthetics with CRT effects and scanlines  
- **📱 Mobile Responsive** - Clean mobile experience with adaptive navigation
- **� Social Integration** - Direct links to Facebook events and social media
- **⚡ Real-time Updates** - Automatic event refresh and duplicate prevention
- **🎯 Future-focused** - Only displays upcoming gigs in chronological order

## Tech Stack

- **Flask 2.3.3** - Python web framework
- **Selenium 4.35.0** - Browser automation for Facebook scraping
- **SQLite** - Event data storage
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

3. **Install ChromeDriver** (REQUIRED for Facebook scraping):
   - Download from [chromedriver.chromium.org](https://chromedriver.chromium.org/)
   - Add to your PATH or place in project directory

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Visit**: http://localhost:5000
```bash
python -c "from app import init_db; init_db()"
```

3. Run the application:
```bash
python app.py
```

4. Visit `http://127.0.0.1:5000` in your browser

## Manual Event Updates

To manually update events:
```bash
python update_events.py
```

## API Endpoints

- `GET /` - Main website
- `GET /update_events` - Trigger manual event scraping
- `GET /events_json` - Get events as JSON

## Theme Features

- **Hero Section**: Local background image with CRT scanlines and flicker effects
- **Navigation**: Glowing purple/red hover effects
- **Typography**: Impact font with neon glow effects
- **Animations**: Synthwave gradients and retro CRT effects
- **Color Palette**: Deep purples (#660066, #cc0066) and magentas (#ff00ff, #ff0066)

## File Structure

```
bearduk/
├── app.py                 # Flask application
├── update_events.py       # Manual event update script
├── requirements.txt       # Python dependencies
├── events.db             # SQLite database (auto-created)
├── templates/
│   └── index.html        # Main template
└── static/
    ├── style.css         # 80s theme styles
    └── hero-background.jpg # Hero background image
```

## Deployment

The app is ready for deployment on platforms like:
- Heroku
- DigitalOcean App Platform
- Railway
- Coolify (as mentioned in your requirements)

## Event Scraping

The app attempts to scrape Facebook events daily. If scraping fails, it falls back to manually curated events. The scraper is designed to be resilient to Facebook's anti-scraping measures.

## Customization

- Edit `static/style.css` to modify the 80s theme colors
- Update events in `app.py` or via the `/update_events` endpoint
- Modify the hero image by replacing `static/hero-background.jpg`