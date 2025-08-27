import json
import random
import time
import sqlite3
import sys
import os
import subprocess
from urllib.parse import quote_plus
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

print("🚀 BING AUTOMATION - YOUR CHROME PROFILE")
print("="*50)

# Simple config
config = {
    "delay_min": 120,
    "delay_max": 300,
    "bing_market": "en-IN"
}

# Database setup
db_file = 'used_terms.db'
conn = sqlite3.connect(db_file)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS used_terms (term TEXT PRIMARY KEY)')
conn.commit()
conn.close()

def is_used(term):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT 1 FROM used_terms WHERE term = ?', (term,))
    used = c.fetchone() is not None
    conn.close()
    return used

def mark_used(term):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO used_terms (term) VALUES (?)', (term,))
    conn.commit()
    conn.close()

def get_chrome_profiles():
    """Get available Chrome profiles."""
    try:
        # Common Chrome user data paths
        possible_paths = [
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data"),
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome Beta\\User Data"),
            "C:\\Users\\%s\\AppData\\Local\\Google\\Chrome\\User Data" % os.getenv('USERNAME')
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
                    # Try to get profile name from Preferences
                    pref_file = os.path.join(profile_path, "Preferences")
                    profile_name = item
                    try:
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
        print(f"Error finding Chrome profiles: {e}")
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
        print(f"{i}. {name} ({folder})")
    
    print(f"{len(profiles) + 1}. Use temporary profile (not recommended)")
    
    while True:
        try:
            choice = input(f"\nChoose profile (1-{len(profiles) + 1}) [1]: ").strip()
            if not choice:
                choice = "1"
            choice = int(choice)
            
            if 1 <= choice <= len(profiles):
                return profiles[choice - 1]
            elif choice == len(profiles) + 1:
                return None, None  # Temporary profile
            else:
                print(f"Please enter a number between 1 and {len(profiles) + 1}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def setup_browser_with_profile(profile_folder, profile_name):
    """Setup browser with specific Chrome profile."""
    print(f"\n🔧 Setting up browser...")
    
    options = uc.ChromeOptions()
    
    # Use existing profile if specified
    if profile_folder:
        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(user_data_dir):
            user_data_dir = "C:\\Users\\%s\\AppData\\Local\\Google\\Chrome\\User Data" % os.getenv('USERNAME')
        
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_folder}")
        print(f"📱 Using Chrome profile: {profile_name}")
    else:
        print("📱 Using temporary profile")
    
    # Anti-detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-web-security')
    
    # Always start with new window
    options.add_argument('--new-window')
    
    try:
        driver = uc.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Browser started with your profile!")
        return driver
    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return None

def open_bing_directly():
    """Alternative method - open Bing directly in existing Chrome."""
    try:
        print("\n🌐 Opening Bing in your existing Chrome...")
        subprocess.run(['start', 'chrome', 'https://www.bing.com'], shell=True)
        time.sleep(3)
        print("✅ Bing opened in Chrome!")
        return True
    except Exception as e:
        print(f"❌ Failed to open Bing: {e}")
        return False

# Search terms
search_terms = [
    "ChatGPT 2025", "AI tools", "iPhone 16", "Tesla news", "IPL 2025",
    "Budget 2025 India", "Space mission", "Climate change", "Netflix shows",
    "Bollywood movies", "Tech trends", "Electric cars", "Cricket news",
    "Stock market today", "Weather forecast", "Job opportunities", "Education tips",
    "Health tips", "Travel destinations", "Food recipes", "Gaming news",
    "Social media trends", "Fashion 2025", "Investment tips", "Sports updates"
]

def main():
    try:
        # Get search preferences
        random.shuffle(search_terms)
        available_terms = [t for t in search_terms if not is_used(t)]
        
        if not available_terms:
            print("ℹ️  No new terms to search. Resetting database...")
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute('DELETE FROM used_terms')
            conn.commit()
            conn.close()
            available_terms = search_terms[:15]
        
        print(f"\nAvailable searches: {len(available_terms)}")
        search_count = int(input("How many searches? (5-15) [10]: ") or "10")
        search_count = min(search_count, len(available_terms), 15)
        
        print("\nBrowser Method:")
        print("1. Use Selenium with your Chrome profile (Recommended)")
        print("2. Open Bing directly in existing Chrome (Manual searches)")
        
        method = int(input("Choose method (1-2) [1]: ") or "1")
        
        if method == 1:
            # Selenium method with profile
            profile_folder, profile_name = choose_chrome_profile()
            
            driver = setup_browser_with_profile(profile_folder, profile_name)
            if not driver:
                print("💥 Failed to start browser. Exiting...")
                return
            
            # Perform automated searches
            terms_to_search = available_terms[:search_count]
            print(f"\n🎯 Starting {search_count} automated searches...")
            print("Press Ctrl+C to stop\n")
            
            successful = 0
            try:
                for i, term in enumerate(terms_to_search, 1):
                    try:
                        # Open new tab for each search (except first)
                        if i > 1:
                            driver.execute_script("window.open('', '_blank');")
                            driver.switch_to.window(driver.window_handles[-1])
                        
                        # Search on Bing
                        url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config['bing_market']}"
                        print(f"🔍 [{i}/{search_count}] Searching: {term}")
                        
                        driver.get(url)
                        time.sleep(random.uniform(5, 12))  # Human-like wait
                        
                        mark_used(term)
                        successful += 1
                        
                        # Wait between searches
                        if i < search_count:
                            delay = random.uniform(config['delay_min'], config['delay_max'])
                            minutes = int(delay // 60)
                            print(f"⏰ Waiting {minutes} minutes...")
                            time.sleep(delay)
                            
                    except KeyboardInterrupt:
                        print(f"\n⏹️  Stopped after {successful} searches")
                        break
                    except Exception as e:
                        print(f"❌ Error searching '{term}': {e}")
                        continue
            
            except KeyboardInterrupt:
                print(f"\n⏹️  Cancelled after {successful} searches")
            
            print(f"\n🎉 Completed: {successful}/{search_count} searches!")
            
            # Keep browser open option
            keep = input("\nKeep browser tabs open? (y/n) [y]: ").strip().lower()
            if keep != 'n':
                print("🌐 Browser tabs left open for you to review")
            else:
                driver.quit()
                print("🔒 Browser closed")
        
        else:
            # Manual method - just open Bing
            if open_bing_directly():
                print(f"\n📋 Search these terms manually in Bing:")
                for i, term in enumerate(available_terms[:search_count], 1):
                    print(f"{i}. {term}")
                    mark_used(term)
                print(f"\n✅ {search_count} terms marked as used in database")
                print("💡 Search them manually with 2-5 minute delays between searches")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        print("\n👋 Done!")

if __name__ == "__main__":
    main()
