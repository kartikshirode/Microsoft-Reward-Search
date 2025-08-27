import json
import random
import time
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from urllib.parse import quote_plus
from pytrends.request import TrendReq
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys

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
    print("\n" + "="*50)
    print("BING SEARCH AUTOMATION - HUMAN-LIKE BEHAVIOR")
    print("="*50)
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

def get_trending_terms():
    """Fetch trending search terms for India using Google Trends.
       Falls back to a preset list if the API call fails."""
    try:
        pytrends = TrendReq(hl=config['hl'], tz=config['tz'], geo=config['geo'])
        # 'india' is the correct region code for trending_searches
        df = pytrends.trending_searches(pn='india')
        # The DataFrame returns one column of terms—grab them as a list
        terms = df.iloc[:, 0].tolist()
        random.shuffle(terms)
        logger.info(f"Fetched {len(terms)} trending terms from Google Trends")
        return terms
    except Exception as e:
        logger.error(f"Failed to retrieve Google Trends: {e}")
        # Fallback list of popular India-centric terms
        fallback = [
            "IPL 2025", "Lok Sabha", "ISRO", "Budget India 2025",
            "RBI", "Startup India", "Kohli century", "Indian Railways"
        ]
        random.shuffle(fallback)
        logger.info("Using fallback trending terms")
        return fallback

def worker():
    """Worker thread: takes search terms from queue and performs a Bing search."""
    while not stop_event.is_set():
        try:
            term = search_queue.get(timeout=1)
        except queue.Empty:
            return

        if is_used(term):
            search_queue.task_done()
            continue

        success = False
        for attempt in range(config.get('retry_max', 3)):
            try:
                # Rotate user-agent & proxy
                ua = random.choice(config['user_agents'])
                proxy = random.choice(config['proxies'])
                options = uc.ChromeOptions()
                options.add_argument(f'user-agent={ua}')
                options.add_argument(f'--proxy-server={proxy}')
                # options.add_argument('--headless')  # optional
                driver = uc.Chrome(options=options)

                # Perform the search
                bing_url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config.get('bing_market','en-IN')}"
                driver.get(bing_url)
                time.sleep(random.uniform(config['search_delay_min'], config['search_delay_max']))

                # Clean shutdown of the browser
                driver.quit()
                # Prevent the destructor from calling quit() again on an invalid handle
                driver.quit = lambda *args, **kwargs: None

                success = True
                break

            except Exception as e:
                logger.error(f"Error searching “{term}” (attempt {attempt+1}): {e}")
                backoff = (2 ** attempt) * config.get('backoff_factor', 1)
                time.sleep(backoff)

        if success:
            mark_used(term)
            logger.info(f"Searched term: {term}")
        else:
            logger.warning(f"Giving up on term after retries: {term}")

        search_queue.task_done()


def main():
    # Load trending terms and enqueue new ones
    terms = get_trending_terms()
    for t in terms:
        if not is_used(t):
            search_queue.put(t)
    if search_queue.empty():
        logger.info("No new trending terms to search. Exiting.")
        return

    # Start worker threads
    threads = []
    for i in range(config.get('max_threads', 5)):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)
    logger.info(f"Started {len(threads)} worker threads.")

    # Wait for threads or handle Ctrl+C
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Shutdown requested. Stopping threads...")
        stop_event.set()
        for t in threads:
            t.join()

if __name__ == "__main__":
    main()
