#!/usr/bin/env python3
"""
Ultimate Facebook scraping attempt using browser automation
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import base64

def decode_facebook_content():
    """Try to decode the obfuscated Facebook content"""
    print("🔍 Attempting to decode Facebook content...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Don't compress to avoid encoding issues
            'Connection': 'keep-alive',
        }
        
        response = requests.get('https://mbasic.facebook.com/bearduk/events', headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    content = response.content.decode(encoding, errors='ignore')
                    print(f"\n📋 Using encoding: {encoding}")
                    
                    # Look for readable text patterns
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all text that might be events
                    all_text = soup.get_text()
                    
                    # Look for event-like patterns
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    
                    print(f"Total lines found: {len(lines)}")
                    
                    # Look for lines with dates or venues
                    event_lines = []
                    for line in lines:
                        if any(word in line.lower() for word in ['event', 'gig', 'show', 'concert', 'at ', '@ ', 'pm', 'am', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            if len(line) > 5 and len(line) < 200:  # Reasonable length
                                event_lines.append(line)
                    
                    if event_lines:
                        print(f"✅ Found {len(event_lines)} potential event lines:")
                        for i, line in enumerate(event_lines[:10]):
                            print(f"  {i+1}. {line}")
                    
                    # Look for links that might contain event info
                    links = soup.find_all('a')
                    event_links = []
                    for link in links:
                        href = getattr(link, 'get', lambda x: '')('href') or ''
                        text = link.get_text(strip=True)
                        if '/events/' in str(href) and text and len(text) > 3:
                            event_links.append((text, href))
                    
                    if event_links:
                        print(f"✅ Found {len(event_links)} event links:")
                        for text, href in event_links[:5]:
                            print(f"  - {text}: {href}")
                    
                    break  # Use first successful encoding
                    
                except UnicodeDecodeError:
                    continue
                    
    except Exception as e:
        print(f"❌ Error: {e}")

def try_alternative_sources():
    """Try alternative sources for BEARD events"""
    print("\n🎯 Trying alternative event sources...")
    
    # Try searching for BEARD events on other platforms
    alternative_sources = [
        'https://www.songkick.com/search?query=BEARD%20UK',
        'https://www.bandsintown.com/en/a/15301696-beard-uk',
        'https://www.jambase.com/shows/artist/beard-uk',
        'https://www.setlist.fm/search?query=BEARD%20UK',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    for source in alternative_sources:
        try:
            print(f"\n📍 Checking: {source}")
            response = requests.get(source, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                # Look for dates and venues
                if 'beard' in text_content.lower():
                    print("✅ Found BEARD mentions!")
                    
                    # Extract lines with BEARD
                    lines = text_content.split('\n')
                    beard_lines = [line.strip() for line in lines if 'beard' in line.lower() and len(line.strip()) > 5]
                    
                    for line in beard_lines[:5]:
                        print(f"  - {line}")
                        
        except Exception as e:
            print(f"❌ Error with {source}: {e}")

def manual_event_extraction():
    """Manually try to extract events from the known obfuscated patterns"""
    print("\n🔧 Manual pattern extraction...")
    
    # Based on the patterns we saw: '@Wkr', '@i\x0c', '@iqk', etc.
    # These might be encoded venue names or event IDs
    
    print("The patterns we found (@Wkr, @iqk, etc.) suggest Facebook is using:")
    print("1. Character encoding obfuscation")
    print("2. Base64 or similar encoding")
    print("3. JavaScript-based content loading")
    print("\nRecommendations:")
    print("- Use browser automation (Selenium) with actual Chrome browser")
    print("- Implement Facebook Graph API properly")
    print("- Focus on manual event updates for reliability")

if __name__ == "__main__":
    decode_facebook_content()
    try_alternative_sources()
    manual_event_extraction()