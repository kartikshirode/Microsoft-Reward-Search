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
            "RBI", "Startup India", "Kohli century", "Indian Railways",
            "Digital India", "Ayushman Bharat", "GST India", "UPI payments",
            "Farmer protests", "COVID vaccination", "Climate change India",
            "Education policy India", "Make in India", "India GDP growth",
            "Bollywood movies 2025", "Cricket World Cup", "Diwali celebrations",
            "Indian festivals", "Tech startups India", "Space mission India"
        ]
        random.shuffle(fallback)
        logger.info("Using fallback trending terms")
        return fallback

def setup_browser(browser_choice, operation_mode):
    """Setup browser based on user choice and operation mode."""
    options = uc.ChromeOptions()
    
    # Random user agent for more human-like behavior
    ua = random.choice(config['user_agents'])
    options.add_argument(f'user-agent={ua}')
    
    # Additional options for human-like behavior
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    
    # Configure based on operation mode
    if operation_mode == 1:  # Interactive Mode
        options.add_argument('--start-maximized')
        print("Interactive Mode: Browser will be visible and active")
    elif operation_mode == 2:  # Background Mode
        options.add_argument('--start-minimized')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        print("Background Mode: Browser will be minimized (you can use your device freely)")
    elif operation_mode == 3:  # Headless Mode
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        print("Headless Mode: Browser will be completely hidden (you can use your device freely)")
    
    if browser_choice == 1:
        # Try to connect to existing browser (not fully implemented in this version)
        print("Note: Using new browser instance (connecting to existing browser requires additional setup)")
    elif browser_choice == 3:
        # Use Edge instead of Chrome
        try:
            options.binary_location = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
        except:
            print("Edge not found, using Chrome instead")
    
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
        # Random scroll behavior
        scroll_actions = random.randint(1, 3)
        for _ in range(scroll_actions):
            # Scroll down a random amount
            scroll_pixels = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            time.sleep(random.uniform(
                config.get('scroll_delay_min', 1), 
                config.get('scroll_delay_max', 3)
            ))
            
        # Sometimes scroll back up
        if random.random() < 0.3:
            scroll_pixels = random.randint(200, 500)
            driver.execute_script(f"window.scrollBy(0, -{scroll_pixels});")
            time.sleep(random.uniform(1, 2))
            
    except Exception as e:
        logger.warning(f"Error during scrolling: {e}")

def human_like_page_interaction(driver, operation_mode):
    """Perform human-like interactions on the search results page."""
    try:
        # Wait for page to load
        WebDriverWait(driver, 10).wait(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Random delay before interaction
        time.sleep(random.uniform(
            config.get('page_interaction_delay_min', 3),
            config.get('page_interaction_delay_max', 8)
        ))
        
        # Only perform visual interactions in Interactive Mode
        if operation_mode == 1:
            # Perform human-like scrolling (only in interactive mode)
            human_like_scroll(driver)
            
            # Sometimes click on a result (30% chance, only in interactive mode)
            if random.random() < 0.3:
                try:
                    # Find search result links
                    results = driver.find_elements(By.CSS_SELECTOR, "h2 a, .b_algo h2 a")
                    if results:
                        # Click on a random result (but not the first one to avoid suspicion)
                        if len(results) > 1:
                            result_to_click = random.choice(results[1:min(5, len(results))])
                            result_to_click.click()
                            logger.info("Clicked on a search result")
                            
                            # Stay on the page for a random time
                            time.sleep(random.uniform(5, 15))
                            
                            # Go back to search results
                            driver.back()
                            time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Error clicking search result: {e}")
        else:
            # Background/Headless mode: just wait without interactions
            time.sleep(random.uniform(5, 12))
            logger.info("Background mode: Page loaded without visual interactions")
                
    except TimeoutException:
        logger.warning("Page load timeout during interaction")
    except Exception as e:
        logger.warning(f"Error during page interaction: {e}")

def perform_search(driver, term, search_count, total_searches, operation_mode):
    """Perform a single search with human-like behavior."""
    try:
        # Open new tab for search (except for the first search)
        if search_count > 1:
            driver.execute_script("window.open('', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
        
        # Construct Bing URL
        bing_url = f"https://www.bing.com/search?q={quote_plus(term)}&setmkt={config.get('bing_market','en-IN')}"
        
        print(f"\n[{search_count}/{total_searches}] Searching for: {term}")
        logger.info(f"[{search_count}/{total_searches}] Starting search for: {term}")
        
        # Navigate to Bing
        driver.get(bing_url)
        
        # Perform human-like interactions based on operation mode
        human_like_page_interaction(driver, operation_mode)
        
        # Mark as used
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
    
    # Add some variance based on search count (getting tired effect)
    if search_count > total_searches * 0.7:  # After 70% of searches
        base_delay *= random.uniform(1.2, 1.5)  # Longer delays
    
    # Random variation to avoid patterns
    variation = random.uniform(0.8, 1.3)
    final_delay = base_delay * variation
    
    return max(final_delay, 60)  # Minimum 1 minute delay

def main():
    """Main function with human-like behavior."""
    try:
        # Get user preferences
        browser_choice = get_browser_choice()
        if browser_choice == 4:
            print("Exiting...")
            return
            
        operation_mode = get_operation_mode()
        search_count_desired = get_search_count()
        
        mode_names = {1: "Interactive", 2: "Background", 3: "Headless"}
        device_usage = {1: "❌ Cannot use device freely", 2: "✅ Can use device freely", 3: "✅ Can use device freely"}
        
        print(f"\nSetup Summary:")
        print(f"- Browser: {'Existing/Chrome' if browser_choice <= 2 else 'Edge'}")
        print(f"- Operation Mode: {mode_names[operation_mode]}")
        print(f"- Device Usage: {device_usage[operation_mode]}")
        print(f"- Number of searches: {search_count_desired}")
        print(f"- Delay between searches: {config.get('search_delay_min', 120)}-{config.get('search_delay_max', 300)} seconds")
        print(f"- Human-like behavior: {'Full interactions' if operation_mode == 1 else 'Basic timing only'}")
        
        confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return
        
        # Setup browser
        print("\nSetting up browser...")
        driver, operation_mode = setup_browser(browser_choice, operation_mode)
        if not driver:
            print("Failed to setup browser. Exiting...")
            return
        
        # Get trending terms
        print("Fetching search terms...")
        terms = get_trending_terms()
        
        # Filter out already used terms
        available_terms = [t for t in terms if not is_used(t)]
        
        if len(available_terms) < search_count_desired:
            print(f"Warning: Only {len(available_terms)} unused terms available.")
            search_count_desired = min(search_count_desired, len(available_terms))
        
        if search_count_desired == 0:
            print("No new terms to search. Exiting.")
            driver.quit()
            return
        
        # Select terms for searching
        search_terms = available_terms[:search_count_desired]
        
        print(f"\nStarting {search_count_desired} searches...")
        if operation_mode in [2, 3]:
            print("✅ You can now use your device freely - the browser will run in the background!")
        else:
            print("❌ Please avoid using your device while searches are running (browser needs focus)")
        print("Press Ctrl+C to stop gracefully\n")
        
        # Perform searches
        successful_searches = 0
        for i, term in enumerate(search_terms, 1):
            try:
                if perform_search(driver, term, i, search_count_desired, operation_mode):
                    successful_searches += 1
                
                # Calculate and show delay for next search
                if i < search_count_desired:
                    delay = calculate_delay(i, search_count_desired)
                    minutes = int(delay // 60)
                    seconds = int(delay % 60)
                    print(f"Waiting {minutes}m {seconds}s before next search...")
                    
                    # Sleep with periodic updates
                    for remaining in range(int(delay), 0, -30):
                        if remaining <= 30:
                            time.sleep(remaining)
                            break
                        time.sleep(30)
                        print(f"  {remaining // 60}m {remaining % 60}s remaining...")
                        
            except KeyboardInterrupt:
                print(f"\n\nGracefully stopping after {successful_searches} successful searches...")
                break
            except Exception as e:
                logger.error(f"Unexpected error during search {i}: {e}")
                print(f"Error during search {i}, continuing...")
        
        print(f"\n\nCompleted! {successful_searches} successful searches out of {search_count_desired} planned.")
        
        # Keep browser open option
        if operation_mode == 1:  # Only ask in Interactive Mode
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
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"Fatal error: {e}")
    finally:
        logger.info("Script execution ended")

if __name__ == "__main__":
    main()
