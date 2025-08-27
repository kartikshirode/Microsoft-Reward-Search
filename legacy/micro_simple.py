import json
import random
import time
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from urllib.parse import quote_plus
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys
import requests
from bs4 import BeautifulSoup
import feedparser
from fake_useragent import UserAgent

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Configure logging
log_file = config.get('log_file', 'bing_search.log')
max_bytes = config.get('log_max_bytes', 1048576)
backup_count = config.get('log_backup_count', 5)
logger = logging.getLogger('bing_search')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Initialize SQLite DB
db_file = config.get('db_file', 'used_terms.db')
conn = sqlite3.connect(db_file)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS used_terms (term TEXT PRIMARY KEY)')
conn.commit()
conn.close()

def check_chrome_windows():
    """Simple check for Chrome windows using PowerShell."""
    try:
        import subprocess
        result = subprocess.run([
            'powershell', '-Command',
            "Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object Id, MainWindowTitle"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            # Skip header lines and count actual windows
            actual_lines = [line for line in lines[2:] if line.strip() and not line.startswith('---')]
            return len(actual_lines) if actual_lines else 0
        return 0
    except Exception as e:
        logger.warning(f"Error checking Chrome windows: {e}")
        return 0

def get_browser_choice():
    """Simplified browser choice with better Chrome profile handling."""
    print("\n" + "="*60)
    print("BING SEARCH AUTOMATION - CHROME & BING FOCUSED")
    print("="*60)
    
    chrome_count = check_chrome_windows()
    
    print("\nBrowser Options:")
    if chrome_count > 0:
        print(f"1. Try to use existing Chrome ({chrome_count} window{'s' if chrome_count > 1 else ''} detected)")
        print("   ⚠️  Note: May open new window due to Chrome profiles/security")
    else:
        print("1. Use existing Chrome (no windows detected)")
    
    print("2. Open new Chrome window (Recommended)")
    print("3. Open new Edge window")
    print("4. Exit")
    
    while True:
        try:
            choice = input(f"\nEnter your choice (1-4) [Recommended: 2]: ").strip()
            if not choice:
                choice = "2"  # Default to new Chrome
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("Please enter a valid choice (1-4)")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_operation_mode():
    """Operation mode selection."""
    print("\nOperation Mode:")
    print("1. Interactive Mode - Visible browser (❌ cannot use device freely)")
    print("2. Background Mode - Minimized browser (✅ can use device freely)")
    print("3. Headless Mode - Hidden browser (✅ can use device freely)")
    
    while True:
        try:
            choice = input("\nEnter operation mode (1-3) [Recommended: 2]: ").strip()
            if not choice:
                choice = "2"  # Default to background
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Please enter a valid choice (1-3)")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_search_source():
    """Search source selection."""
    print("\nSearch Terms Source:")
    print("1. Google Trends")
    print("2. Google News Headlines (Recommended)")
    print("3. Mixed Sources")
    
    while True:
        try:
            choice = input("\nEnter source choice (1-3) [Recommended: 2]: ").strip()
            if not choice:
                choice = "2"  # Default to Google News
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Please enter a valid choice (1-3)")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_search_count():
    """Number of searches."""
    while True:
        try:
            count = input(f"\nHow many searches? (10-20) [Default: 15]: ").strip()
            if not count:
                return 15
            count = int(count)
            if 10 <= count <= 20:
                return count
            else:
                print("Please enter a number between 10 and 20")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def is_used(term):
    """Check if term already used."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT 1 FROM used_terms WHERE term = ?', (term,))
    used = c.fetchone() is not None
    conn.close()
    return used

def mark_used(term):
    """Mark term as used."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO used_terms (term) VALUES (?)', (term,))
    conn.commit()
    conn.close()

def get_google_news_headlines():
    """Fetch Google News headlines."""
    try:
        headlines = []
        news_feeds = [
            "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen",
        ]
        
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        for feed_url in news_feeds:
            try:
                response = requests.get(feed_url, headers=headers, timeout=10)
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:10]:
                    title = entry.title.strip()
                    if ' - ' in title:
                        title = title.split(' - ')[0]
                    if len(title) > 70:
                        title = title[:70] + "..."
                    headlines.append(title)
            except Exception as e:
                logger.warning(f"Failed to fetch from feed: {e}")
                continue
        
        headlines = list(set(headlines))
        random.shuffle(headlines)
        logger.info(f"Fetched {len(headlines)} headlines from Google News")
        return headlines[:20]
        
    except Exception as e:
        logger.error(f"Failed to retrieve Google News: {e}")
        return []

def get_fallback_topics():
    """Fallback topics."""
    topics = [
        "ChatGPT latest features", "AI tools 2025", "iPhone 16 review", "Tesla stock",
        "IPL 2025", "Lok Sabha elections", "ISRO mission", "Budget 2025 India",
        "Bollywood new movies", "Netflix releases", "Cricket World Cup", "Olympics",
        "Climate change", "Electric cars India", "Space news", "Tech trends 2025"
    ]
    random.shuffle(topics)
    return topics

def get_search_terms(source_choice, count_needed):
    """Get search terms based on source."""
    terms = []
    
    if source_choice == 1:  # Google Trends
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl=config['hl'], tz=config['tz'], geo=config['geo'])
            df = pytrends.trending_searches(pn='india')
            trends = df.iloc[:, 0].tolist()
            terms.extend(trends)
            logger.info(f"Fetched {len(trends)} terms from Google Trends")
        except Exception as e:
            logger.error(f"Google Trends failed: {e}")
            
    elif source_choice == 2:  # Google News
        news_headlines = get_google_news_headlines()
        terms.extend(news_headlines)
        
    elif source_choice == 3:  # Mixed
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl=config['hl'], tz=config['tz'], geo=config['geo'])
            df = pytrends.trending_searches(pn='india')
            trends = df.iloc[:, 0].tolist()
            terms.extend(trends[:8])
        except:
            pass
        news_headlines = get_google_news_headlines()
        terms.extend(news_headlines[:12])
    
    if len(terms) < count_needed:
        fallback = get_fallback_topics()
        terms.extend(fallback)
    
    terms = list(set(terms))
    random.shuffle(terms)
    return terms

def setup_browser(browser_choice, operation_mode):
    """Setup browser - simplified and more reliable."""
    print(f"\n🔧 Setting up browser...")
    
    # Always create new browser instance for reliability
    # Chrome profiles and security make existing connection unreliable
    if browser_choice == 1:
        print("⚠️  Note: Creating new Chrome window for reliability")
        print("   (Chrome profiles/security prevent reliable existing window connection)")
    
    options = uc.ChromeOptions()
    
    # Use realistic user agent
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    
    # Anti-detection options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-web-security')
    
    # Configure based on operation mode
    if operation_mode == 1:  # Interactive
        options.add_argument('--start-maximized')
        print("📱 Interactive Mode: Browser will be visible")
    elif operation_mode == 2:  # Background
        options.add_argument('--start-minimized')
        print("🔇 Background Mode: Browser minimized (✅ you can use device freely)")
    elif operation_mode == 3:  # Headless
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        print("👻 Headless Mode: Browser hidden (✅ you can use device freely)")
    
    # Browser selection
    if browser_choice == 3:  # Edge
        try:
            edge_paths = [
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
            ]
            for path in edge_paths:
                try:
                    options.binary_location = path
                    print("Using Microsoft Edge browser")
                    break
                except:
                    continue
            else:
                print("Edge not found, using Chrome instead")
        except:
            print("Using Chrome instead of Edge")
    else:
        print("Using Google Chrome browser")
    
    try:
        driver = uc.Chrome(options=options)
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info(f"Browser setup successful - Choice: {browser_choice}, Mode: {operation_mode}")
        print("✅ Browser started successfully!")
        return driver
    except Exception as e:
        logger.error(f"Failed to setup browser: {e}")
        print(f"❌ Browser setup failed: {e}")
        return None

def human_like_scroll(driver):
    """Human-like scrolling."""
    try:
        for _ in range(random.randint(1, 3)):
            scroll_pixels = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            time.sleep(random.uniform(1, 3))
        
        if random.random() < 0.3:
            scroll_pixels = random.randint(200, 500)
            driver.execute_script(f"window.scrollBy(0, -{scroll_pixels});")
            time.sleep(random.uniform(1, 2))
    except Exception as e:
        logger.warning(f"Scrolling error: {e}")

def human_like_interaction(driver, operation_mode):
    """Human-like page interactions."""
    try:
        WebDriverWait(driver, 10).wait(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(random.uniform(3, 8))
        
        if operation_mode == 1:  # Interactive only
            human_like_scroll(driver)
            
            if random.random() < 0.3:  # 30% chance to click result
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, "h2 a, .b_algo h2 a")
                    if results and len(results) > 1:
                        result = random.choice(results[1:min(5, len(results))])
                        result.click()
                        logger.info("Clicked search result")
                        time.sleep(random.uniform(5, 15))
                        driver.back()
                        time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Click error: {e}")
        else:
            time.sleep(random.uniform(5, 12))
            logger.info("Background mode: Basic page load")
    except Exception as e:
        logger.warning(f"Interaction error: {e}")

def perform_search(driver, term, search_count, total_searches, operation_mode):
    """Perform single search."""
    try:
        if search_count > 1:
            driver.execute_script("window.open('', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
        
        bing_url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config.get('bing_market','en-IN')}"
        
        print(f"\n🔍 [{search_count}/{total_searches}] Searching: {term}")
        logger.info(f"[{search_count}/{total_searches}] Search: {term}")
        
        driver.get(bing_url)
        human_like_interaction(driver, operation_mode)
        
        mark_used(term)
        logger.info(f"Completed search: {term}")
        return True
        
    except Exception as e:
        logger.error(f"Search error for '{term}': {e}")
        print(f"❌ Error searching '{term}': {e}")
        return False

def calculate_delay(search_count, total_searches):
    """Calculate human-like delay."""
    base_delay = random.uniform(120, 300)  # 2-5 minutes
    
    if search_count > total_searches * 0.7:
        base_delay *= random.uniform(1.2, 1.5)  # Slower towards end
    
    variation = random.uniform(0.8, 1.3)
    return max(base_delay * variation, 60)  # Min 1 minute

def main():
    """Main function."""
    try:
        print("🚀 Starting Bing Search Automation...")
        
        browser_choice = get_browser_choice()
        if browser_choice == 4:
            print("👋 Goodbye!")
            return
            
        operation_mode = get_operation_mode()
        source_choice = get_search_source()
        search_count_desired = get_search_count()
        
        mode_names = {1: "Interactive", 2: "Background", 3: "Headless"}
        source_names = {1: "Google Trends", 2: "Google News", 3: "Mixed Sources"}
        browser_names = {1: "Existing Chrome", 2: "New Chrome", 3: "New Edge"}
        
        print(f"\n📋 Configuration Summary:")
        print(f"- Browser: {browser_names[browser_choice]}")
        print(f"- Mode: {mode_names[operation_mode]}")
        print(f"- Source: {source_names[source_choice]}")
        print(f"- Searches: {search_count_desired}")
        print(f"- Delays: 2-5 minutes between searches")
        if operation_mode in [2, 3]:
            print("- ✅ You can use your device freely!")
        else:
            print("- ❌ Avoid using device during searches")
        
        confirm = input("\nProceed? (y/n) [y]: ").strip().lower()
        if confirm and confirm != 'y':
            print("👋 Cancelled")
            return
        
        driver = setup_browser(browser_choice, operation_mode)
        if not driver:
            print("💥 Failed to start browser. Exiting...")
            return
        
        print(f"📰 Getting search terms from {source_names[source_choice]}...")
        terms = get_search_terms(source_choice, search_count_desired + 3)
        
        available_terms = [t for t in terms if not is_used(t)]
        
        if len(available_terms) < search_count_desired:
            print(f"⚠️  Only {len(available_terms)} unused terms available")
            search_count_desired = min(search_count_desired, len(available_terms))
        
        if search_count_desired == 0:
            print("ℹ️  No new terms to search")
            driver.quit()
            return
        
        search_terms = available_terms[:search_count_desired]
        
        print(f"\n🎯 Starting {search_count_desired} searches...")
        print("Press Ctrl+C to stop gracefully\n")
        
        successful_searches = 0
        for i, term in enumerate(search_terms, 1):
            try:
                if perform_search(driver, term, i, search_count_desired, operation_mode):
                    successful_searches += 1
                
                if i < search_count_desired:
                    delay = calculate_delay(i, search_count_desired)
                    minutes, seconds = int(delay // 60), int(delay % 60)
                    print(f"⏰ Waiting {minutes}m {seconds}s...")
                    
                    # Progress updates every 30 seconds
                    for remaining in range(int(delay), 0, -30):
                        if remaining <= 30:
                            time.sleep(remaining)
                            break
                        time.sleep(30)
                        mins, secs = remaining // 60, remaining % 60
                        print(f"  ⏳ {mins}m {secs}s remaining...")
                        
            except KeyboardInterrupt:
                print(f"\n\n⏹️  Graceful stop after {successful_searches} searches")
                break
            except Exception as e:
                logger.error(f"Unexpected error in search {i}: {e}")
                print(f"❌ Error in search {i}, continuing...")
        
        print(f"\n🎉 Completed: {successful_searches}/{search_count_desired} searches successful!")
        
        # Cleanup
        try:
            if operation_mode == 1:  # Interactive
                keep_open = input("\nKeep browser open? (y/n) [n]: ").strip().lower()
                if keep_open == 'y':
                    print("🌐 Browser left open")
                else:
                    driver.quit()
                    print("🔒 Browser closed")
            else:
                driver.quit()
                print("🔒 Browser closed automatically")
        except:
            pass
            
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
