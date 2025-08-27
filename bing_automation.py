#!/usr/bin/env python3
"""
Microsoft Bing Search Automation
Enhanced with Chrome Profile Support, Google News, and AI Integration

Author: AI Assistant
Version: 3.0
Date: August 2025
License: MIT

Features:
- Uses your actual Chrome profiles (logged-in accounts)
- Google News integration for fresh search topics
- Gemini AI support for unique search generation
- Human-like behavior patterns
- Microsoft compliance (2-5 minute delays)
- SQLite database to prevent duplicate searches
- Multiple automation methods
"""

import json
import random
import time
import sqlite3
import sys
import os
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
import feedparser
from fake_useragent import UserAgent

# Optional imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ASCII Art Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                  🚀 BING SEARCH AUTOMATION 🚀                ║
║                     Microsoft Rewards Edition                 ║
║                                                               ║
║  ✅ Chrome Profile Support    ✅ Google News Integration      ║
║  ✅ Gemini AI Topics         ✅ Human-like Behavior         ║
║  ✅ Microsoft Compliant      ✅ Anti-Detection              ║
╚═══════════════════════════════════════════════════════════════╝
"""

# Load configuration
def load_config():
    """Load configuration from config.json or create default."""
    default_config = {
        "geo": "IN",
        "hl": "en-IN",
        "tz": 330,
        "bing_market": "en-IN",
        "max_searches": 15,
        "search_delay_min": 120,
        "search_delay_max": 300,
        "page_interaction_delay_min": 3,
        "page_interaction_delay_max": 8,
        "background_mode": False,
        "headless_mode": False,
        "gemini_api_key": "",
        "log_file": "bing_search.log",
        "log_max_bytes": 1048576,
        "log_backup_count": 5,
        "db_file": "used_terms.db"
    }
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except FileNotFoundError:
        # Create default config
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("📁 Created default config.json file")
        return default_config

config = load_config()

# Setup logging
logger = logging.getLogger('bing_search')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    config['log_file'], 
    maxBytes=config['log_max_bytes'], 
    backupCount=config['log_backup_count']
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Database setup
db_file = config['db_file']
def init_database():
    """Initialize SQLite database for storing used search terms."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS used_terms (term TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def is_used(term):
    """Check if search term has been used before."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT 1 FROM used_terms WHERE term = ?', (term,))
    used = c.fetchone() is not None
    conn.close()
    return used

def mark_used(term):
    """Mark search term as used."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO used_terms (term) VALUES (?)', (term,))
    conn.commit()
    conn.close()

def get_used_count():
    """Get count of used search terms."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM used_terms')
    count = c.fetchone()[0]
    conn.close()
    return count

def reset_database():
    """Reset the used terms database."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('DELETE FROM used_terms')
    conn.commit()
    conn.close()
    print("🗑️  Database reset - all terms marked as unused")

# Chrome Profile Management
def get_chrome_profiles():
    """Get available Chrome profiles."""
    try:
        possible_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data"),
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome Beta\\User Data"),
            f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\User Data"
        ]
        
        user_data_dir = None
        for path in possible_paths:
            if os.path.exists(path):
                user_data_dir = path
                break
        
        if not user_data_dir:
            return []
        
        profiles = []
        
        # Check Default profile
        default_path = os.path.join(user_data_dir, "Default")
        if os.path.exists(default_path):
            profiles.append(("Default", "Default Profile"))
        
        # Check Profile directories
        for item in os.listdir(user_data_dir):
            if item.startswith("Profile "):
                profile_path = os.path.join(user_data_dir, item)
                if os.path.isdir(profile_path):
                    profile_name = item
                    try:
                        pref_file = os.path.join(profile_path, "Preferences")
                        if os.path.exists(pref_file):
                            with open(pref_file, 'r', encoding='utf-8') as f:
                                prefs = json.load(f)
                                if 'profile' in prefs and 'name' in prefs['profile']:
                                    profile_name = prefs['profile']['name']
                    except:
                        pass
                    profiles.append((item, profile_name))
        
        return profiles
    except Exception as e:
        logger.error(f"Error finding Chrome profiles: {e}")
        return []

def choose_chrome_profile():
    """Let user choose Chrome profile."""
    profiles = get_chrome_profiles()
    
    if not profiles:
        print("❌ No Chrome profiles found!")
        print("Please make sure Chrome is installed and has been run at least once.")
        return None, None
    
    print(f"\n📁 Found {len(profiles)} Chrome profile(s):")
    for i, (folder, name) in enumerate(profiles, 1):
        print(f"  {i}. {name} ({folder})")
    
    while True:
        try:
            choice = input(f"\nChoose profile (1-{len(profiles)}) [1]: ").strip()
            if not choice:
                choice = "1"
            choice = int(choice)
            
            if 1 <= choice <= len(profiles):
                selected = profiles[choice - 1]
                logger.info(f"Selected Chrome profile: {selected[1]}")
                return selected
            else:
                print(f"Please enter a number between 1 and {len(profiles)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

# Search Term Sources
def get_google_news_headlines():
    """Fetch Google News headlines."""
    try:
        headlines = []
        news_feeds = [
            "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen",
            "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen",
        ]
        
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        for feed_url in news_feeds:
            try:
                response = requests.get(feed_url, headers=headers, timeout=10)
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:8]:
                    title = entry.title.strip()
                    # Clean up title
                    if ' - ' in title:
                        title = title.split(' - ')[0]
                    if len(title) > 60:
                        title = title[:60] + "..."
                    headlines.append(title)
            except Exception as e:
                logger.warning(f"Failed to fetch from feed: {e}")
                continue
        
        # Remove duplicates and shuffle
        headlines = list(set(headlines))
        random.shuffle(headlines)
        logger.info(f"Fetched {len(headlines)} headlines from Google News")
        return headlines[:20]
        
    except Exception as e:
        logger.error(f"Failed to retrieve Google News: {e}")
        return []

def get_google_trends():
    """Get Google Trends data."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl=config['hl'], tz=config['tz'], geo=config['geo'])
        df = pytrends.trending_searches(pn='india')
        trends = df.iloc[:, 0].tolist()
        logger.info(f"Fetched {len(trends)} terms from Google Trends")
        return trends
    except Exception as e:
        logger.error(f"Google Trends failed: {e}")
        return []

def get_gemini_topics(count=10):
    """Generate search topics using Gemini AI."""
    if not GEMINI_AVAILABLE or not config.get('gemini_api_key'):
        return []
    
    try:
        genai.configure(api_key=config['gemini_api_key'])
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""Generate {count} diverse search topics that Indians typically search for on Bing. 
        Include mix of: current events, technology, entertainment, sports, finance, education, health, travel.
        Make them realistic and varied. Return only the search terms, one per line."""
        
        response = model.generate_content(prompt)
        topics = [line.strip() for line in response.text.split('\n') if line.strip()]
        logger.info(f"Generated {len(topics)} topics using Gemini AI")
        return topics[:count]
    except Exception as e:
        logger.error(f"Gemini AI failed: {e}")
        return []

def get_fallback_topics():
    """Fallback search topics."""
    topics = [
        "ChatGPT latest features 2025", "iPhone 16 Pro review", "Tesla stock news",
        "IPL 2025 schedule", "Budget 2025 India highlights", "ISRO Chandrayaan mission",
        "Bollywood movies 2025", "Netflix new releases", "Cricket World Cup 2025",
        "Climate change solutions", "Electric cars in India", "Space exploration news",
        "Stock market predictions", "Weather forecast Mumbai", "Job opportunities tech",
        "Education loan schemes", "Health insurance plans", "Travel destinations India",
        "Food delivery apps", "Gaming laptop reviews", "Social media trends",
        "Fashion trends 2025", "Investment strategies", "Cryptocurrency news",
        "AI tools for students", "Digital marketing courses", "Fitness apps review"
    ]
    random.shuffle(topics)
    return topics

def get_search_terms(source_choice, count_needed):
    """Get search terms based on source choice."""
    terms = []
    
    print(f"🔍 Gathering search terms...")
    
    if source_choice == 1:  # Google News
        news_headlines = get_google_news_headlines()
        terms.extend(news_headlines)
        
    elif source_choice == 2:  # Google Trends
        trends = get_google_trends()
        terms.extend(trends)
        
    elif source_choice == 3:  # Mixed Sources
        news_headlines = get_google_news_headlines()
        trends = get_google_trends()
        terms.extend(news_headlines[:8])
        terms.extend(trends[:7])
        
    elif source_choice == 4:  # Gemini AI
        ai_topics = get_gemini_topics(count_needed + 5)
        terms.extend(ai_topics)
    
    # Add fallback topics if needed
    if len(terms) < count_needed:
        fallback = get_fallback_topics()
        terms.extend(fallback)
    
    # Remove duplicates and filter unused terms
    terms = list(set(terms))
    available_terms = [t for t in terms if not is_used(t)]
    
    if len(available_terms) < count_needed:
        print(f"⚠️  Only {len(available_terms)} unused terms available")
        if len(available_terms) == 0:
            print("🔄 All terms have been used. Reset database? (y/n)")
            if input().lower().startswith('y'):
                reset_database()
                available_terms = terms[:count_needed]
    
    random.shuffle(available_terms)
    return available_terms

# Chrome Browser Management
def get_chrome_executable():
    """Find Chrome executable path."""
    chrome_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    return None

def open_chrome_with_profile(profile_folder, profile_name, url=None):
    """Open Chrome with specific profile."""
    try:
        chrome_exe = get_chrome_executable()
        if not chrome_exe:
            print("❌ Chrome executable not found")
            return False
        
        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(user_data_dir):
            user_data_dir = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\User Data"
        
        cmd = [
            chrome_exe,
            f"--user-data-dir={user_data_dir}",
            f"--profile-directory={profile_folder}",
            "--new-window"
        ]
        
        if url:
            cmd.append(url)
        else:
            cmd.append("https://www.bing.com")
        
        subprocess.Popen(cmd)
        time.sleep(2)
        logger.info(f"Opened Chrome with profile: {profile_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to open Chrome with profile: {e}")
        return False

def open_search_tabs_with_delays(terms, profile_folder, profile_name):
    """Open search tabs with human-like delays."""
    try:
        chrome_exe = get_chrome_executable()
        if not chrome_exe:
            return False
        
        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(user_data_dir):
            user_data_dir = f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Google\\Chrome\\User Data"
        
        print(f"🚀 Starting automated searches in Chrome profile: {profile_name}")
        print(f"📊 Total searches: {len(terms)}")
        print(f"⏱️  Delays: {config['search_delay_min']//60}-{config['search_delay_max']//60} minutes between searches")
        print("🎮 You can use your device freely during delays!\n")
        
        successful = 0
        
        for i, term in enumerate(terms, 1):
            try:
                # Create Bing search URL
                url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config['bing_market']}"
                
                print(f"🔍 [{i}/{len(terms)}] Searching: {term}")
                
                # Open new tab/window
                if i == 1:
                    cmd = [
                        chrome_exe,
                        f"--user-data-dir={user_data_dir}",
                        f"--profile-directory={profile_folder}",
                        "--new-window",
                        url
                    ]
                else:
                    cmd = [
                        chrome_exe,
                        f"--user-data-dir={user_data_dir}",
                        f"--profile-directory={profile_folder}",
                        "--new-tab",
                        url
                    ]
                
                subprocess.Popen(cmd)
                mark_used(term)
                successful += 1
                logger.info(f"[{i}/{len(terms)}] Searched: {term}")
                
                # Human-like delay between searches
                if i < len(terms):
                    delay = random.uniform(config['search_delay_min'], config['search_delay_max'])
                    minutes, seconds = int(delay // 60), int(delay % 60)
                    print(f"⏰ Waiting {minutes}m {seconds}s before next search...")
                    
                    # Show countdown every 30 seconds
                    remaining = int(delay)
                    while remaining > 0:
                        wait_time = min(30, remaining)
                        time.sleep(wait_time)
                        remaining -= wait_time
                        if remaining > 0:
                            mins, secs = remaining // 60, remaining % 60
                            print(f"  ⏳ {mins}m {secs}s remaining...")
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Graceful stop after {successful} searches")
                break
            except Exception as e:
                logger.error(f"Error searching '{term}': {e}")
                print(f"❌ Error searching '{term}': {e}")
                continue
        
        print(f"\n🎉 Completed: {successful}/{len(terms)} searches!")
        return True
        
    except Exception as e:
        logger.error(f"Error in automated searches: {e}")
        return False

# Main Application
def show_menu():
    """Display main menu."""
    print(BANNER)
    print(f"📊 Database Status: {get_used_count()} terms used")
    print(f"🔧 Config: {config['search_delay_min']//60}-{config['search_delay_max']//60} min delays, {config['bing_market']} market")
    
    print("\n🎯 Search Sources:")
    print("  1. Google News Headlines (Recommended - Fresh daily topics)")
    print("  2. Google Trends (Trending searches in India)")
    print("  3. Mixed Sources (News + Trends)")
    if GEMINI_AVAILABLE and config.get('gemini_api_key'):
        print("  4. Gemini AI Generated (Unique AI-generated topics)")
    
    print("\n🚀 Automation Methods:")
    print("  A. Automated with delays (Opens tabs automatically)")
    print("  B. Manual list (Just shows terms to search)")
    print("  C. Reset database (Mark all terms as unused)")
    print("  D. Exit")

def main():
    """Main application function."""
    try:
        init_database()
        
        while True:
            show_menu()
            
            # Get source choice
            max_source = 4 if (GEMINI_AVAILABLE and config.get('gemini_api_key')) else 3
            while True:
                try:
                    source = input(f"\nChoose search source (1-{max_source}) [1]: ").strip()
                    if not source:
                        source = "1"
                    source = int(source)
                    if 1 <= source <= max_source:
                        break
                    print(f"Please enter a number between 1 and {max_source}")
                except ValueError:
                    print("Please enter a valid number")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    return
            
            # Get automation method
            while True:
                try:
                    method = input("\nChoose method (A/B/C/D) [A]: ").strip().upper()
                    if not method:
                        method = "A"
                    if method in ['A', 'B', 'C', 'D']:
                        break
                    print("Please enter A, B, C, or D")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    return
            
            if method == 'D':
                print("👋 Goodbye!")
                break
            elif method == 'C':
                reset_database()
                continue
            
            # Get number of searches
            while True:
                try:
                    count = input(f"\nHow many searches? (5-{config['max_searches']}) [10]: ").strip()
                    if not count:
                        count = "10"
                    count = int(count)
                    if 5 <= count <= config['max_searches']:
                        break
                    print(f"Please enter a number between 5 and {config['max_searches']}")
                except ValueError:
                    print("Please enter a valid number")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    return
            
            # Get search terms
            search_terms = get_search_terms(source, count)
            if not search_terms:
                print("❌ No search terms available")
                continue
            
            terms_to_use = search_terms[:count]
            
            # Choose Chrome profile
            profile_folder, profile_name = choose_chrome_profile()
            if not profile_folder:
                print("❌ No Chrome profile selected")
                continue
            
            if method == 'A':
                # Automated method
                print(f"\n🤖 Starting automated searches...")
                success = open_search_tabs_with_delays(terms_to_use, profile_folder, profile_name)
                if success:
                    print("✅ Automation completed successfully!")
                else:
                    print("❌ Automation failed")
                
            elif method == 'B':
                # Manual method
                success = open_chrome_with_profile(profile_folder, profile_name)
                if success:
                    print(f"\n📋 Search these terms manually in Bing:")
                    for i, term in enumerate(terms_to_use, 1):
                        print(f"  {i}. {term}")
                        mark_used(term)
                    print(f"\n✅ {len(terms_to_use)} terms marked as used")
                    print("💡 Use 2-5 minute delays between manual searches")
                else:
                    print("❌ Failed to open Chrome")
            
            # Ask if user wants to continue
            if input("\nRun another session? (y/n) [n]: ").strip().lower() != 'y':
                break
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
    finally:
        logger.info("Script ended")
        print("\n👋 Done!")

if __name__ == "__main__":
    main()
