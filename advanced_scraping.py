#!/usr/bin/env python3
"""
Advanced Facebook scraping with selenium and other techniques
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re

def test_advanced_techniques():
    """Try advanced scraping techniques"""
    print("🔥 Advanced Facebook Scraping Techniques")
    print("=" * 50)
    
    # Test 1: Look for embedded JSON data
    print("\n🎯 Test 1: Looking for embedded JSON data...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get('https://www.facebook.com/bearduk', headers=headers, timeout=15)
        
        if response.status_code == 200:
            content = response.text
            
            # Look for JSON data in script tags
            json_patterns = [
                r'__INITIAL_DATA__["\']:\s*({.*?})',
                r'data-store["\']:\s*({.*?})',
                r'"Events":\s*({.*?})',
                r'"events":\s*(\[.*?\])',
                r'"upcoming_events":\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    print(f"✅ Found JSON data with pattern: {pattern[:30]}...")
                    for i, match in enumerate(matches[:2]):
                        try:
                            data = json.loads(match)
                            print(f"  Match {i+1}: {str(data)[:200]}...")
                        except:
                            print(f"  Match {i+1}: Raw data found (not valid JSON)")
            
            # Look for event-related text
            event_keywords = ['event', 'upcoming', 'gig', 'concert', 'show', 'performance']
            for keyword in event_keywords:
                pattern = rf'({keyword}[^<>]*(?:at|@)[^<>]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^<>]*\d{{1,2}})'
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"✅ Found {keyword} mentions: {len(matches)}")
                    for match in matches[:3]:
                        print(f"  - {match}")
                        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Try the graph API endpoints without auth
    print("\n🎯 Test 2: Testing public Graph API endpoints...")
    try:
        public_endpoints = [
            'https://graph.facebook.com/bearduk',
            'https://graph.facebook.com/bearduk?fields=events',
            'https://graph.facebook.com/v18.0/bearduk',
            'https://graph.facebook.com/v18.0/bearduk/events',
        ]
        
        for endpoint in public_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                print(f"Endpoint: {endpoint}")
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Data: {json.dumps(data, indent=2)[:300]}...")
                else:
                    print(f"Error: {response.text[:200]}")
                print()
            except Exception as e:
                print(f"Error with {endpoint}: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Try RSS/Feed endpoints
    print("\n🎯 Test 3: Looking for RSS/feed endpoints...")
    try:
        feed_urls = [
            'https://www.facebook.com/feeds/page.php?id=bearduk&format=rss20',
            'https://www.facebook.com/bearduk/posts.rss',
            'https://graph.facebook.com/bearduk/feed',
        ]
        
        for feed_url in feed_urls:
            try:
                response = requests.get(feed_url, headers=headers, timeout=10)
                print(f"Feed: {feed_url}")
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Content type: {response.headers.get('content-type')}")
                    print(f"Content preview: {response.text[:300]}...")
                print()
            except Exception as e:
                print(f"Error with {feed_url}: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Try mobile.facebook.com with different approaches
    print("\n🎯 Test 4: Advanced mobile Facebook scraping...")
    try:
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        mobile_urls = [
            'https://m.facebook.com/bearduk',
            'https://m.facebook.com/bearduk/events',
            'https://touch.facebook.com/bearduk/events',
            'https://mbasic.facebook.com/bearduk/events',
        ]
        
        for url in mobile_urls:
            try:
                response = requests.get(url, headers=mobile_headers, timeout=15)
                print(f"Mobile URL: {url}")
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for event-related text in the mobile version
                    text_content = soup.get_text()
                    
                    # Search for date patterns
                    date_patterns = [
                        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})',
                        r'(\d{1,2}\/\d{1,2}\/\d{4})',
                        r'(\d{1,2}-\d{1,2}-\d{4})',
                        r'(Tomorrow|Today|Tonight)',
                        r'(\d{1,2}:\d{2}\s*(?:AM|PM))',
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            print(f"  Date patterns found: {matches[:5]}")
                    
                    # Look for venue/location patterns
                    venue_patterns = [
                        r'(@\s*[A-Z][a-zA-Z\s]+)',
                        r'(at\s+[A-Z][a-zA-Z\s]+)',
                        r'(\b(?:pub|bar|brewery|venue|hall|club)\b[^.]*)',
                    ]
                    
                    for pattern in venue_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            print(f"  Venue patterns found: {matches[:3]}")
                
                print()
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"Error with {url}: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 ADVANCED ANALYSIS COMPLETE")
    print("If any JSON data or patterns were found above, we can extract event info!")

if __name__ == "__main__":
    test_advanced_techniques()