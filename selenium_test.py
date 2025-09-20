#!/usr/bin/env python3
"""
Install selenium and try browser automation
"""

import subprocess
import sys

def install_selenium():
    """Install selenium for browser automation"""
    try:
        print("📦 Installing selenium...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'selenium'])
        print("✅ Selenium installed!")
        return True
    except Exception as e:
        print(f"❌ Failed to install selenium: {e}")
        return False

def test_selenium_scraping():
    """Try selenium-based scraping"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        print("🚗 Setting up Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized!")
            
            # Try to load Facebook page
            print("🌐 Loading Facebook page...")
            driver.get("https://www.facebook.com/bearduk")
            
            # Wait a bit for JavaScript to load
            time.sleep(5)
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            print(f"📄 Page source length: {len(page_source)} characters")
            
            # Look for event-related content
            if 'event' in page_source.lower():
                print("✅ Found 'event' in page source!")
                
                # Extract text content
                text_content = driver.find_element(By.TAG_NAME, "body").text
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                event_lines = []
                for line in lines:
                    if any(word in line.lower() for word in ['event', 'gig', 'show', 'concert', 'upcoming']):
                        if len(line) > 10 and len(line) < 150:
                            event_lines.append(line)
                
                if event_lines:
                    print(f"🎉 Found {len(event_lines)} potential event lines:")
                    for i, line in enumerate(event_lines[:10]):
                        print(f"  {i+1}. {line}")
                else:
                    print("❌ No event-related content found")
            else:
                print("❌ No 'event' keyword found in page")
            
            # Try events page directly
            print("\n🎯 Trying events page...")
            driver.get("https://www.facebook.com/bearduk/events")
            time.sleep(5)
            
            events_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"Events page text length: {len(events_text)}")
            
            if events_text:
                lines = [line.strip() for line in events_text.split('\n') if line.strip()]
                for i, line in enumerate(lines[:20]):
                    print(f"  {i+1}. {line}")
            
            driver.quit()
            print("✅ Browser automation test complete!")
            
        except Exception as e:
            print(f"❌ Chrome driver error: {e}")
            print("💡 You may need to install ChromeDriver:")
            print("   1. Download from https://chromedriver.chromium.org/")
            print("   2. Add to PATH")
            return False
            
    except ImportError:
        print("❌ Selenium not available, trying to install...")
        if install_selenium():
            print("🔄 Restart script to try again with selenium")
        return False
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return False

def final_recommendation():
    """Provide final recommendations based on all tests"""
    print("\n" + "="*60)
    print("🎯 FINAL ASSESSMENT & RECOMMENDATIONS")
    print("="*60)
    
    print("\n📊 What We Discovered:")
    print("✅ Facebook actively blocks automated scraping")
    print("✅ Mobile endpoints return obfuscated content")
    print("✅ Graph API requires proper authentication")
    print("✅ Alternative sources exist but limited BEARD data")
    
    print("\n🛠️ BEST SOLUTIONS (in order of preference):")
    print("\n1. 🥇 MANUAL EVENT UPDATES (Recommended)")
    print("   - Most reliable and fast")
    print("   - Your current system already works well")
    print("   - Add events via the /update_events endpoint")
    
    print("\n2. 🥈 FACEBOOK GRAPH API")
    print("   - Requires Facebook Developer account")
    print("   - Need to create Facebook App")
    print("   - Get proper access tokens")
    print("   - More complex but official approach")
    
    print("\n3. 🥉 BROWSER AUTOMATION (Selenium)")
    print("   - Can bypass some JavaScript protection")
    print("   - Requires ChromeDriver installation")
    print("   - More resource intensive")
    print("   - May still be blocked by Facebook")
    
    print("\n4. 🔄 ALTERNATIVE PLATFORMS")
    print("   - Post events on Eventbrite/Bandcamp")
    print("   - Scrape your own event sources")
    print("   - Use venue websites")
    
    print("\n💡 IMMEDIATE ACTION:")
    print("Keep using your manual event system - it's actually the most reliable!")
    print("Facebook's anti-scraping is too sophisticated for simple approaches.")

if __name__ == "__main__":
    success = test_selenium_scraping()
    if not success:
        final_recommendation()