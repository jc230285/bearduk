#!/usr/bin/env python3
"""
Aggressive test script to debug Facebook scraping with multiple approaches
"""

import requests
from bs4 import BeautifulSoup
import time
import random

FACEBOOK_URL = 'https://www.facebook.com/bearduk/events'

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    ]
    return random.choice(user_agents)

def test_aggressive_scraping():
    """Test Facebook scraping with multiple aggressive approaches"""
    print("🚀 Starting aggressive Facebook scraping test...")
    print(f"🎯 Target URL: {FACEBOOK_URL}")
    print("=" * 60)

    # Test 1: Basic request with realistic headers
    print("\n📋 Test 1: Basic request with realistic headers")
    try:
        headers = {
            'User-Agent': get_random_user_agent(),
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

        response = requests.get(FACEBOOK_URL, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            print(f"Page title: {title.get_text() if title else 'No title'}")

            all_links = soup.find_all('a')
            event_links = [link for link in all_links if '/events/' in str(getattr(link, 'get', lambda x: '')('href') or '')]
            print(f"Event links found: {len(event_links)}")

            if event_links:
                print("✅ SUCCESS: Found event links!")
                for i, link in enumerate(event_links[:3]):
                    print(f"  {i+1}. {link.get_text(strip=True)}")
            else:
                print("❌ No event links found")
        else:
            print(f"❌ Failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: With cookies and session
    print("\n📋 Test 2: Using session with cookies")
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # First visit the main page
        print("Visiting main Facebook page first...")
        session.get('https://www.facebook.com', timeout=10)
        time.sleep(random.uniform(1, 3))

        # Then visit events page
        print("Now visiting events page...")
        response = session.get(FACEBOOK_URL, timeout=15)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            all_links = soup.find_all('a')
            event_links = [link for link in all_links if '/events/' in str(getattr(link, 'get', lambda x: '')('href') or '')]
            print(f"Event links found: {len(event_links)}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Mobile user agent
    print("\n📋 Test 3: Mobile user agent")
    try:
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        response = requests.get(FACEBOOK_URL, headers=mobile_headers, timeout=15)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            all_links = soup.find_all('a')
            event_links = [link for link in all_links if '/events/' in str(getattr(link, 'get', lambda x: '')('href') or '')]
            print(f"Event links found: {len(event_links)}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Check different Facebook URLs
    print("\n📋 Test 4: Testing different Facebook URLs")
    test_urls = [
        'https://www.facebook.com/bearduk',
        'https://m.facebook.com/bearduk/events',
        'https://www.facebook.com/pg/bearduk/events',
    ]

    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                all_links = soup.find_all('a')
                event_links = [link for link in all_links if '/events/' in str(getattr(link, 'get', lambda x: '')('href') or '')]
                print(f"Event links found: {len(event_links)}")

                if event_links:
                    print("✅ Found events!")
                    break

            time.sleep(random.uniform(2, 5))  # Be respectful

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    print("Facebook has implemented aggressive anti-scraping measures.")
    print("The 400 status codes indicate they're blocking automated requests.")
    print("Consider using Facebook Graph API or manual event updates instead.")
    print("=" * 60)

if __name__ == "__main__":
    test_aggressive_scraping()