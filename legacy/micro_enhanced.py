import json
import random
import time
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from urllib.parse import quote_plus
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys
import requests
from bs4 import BeautifulSoup
import feedparser
from fake_useragent import UserAgent

# Optional Gemini AI import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Configure logging (rotating file)
log_file = config.get('log_file', 'bing_search.log')
max_bytes = config.get('log_max_bytes', 1048576)
backup_count = config.get('log_backup_count', 5)
logger = logging.getLogger('bing_search')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Initialize SQLite DB to store used search terms
db_file = config.get('db_file', 'used_terms.db')
conn = sqlite3.connect(db_file)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS used_terms (term TEXT PRIMARY KEY)')
conn.commit()
conn.close()

def get_browser_choice():
    """Ask user for browser preference."""
    print("\n" + "="*60)
    print("ENHANCED BING SEARCH AUTOMATION - GOOGLE NEWS INTEGRATION")
    print("="*60)
    print("\nBrowser Options:")
    print("1. Use existing browser window (if open)")
    print("2. Open new Chrome window")
    print("3. Open new Edge window")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("Please enter a valid choice (1-4)")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_operation_mode():
    """Ask user for operation mode preference."""
    print("\nOperation Mode:")
    print("1. Interactive Mode - Visible browser with interactions (you cannot use device freely)")
    print("2. Background Mode - Minimized browser, basic searches only (you can use device freely)")
    print("3. Headless Mode - Completely hidden browser (you can use device freely)")
    
    while True:
        try:
            choice = input("\nEnter operation mode (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("Please enter a valid choice (1-3)")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_search_source():
    """Ask user for search term source preference."""
    print("\nSearch Terms Source:")
    print("1. Google Trends (Traditional)")
    print("2. Google News Headlines (Fresh & Diverse)")
    print("3. Mixed Sources (Google News + Trends)")
    if GEMINI_AVAILABLE:
        print("4. Gemini AI Generated Topics (Most Diverse)")
    
    while True:
        try:
            max_choice = 4 if GEMINI_AVAILABLE else 3
            choice = input(f"\nEnter source choice (1-{max_choice}): ").strip()
            if choice in [str(i) for i in range(1, max_choice + 1)]:
                return int(choice)
            else:
                print(f"Please enter a valid choice (1-{max_choice})")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def get_search_count():
    """Ask user for number of searches."""
    while True:
        try:
            count = input(f"\nHow many searches do you want to perform? (10-20, default: {config.get('max_searches', 15)}): ").strip()
            if not count:
                return config.get('max_searches', 15)
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
    """Check if a search term is already used (in the SQLite DB)."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT 1 FROM used_terms WHERE term = ?', (term,))
    used = c.fetchone() is not None
    conn.close()
    return used

def mark_used(term):
    """Mark a term as used by inserting it into the SQLite DB."""
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO used_terms (term) VALUES (?)', (term,))
    conn.commit()
    conn.close()

def get_google_news_headlines():
    """Fetch fresh headlines from Google News RSS feeds."""
    try:
        headlines = []
        
        # Google News RSS feeds for different categories
        news_feeds = [
            "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",  # Top stories India
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen",  # Technology
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREZqY0hsUUFTZ0FCaTVJQ0NRQUFB?hl=en-IN&gl=IN&ceid=IN%3Aen",  # Sports
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen",  # Business
        ]
        
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        
        for feed_url in news_feeds:
            try:
                response = requests.get(feed_url, headers=headers, timeout=10)
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:8]:  # Get top 8 from each category
                    title = entry.title.strip()
                    # Clean up the title
                    if ' - ' in title:
                        title = title.split(' - ')[0]  # Remove source attribution
                    if len(title) > 80:
                        title = title[:80] + "..."
                    headlines.append(title)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from feed {feed_url}: {e}")
                continue
        
        # Remove duplicates and shuffle
        headlines = list(set(headlines))
        random.shuffle(headlines)
        
        logger.info(f"Fetched {len(headlines)} headlines from Google News")
        return headlines[:25]  # Return top 25
        
    except Exception as e:
        logger.error(f"Failed to retrieve Google News: {e}")
        return []

def get_trending_topics_fallback():
    """Enhanced fallback list with more diverse topics."""
    topics = [
        # Technology & AI
        "ChatGPT latest updates", "AI tools 2025", "Tesla stock news", "iPhone 16 features",
        "Microsoft Copilot", "Google Bard updates", "Cryptocurrency trends", "Bitcoin price",
        
        # Indian Topics
        "IPL 2025 schedule", "Lok Sabha elections", "ISRO missions", "Budget India 2025",
        "Digital India progress", "UPI payment growth", "Make in India", "Startup India",
        
        # Entertainment & Sports
        "Bollywood movies 2025", "Netflix new releases", "FIFA World Cup", "Olympics 2024",
        "Indian cricket team", "Premier League updates", "Marvel new movies", "Music albums 2025",
        
        # Current Affairs
        "Climate change initiatives", "Electric vehicles India", "Space exploration news",
        "Renewable energy projects", "Education policy India", "Healthcare reforms",
        
        # Global Topics
        "World economy 2025", "International relations", "Travel destinations 2025",
        "Food trends", "Fashion week", "Technology conferences", "Innovation summit"
    ]
    random.shuffle(topics)
    return topics

def get_gemini_generated_topics(count=20):
    """Generate diverse search topics using Gemini AI."""
    if not GEMINI_AVAILABLE:
        return []
    
    try:
        # Configure Gemini (user needs to set API key in config)
        api_key = config.get('gemini_api_key')
        if not api_key:
            print("⚠️  Gemini API key not found in config.json. Add 'gemini_api_key' to use AI generation.")
            return []
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""Generate {count} diverse, trending search topics that a curious person in India might search for on Bing in 2025. 
        Include mix of:
        - Current technology trends
        - Indian current affairs 
        - Global news topics
        - Entertainment and sports
        - Educational topics
        - Lifestyle and health
        
        Make them realistic, specific, and varied. Return only the search terms, one per line, without numbering."""
        
        response = model.generate_content(prompt)
        topics = [line.strip() for line in response.text.split('\n') if line.strip()]
        
        logger.info(f"Generated {len(topics)} topics using Gemini AI")
        return topics[:count]
        
    except Exception as e:
        logger.error(f"Failed to generate topics with Gemini: {e}")
        return []

def get_search_terms(source_choice, count_needed):
    """Get search terms based on user's source choice."""
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
        
    elif source_choice == 3:  # Mixed Sources
        # Get from both sources
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl=config['hl'], tz=config['tz'], geo=config['geo'])
            df = pytrends.trending_searches(pn='india')
            trends = df.iloc[:, 0].tolist()
            terms.extend(trends[:10])
        except Exception as e:
            logger.error(f"Google Trends failed: {e}")
            
        news_headlines = get_google_news_headlines()
        terms.extend(news_headlines[:15])
        
    elif source_choice == 4 and GEMINI_AVAILABLE:  # Gemini AI
        ai_topics = get_gemini_generated_topics(count_needed + 5)
        terms.extend(ai_topics)
    
    # Add fallback topics if needed
    if len(terms) < count_needed:
        fallback = get_trending_topics_fallback()
        terms.extend(fallback)
    
    # Remove duplicates and shuffle
    terms = list(set(terms))
    random.shuffle(terms)
    
    logger.info(f"Total terms collected: {len(terms)}")
    return terms

def setup_browser(browser_choice, operation_mode):
    """Setup browser based on user choice and operation mode."""
    options = uc.ChromeOptions()
    
    # Enhanced user agent rotation
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    
    # Additional options for human-like behavior
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    
    # Configure based on operation mode
    if operation_mode == 1:  # Interactive Mode
        options.add_argument('--start-maximized')
        print("📱 Interactive Mode: Browser will be visible and active")
    elif operation_mode == 2:  # Background Mode
        options.add_argument('--start-minimized')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        print("🔇 Background Mode: Browser will be minimized (you can use your device freely)")
    elif operation_mode == 3:  # Headless Mode
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        print("👻 Headless Mode: Browser will be completely hidden (you can use your device freely)")
    
    # Browser-specific settings
    if browser_choice == 3:  # Edge
        try:
            options.binary_location = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            print("Using Microsoft Edge browser")
        except:
            print("Edge not found, using Chrome instead")
    else:
        print("Using Google Chrome browser")
    
    try:
        driver = uc.Chrome(options=options)
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info(f"Browser setup successful with choice {browser_choice}, mode {operation_mode}")
        return driver, operation_mode
    except Exception as e:
        logger.error(f"Failed to setup browser: {e}")
        return None, operation_mode

def human_like_scroll(driver):
    """Perform human-like scrolling on the page."""
    try:
        scroll_actions = random.randint(1, 3)
        for _ in range(scroll_actions):
            scroll_pixels = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            time.sleep(random.uniform(
                config.get('scroll_delay_min', 1), 
                config.get('scroll_delay_max', 3)
            ))
            
        if random.random() < 0.3:
            scroll_pixels = random.randint(200, 500)
            driver.execute_script(f"window.scrollBy(0, -{scroll_pixels});")
            time.sleep(random.uniform(1, 2))
            
    except Exception as e:
        logger.warning(f"Error during scrolling: {e}")

def human_like_page_interaction(driver, operation_mode):
    """Perform human-like interactions on the search results page."""
    try:
        WebDriverWait(driver, 10).wait(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        time.sleep(random.uniform(
            config.get('page_interaction_delay_min', 3),
            config.get('page_interaction_delay_max', 8)
        ))
        
        if operation_mode == 1:  # Interactive Mode only
            human_like_scroll(driver)
            
            if random.random() < 0.3:
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, "h2 a, .b_algo h2 a")
                    if results and len(results) > 1:
                        result_to_click = random.choice(results[1:min(5, len(results))])
                        result_to_click.click()
                        logger.info("Clicked on a search result")
                        
                        time.sleep(random.uniform(5, 15))
                        driver.back()
                        time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Error clicking search result: {e}")
        else:
            time.sleep(random.uniform(5, 12))
            logger.info("Background mode: Page loaded without visual interactions")
                
    except TimeoutException:
        logger.warning("Page load timeout during interaction")
    except Exception as e:
        logger.warning(f"Error during page interaction: {e}")

def perform_search(driver, term, search_count, total_searches, operation_mode):
    """Perform a single search with human-like behavior."""
    try:
        if search_count > 1:
            driver.execute_script("window.open('', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
        
        bing_url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config.get('bing_market','en-IN')}"
        
        print(f"\n🔍 [{search_count}/{total_searches}] Searching for: {term}")
        logger.info(f"[{search_count}/{total_searches}] Starting search for: {term}")
        
        driver.get(bing_url)
        human_like_page_interaction(driver, operation_mode)
        
        mark_used(term)
        logger.info(f"Successfully completed search for: {term}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during search for '{term}': {e}")
        return False

def calculate_delay(search_count, total_searches):
    """Calculate delay with human-like variations."""
    base_delay = random.uniform(
        config.get('search_delay_min', 120), 
        config.get('search_delay_max', 300)
    )
    
    if search_count > total_searches * 0.7:
        base_delay *= random.uniform(1.2, 1.5)
    
    variation = random.uniform(0.8, 1.3)
    final_delay = base_delay * variation
    
    return max(final_delay, 60)

def main():
    """Enhanced main function with Google News integration."""
    try:
        browser_choice = get_browser_choice()
        if browser_choice == 4:
            print("Exiting...")
            return
            
        operation_mode = get_operation_mode()
        source_choice = get_search_source()
        search_count_desired = get_search_count()
        
        mode_names = {1: "Interactive", 2: "Background", 3: "Headless"}
        source_names = {1: "Google Trends", 2: "Google News", 3: "Mixed Sources", 4: "Gemini AI"}
        device_usage = {1: "❌ Cannot use device freely", 2: "✅ Can use device freely", 3: "✅ Can use device freely"}
        
        print(f"\n📋 Setup Summary:")
        print(f"- Browser: {'Chrome/Edge' if browser_choice <= 3 else 'Unknown'}")
        print(f"- Operation Mode: {mode_names[operation_mode]}")
        print(f"- Device Usage: {device_usage[operation_mode]}")
        print(f"- Search Source: {source_names.get(source_choice, 'Unknown')}")
        print(f"- Number of searches: {search_count_desired}")
        print(f"- Delay between searches: {config.get('search_delay_min', 120)}-{config.get('search_delay_max', 300)} seconds")
        
        confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return
        
        print("\n🔧 Setting up browser...")
        driver, operation_mode = setup_browser(browser_choice, operation_mode)
        if not driver:
            print("Failed to setup browser. Exiting...")
            return
        
        print(f"📰 Fetching search terms from {source_names.get(source_choice, 'Unknown')}...")
        terms = get_search_terms(source_choice, search_count_desired + 5)
        
        available_terms = [t for t in terms if not is_used(t)]
        
        if len(available_terms) < search_count_desired:
            print(f"⚠️  Warning: Only {len(available_terms)} unused terms available.")
            search_count_desired = min(search_count_desired, len(available_terms))
        
        if search_count_desired == 0:
            print("No new terms to search. Exiting.")
            driver.quit()
            return
        
        search_terms = available_terms[:search_count_desired]
        
        print(f"\n🚀 Starting {search_count_desired} searches...")
        if operation_mode in [2, 3]:
            print("✅ You can now use your device freely - the browser will run in the background!")
        else:
            print("❌ Please avoid using your device while searches are running")
        print("Press Ctrl+C to stop gracefully\n")
        
        successful_searches = 0
        for i, term in enumerate(search_terms, 1):
            try:
                if perform_search(driver, term, i, search_count_desired, operation_mode):
                    successful_searches += 1
                
                if i < search_count_desired:
                    delay = calculate_delay(i, search_count_desired)
                    minutes = int(delay // 60)
                    seconds = int(delay % 60)
                    print(f"⏰ Waiting {minutes}m {seconds}s before next search...")
                    
                    for remaining in range(int(delay), 0, -30):
                        if remaining <= 30:
                            time.sleep(remaining)
                            break
                        time.sleep(30)
                        print(f"  ⏳ {remaining // 60}m {remaining % 60}s remaining...")
                        
            except KeyboardInterrupt:
                print(f"\n\n⏹️  Gracefully stopping after {successful_searches} successful searches...")
                break
            except Exception as e:
                logger.error(f"Unexpected error during search {i}: {e}")
                print(f"❌ Error during search {i}, continuing...")
        
        print(f"\n\n🎉 Completed! {successful_searches} successful searches out of {search_count_desired} planned.")
        
        if operation_mode == 1:
            keep_open = input("\nKeep browser window open? (y/n): ").strip().lower()
            if keep_open != 'y':
                driver.quit()
                print("Browser closed.")
            else:
                print("Browser window left open. Close manually when done.")
        else:
            driver.quit()
            print("Background browser closed automatically.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user.")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"💥 Fatal error: {e}")
    finally:
        logger.info("Script execution ended")

if __name__ == "__main__":
    main()
