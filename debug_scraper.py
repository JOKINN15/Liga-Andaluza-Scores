#!/usr/bin/env python3
"""
Debug script to test scraping locally
Run with: python debug_scraper.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import sys

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Use environment variables if set (for GitHub Actions)
    if os.environ.get('CHROME_PATH'):
        chrome_options.binary_location = os.environ.get('CHROME_PATH')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def save_page_source(driver, filename="page_source.html"):
    """Save page source for debugging"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"Page source saved to {filename}")

def debug_scrape():
    driver = None
    try:
        print("Starting debug scrape...")
        driver = setup_driver()
        
        # Get credentials
        username = os.environ.get('GOLF_USER')
        password = os.environ.get('GOLF_PASSWORD')
        
        if not username or not password:
            print("ERROR: GOLF_USER or GOLF_PASSWORD environment variables not set")
            sys.exit(1)
        
        # Navigate to your site (replace with actual URL)
        print("Loading page...")
        driver.get("YOUR_GOLF_SITE_URL_HERE")  # <-- PUT YOUR ACTUAL URL HERE
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Page loaded")
        
        # Save initial page state
        driver.save_screenshot("initial_page.png")
        save_page_source(driver, "initial_page_source.html")
        
        # Try to find the element
        print("\nSearching for 'Ficha de actividad' link...")
        
        # Method 1: Exact link text
        try:
            element = driver.find_element(By.LINK_TEXT, "Ficha de actividad")
            print("✓ Found with exact LINK_TEXT")
            print(f"  Element: {element.tag_name}, Text: {element.text}")
        except NoSuchElementException:
            print("✗ Not found with exact LINK_TEXT")
        
        # Method 2: Partial link text
        try:
            elements = driver.find_elements(By.PARTIAL_LINK_TEXT, "Ficha")
            if elements:
                print(f"✓ Found {len(elements)} element(s) with PARTIAL_LINK_TEXT 'Ficha':")
                for e in elements:
                    print(f"  - '{e.text}'")
            else:
                print("✗ No elements found with PARTIAL_LINK_TEXT 'Ficha'")
        except:
            print("✗ Error searching with PARTIAL_LINK_TEXT")
        
        # Method 3: XPATH contains
        try:
            elements = driver.find_elements(By.XPATH, "//a[contains(text(), 'Ficha')]")
            if elements:
                print(f"✓ Found {len(elements)} element(s) with XPATH containing 'Ficha':")
                for e in elements:
                    print(f"  - '{e.text}'")
            else:
                print("✗ No elements found with XPATH containing 'Ficha'")
        except:
            print("✗ Error searching with XPATH")
        
        # Method 4: Check all links
        print("\nAll links on page (first 30):")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for i, link in enumerate(all_links[:30]):
            if link.text.strip():
                print(f"  {i+1}. '{link.text[:50]}'")
        
        # Method 5: Check for any Spanish golf-related text
        print("\nLooking for common golf activity text patterns...")
        patterns = ["actividad", "tarjeta", "resultados", "ronda", "juego"]
        for pattern in patterns:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
            if elements:
                print(f"  ✓ Found '{pattern}' in {len(elements)} element(s):")
                for e in elements[:3]:
                    if e.text.strip():
                        print(f"    - '{e.text[:80]}'")
        
        print("\nDebug completed. Check the saved files for analysis.")
        
    except Exception as e:
        print(f"Error during debug: {e}")
        if driver:
            driver.save_screenshot("error_screenshot.png")
            save_page_source(driver, "error_page_source.html")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_scrape()
