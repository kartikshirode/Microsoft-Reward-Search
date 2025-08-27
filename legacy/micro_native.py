import json
import random
import time
import sqlite3
import sys
import os
import subprocess
import webbrowser
from urllib.parse import quote_plus

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
    
    while True:
        try:
            choice = input(f"\nChoose profile (1-{len(profiles)}) [1]: ").strip()
            if not choice:
                choice = "1"
            choice = int(choice)
            
            if 1 <= choice <= len(profiles):
                return profiles[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(profiles)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def open_chrome_with_profile(profile_folder, profile_name):
    """Open Chrome with specific profile using system command."""
    try:
        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(user_data_dir):
            user_data_dir = "C:\\Users\\%s\\AppData\\Local\\Google\\Chrome\\User Data" % os.getenv('USERNAME')
        
        # Chrome executable paths
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
        ]
        
        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
        
        if not chrome_exe:
            print("❌ Chrome executable not found")
            return False
        
        # Build command
        cmd = [
            chrome_exe,
            f"--user-data-dir={user_data_dir}",
            f"--profile-directory={profile_folder}",
            "--new-window",
            "https://www.bing.com"
        ]
        
        print(f"🚀 Opening Chrome with profile: {profile_name}")
        subprocess.Popen(cmd)
        time.sleep(3)
        print("✅ Chrome opened with your profile!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to open Chrome with profile: {e}")
        return False

def open_bing_searches_in_tabs(terms, profile_folder, profile_name):
    """Open multiple Bing search tabs with specific profile."""
    try:
        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(user_data_dir):
            user_data_dir = "C:\\Users\\%s\\AppData\\Local\\Google\\Chrome\\User Data" % os.getenv('USERNAME')
        
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
        ]
        
        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
        
        if not chrome_exe:
            print("❌ Chrome executable not found")
            return False
        
        print(f"🚀 Opening {len(terms)} search tabs in Chrome profile: {profile_name}")
        
        # Create URLs for all searches
        urls = []
        for term in terms:
            url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config['bing_market']}"
            urls.append(url)
        
        # Open Chrome with first search
        cmd = [
            chrome_exe,
            f"--user-data-dir={user_data_dir}",
            f"--profile-directory={profile_folder}",
            "--new-window",
            urls[0]
        ]
        
        subprocess.Popen(cmd)
        time.sleep(3)
        print(f"✅ Opened first search: {terms[0]}")
        
        # Open additional tabs with delay
        for i, (term, url) in enumerate(zip(terms[1:], urls[1:]), 2):
            print(f"🔍 [{i}/{len(terms)}] Opening: {term}")
            
            # Open new tab
            cmd = [
                chrome_exe,
                f"--user-data-dir={user_data_dir}",
                f"--profile-directory={profile_folder}",
                "--new-tab",
                url
            ]
            
            subprocess.Popen(cmd)
            
            # Mark as used
            mark_used(term)
            
            # Human-like delay
            if i < len(terms):
                delay = random.uniform(config['delay_min'], config['delay_max'])
                minutes = int(delay // 60)
                print(f"⏰ Waiting {minutes} minutes before next search...")
                time.sleep(delay)
        
        # Mark first term as used too
        mark_used(terms[0])
        print(f"\n🎉 Opened all {len(terms)} searches in your Chrome profile!")
        return True
        
    except Exception as e:
        print(f"❌ Error opening search tabs: {e}")
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
        
        print("\nAutomation Method:")
        print("1. Open all searches in Chrome tabs with delays (Recommended)")
        print("2. Open just Bing and show search list (Manual)")
        
        method = int(input("Choose method (1-2) [1]: ") or "1")
        
        # Choose Chrome profile
        profile_folder, profile_name = choose_chrome_profile()
        if not profile_folder:
            print("❌ No profile selected")
            return
        
        terms_to_search = available_terms[:search_count]
        
        if method == 1:
            # Automated method with tabs and delays
            success = open_bing_searches_in_tabs(terms_to_search, profile_folder, profile_name)
            if success:
                print("\n✅ All searches opened in your Chrome profile!")
                print("💡 Each search will open with 2-5 minute delays")
                print("📱 You can use your device normally during delays")
        else:
            # Manual method
            success = open_chrome_with_profile(profile_folder, profile_name)
            if success:
                print(f"\n📋 Search these terms manually in Bing:")
                for i, term in enumerate(terms_to_search, 1):
                    print(f"{i}. {term}")
                    mark_used(term)
                print(f"\n✅ {search_count} terms marked as used in database")
                print("💡 Search them manually with 2-5 minute delays between searches")
        
        if not success:
            print("❌ Failed to open Chrome. Please check your Chrome installation.")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        print("\n👋 Done!")

if __name__ == "__main__":
    main()
