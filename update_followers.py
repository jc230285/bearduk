import requests
import sqlite3
import os
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re

DATABASE = 'events.db'

def init_followers_db():
    """Initialize the followers database table"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS social_media_followers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  platform TEXT NOT NULL,
                  username TEXT NOT NULL,
                  follower_count INTEGER NOT NULL,
                  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_facebook_followers(page_id, access_token=None, html_content=None):
    """Get follower count from Facebook Graph API or HTML parsing"""
    # If HTML content is provided, parse it directly
    if html_content:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Look for the followers count in the HTML
            followers_link = soup.find('a', href=re.compile(r'followers'))
            if followers_link:
                strong_tag = followers_link.find('strong')
                if strong_tag:
                    count_text = strong_tag.get_text().strip()
                    return int(count_text.replace(',', ''))
            print("Could not find follower count in provided HTML")
            return None
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return None

    # Otherwise try Graph API
    if access_token:
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}"
            params = {
                'fields': 'followers_count',
                'access_token': access_token
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('followers_count', 0)
        except Exception as e:
            print(f"Error fetching Facebook followers via API: {e}")
            return None

    print("No access token or HTML content provided for Facebook")
    return None

def get_instagram_followers(username, access_token=None, html_content=None):
    """Get follower count from Instagram Basic Display API or HTML parsing"""
    # If HTML content is provided, parse it directly
    if html_content:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Look for the span with title attribute containing follower count
            count_span = soup.find('span', title=re.compile(r'^\d+$'))
            if count_span and count_span.get('title'):
                return int(count_span['title'].replace(',', ''))

            # Alternative: look for spans containing "followers" and extract the number
            follower_text = soup.find(text=re.compile(r'followers'))
            if follower_text:
                # Find the parent elements and look for the count
                parent = follower_text.parent
                if parent:
                    count_span = parent.find_previous('span', class_=re.compile(r'html-span'))
                    if count_span:
                        count_text = count_span.get_text().strip()
                        return int(count_text.replace(',', ''))

            print("Could not find follower count in provided Instagram HTML")
            return None
        except Exception as e:
            print(f"Error parsing Instagram HTML: {e}")
            return None

    # Otherwise try Instagram Basic Display API
    if access_token:
        # This would require Instagram Business account and proper setup
        # For now, return None and use fallback
        pass

    # Fallback: Try to scrape from Instagram web (less reliable)
    try:
        url = f"https://www.instagram.com/{username}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Look for follower count in the HTML (this is fragile and may break)
        html = response.text
        if '"edge_followed_by":{"count":' in html:
            start = html.find('"edge_followed_by":{"count":') + len('"edge_followed_by":{"count":')
            end = html.find('}', start)
            count_str = html[start:end].split(',')[0]
            return int(count_str)
        else:
            print("Could not find follower count in Instagram HTML")
            return None

    except Exception as e:
        print(f"Error fetching Instagram followers: {e}")
        return None

def save_follower_count(platform, username, count):
    """Save follower count to database - one record per platform per day max"""
    if count is None:
        return False

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        # Check if we already have a record for this platform/username today
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT id FROM social_media_followers
                     WHERE platform = ? AND username = ?
                     AND DATE(scraped_at) = ?''', (platform, username, today))

        existing_record = c.fetchone()

        if existing_record:
            # Update existing record for today
            c.execute('''UPDATE social_media_followers
                         SET follower_count = ?, scraped_at = CURRENT_TIMESTAMP
                         WHERE id = ?''', (count, existing_record[0]))
            print(f"Updated {platform} followers for {username}: {count} (existing record for today)")
        else:
            # Insert new record
            c.execute('''INSERT INTO social_media_followers (platform, username, follower_count)
                         VALUES (?, ?, ?)''', (platform, username, count))
            print(f"Saved {platform} followers for {username}: {count}")

        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving follower count: {e}")
        return False
    finally:
        conn.close()

def get_latest_follower_count(platform, username):
    """Get the most recent follower count for a platform/username"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT follower_count FROM social_media_followers
                 WHERE platform = ? AND username = ?
                 ORDER BY scraped_at DESC LIMIT 1''', (platform, username))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_all_followers(facebook_html=None, instagram_html=None):
    """Update follower counts for all configured social media accounts"""
    init_followers_db()

    # Configuration - these would typically come from environment variables or config file
    # For Facebook, you can provide HTML content directly or use API
    facebook_config = {
        'page_id': os.getenv('FACEBOOK_PAGE_ID', 'bearduk'),  # Replace with actual page ID
        'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),  # Get from Facebook Developer Console
        'html_content': facebook_html  # HTML content if provided
    }

    # For Instagram, you can try web scraping (unreliable) or use Instagram Basic Display API
    instagram_config = {
        'username': os.getenv('INSTAGRAM_USERNAME', 'beardbanduk'),
        'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN')  # Optional - for API access
    }

    # Update Facebook followers
    fb_count = get_facebook_followers(
        facebook_config['page_id'],
        facebook_config['access_token'],
        facebook_config['html_content']
    )
    if fb_count is not None:
        save_follower_count('facebook', facebook_config['page_id'], fb_count)

    # Update Instagram followers
    ig_count = get_instagram_followers(
        instagram_config['username'],
        instagram_config['access_token'],
        instagram_html
    )
    if ig_count is not None:
        save_follower_count('instagram', instagram_config['username'], ig_count)

if __name__ == "__main__":
    update_all_followers()
