import json
import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from urllib.parse import quote_plus
import sqlite3
import sys

print("🚀 SIMPLE BING AUTOMATION - JUST WORKS!")
print("="*50)

# Simple config
config = {
    "delay_min": 120,
    "delay_max": 300,
    "bing_market": "en-IN"
}

# Simple database
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

# Simple search terms
search_terms = [
    "ChatGPT 2025", "AI tools", "iPhone 16", "Tesla news", "IPL 2025",
    "Budget 2025 India", "Space mission", "Climate change", "Netflix shows",
    "Bollywood movies", "Tech trends", "Electric cars", "Cricket news",
    "Stock market", "Weather forecast", "Job opportunities", "Education",
    "Health tips", "Travel destinations", "Food recipes", "Gaming news",
    "Social media trends", "Fashion 2025", "Investment tips", "Sports news"
]

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

# Get user input
print(f"\nAvailable searches: {len(available_terms)}")
search_count = int(input("How many searches? (5-15) [10]: ") or "10")
search_count = min(search_count, len(available_terms), 15)

print("\nMode:")
print("1. Visible browser (❌ cannot use device)")
print("2. Minimized browser (✅ can use device)")
print("3. Hidden browser (✅ can use device)")

mode = int(input("Choose mode (1-3) [2]: ") or "2")

print(f"\n🔧 Starting browser...")

# Setup browser
options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')

if mode == 1:
    options.add_argument('--start-maximized')
    print("📱 Visible mode")
elif mode == 2:
    options.add_argument('--start-minimized')
    print("🔇 Minimized mode - you can use device freely!")
else:
    options.add_argument('--headless')
    print("👻 Hidden mode - you can use device freely!")

try:
    driver = uc.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✅ Browser started!")
except Exception as e:
    print(f"❌ Browser failed: {e}")
    sys.exit(1)

# Perform searches
terms_to_search = available_terms[:search_count]
print(f"\n🎯 Starting {search_count} searches...")
print("Press Ctrl+C to stop\n")

successful = 0
try:
    for i, term in enumerate(terms_to_search, 1):
        try:
            # Open new tab (except first search)
            if i > 1:
                driver.execute_script("window.open('', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
            
            # Search
            url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config['bing_market']}"
            print(f"🔍 [{i}/{search_count}] {term}")
            
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
            print(f"❌ Error: {e}")
            continue

except KeyboardInterrupt:
    print(f"\n⏹️  Cancelled after {successful} searches")

print(f"\n🎉 Completed: {successful}/{search_count} searches!")

if mode == 1:
    keep = input("\nKeep browser open? (y/n) [n]: ").strip().lower()
    if keep != 'y':
        driver.quit()
        print("🔒 Browser closed")
else:
    driver.quit()
    print("🔒 Browser closed")

print("👋 Done!")
