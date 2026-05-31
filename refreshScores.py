from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def setup_driver():
    """Setup Chrome driver optimized for GitHub Actions"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    # Add these to improve loading in headless mode
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)  # Wait up to 10 seconds for elements
    return driver

def wait_for_page_to_load(driver, timeout=20):
    """Wait for page to be fully loaded"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Page loaded completely")
        return True
    except TimeoutException:
        print("Page load timeout but continuing...")
        return False

def safe_find_element(driver, by, value, timeout=15, description="element"):
    """Try multiple times to find an element with screenshots on failure"""
    try:
        print(f"Looking for {description}: '{value}'...")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        print(f"✓ Found {description}")
        return element
    except TimeoutException:
        print(f"✗ Could not find {description} after {timeout} seconds")
        
        # Take screenshot to see what's actually on the page
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_file = f"error_page_{timestamp}.png"
        driver.save_screenshot(screenshot_file)
        print(f"Screenshot saved: {screenshot_file}")
        
        # Print page info for debugging
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Check if we're on the right page
        if "login" in driver.current_url.lower():
            print("Looks like we're on a login page - authentication may have failed")
        elif "error" in driver.current_url.lower():
            print("Looks like we're on an error page")
        
        raise

# Modify your scraping code like this:
def scrape_activity_fixed(driver):
    """Fixed version with proper waiting"""
    
    # 1. First wait for page to load completely
    wait_for_page_to_load(driver)
    
    # 2. Add a small delay for any JavaScript rendering
    time.sleep(2)
    
    # 3. Try to find the element with explicit wait
    try:
        # Try multiple selector strategies
        ficha_link = None
        
        # Strategy 1: Exact link text
        try:
            ficha_link = safe_find_element(
                driver, 
                By.LINK_TEXT, 
                "Ficha de actividad",
                timeout=10,
                description="'Ficha de actividad' link"
            )
        except:
            # Strategy 2: Partial link text
            try:
                ficha_link = safe_find_element(
                    driver,
                    By.PARTIAL_LINK_TEXT,
                    "Ficha",
                    timeout=5,
                    description="partial 'Ficha' link"
                )
            except:
                # Strategy 3: XPath with contains
                try:
                    ficha_link = safe_find_element(
                        driver,
                        By.XPATH,
                        "//a[contains(text(), 'Ficha de actividad')]",
                        timeout=5,
                        description="XPATH for 'Ficha de actividad'"
                    )
                except:
                    # Strategy 4: Check if we need to scroll or click something first
                    print("Trying to scroll down...")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                    ficha_link = safe_find_element(
                        driver,
                        By.LINK_TEXT,
                        "Ficha de actividad",
                        timeout=5,
                        description="'Ficha de actividad' after scroll"
                    )
        
        if ficha_link:
            # Scroll to element before clicking
            driver.execute_script("arguments[0].scrollIntoView(true);", ficha_link)
            time.sleep(0.5)
            
            # Click with JavaScript as backup
            try:
                ficha_link.click()
            except:
                driver.execute_script("arguments[0].click();", ficha_link)
            
            print("Successfully clicked 'Ficha de actividad'")
            return True
        else:
            print("Could not find 'Ficha de actividad' with any method")
            return False
            
    except Exception as e:
        print(f"Error in scrape_activity_fixed: {e}")
        return False

# And make sure your login has proper waiting too:
def login_fixed(driver, username, password):
    """Fixed login with proper waiting"""
    print("Attempting to login...")
    
    # Wait for username field
    username_field = safe_find_element(driver, By.ID, "username", timeout=10, description="username field")
    username_field.send_keys(username)
    
    # Wait for password field  
    password_field = safe_find_element(driver, By.ID, "password", timeout=10, description="password field")
    password_field.send_keys(password)
    
    # Wait for submit button
    submit_button = safe_find_element(driver, By.XPATH, "//button[@type='submit']", timeout=10, description="submit button")
    submit_button.click()
    
    # Wait for login to complete
    time.sleep(3)
    wait_for_page_to_load(driver)
    
    print("Login completed")
    return True
