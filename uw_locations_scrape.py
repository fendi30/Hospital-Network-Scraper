"""
UW Medicine Location Scraper Module

This module contains all the scraping functions for extracting location data
from the UW Medicine website using Selenium.
"""

import csv
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Import configuration
import config


def setup_driver(headless=None, disable_images=None):
    """
    Set up and configure the Chrome WebDriver with anti-detection measures.
    
    This function configures Chrome to appear as a normal user browser rather than
    an automated script, helping to avoid detection by anti-bot systems.
    
    Args:
        headless: If True, run browser without GUI. If None, uses config.HEADLESS_MODE
        disable_images: If True, disable image loading. If None, uses config.DISABLE_IMAGES
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance with anti-detection
    """
    # Use config defaults if not specified
    if headless is None:
        headless = config.HEADLESS_MODE
    if disable_images is None:
        disable_images = config.DISABLE_IMAGES
    
    chrome_options = Options()
    
    # === ANTI-DETECTION MEASURES ===
    
    # 1. Disable automation flags that websites can detect
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 2. Set a realistic user agent (appears as normal Chrome browser)
    if config.USER_AGENT_TYPE == 'random':
        user_agent = random.choice(list(config.USER_AGENTS.values()))
    else:
        user_agent = config.USER_AGENTS.get(config.USER_AGENT_TYPE, config.USER_AGENTS['windows_chrome'])
    
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # 3. Disable webdriver detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # 4. Add common browser arguments to appear more legitimate
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    
    # 5. Set window size from config
    chrome_options.add_argument(f'--window-size={config.WINDOW_WIDTH},{config.WINDOW_HEIGHT}')
    
    # 6. Enable some features that normal browsers have
    chrome_options.add_argument('--enable-javascript')
    chrome_options.add_argument('--enable-cookies')
    
    # 7. Set language to English (US)
    chrome_options.add_argument('--lang=en-US')
    
    # 8. Disable notifications and other popups
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    
    # 9. Optionally disable images for faster loading
    if disable_images:
        prefs["profile.managed_default_content_settings.images"] = 2
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 10. Run in headless mode if requested (with additional stealth settings)
    if headless:
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--disable-extensions')
    
    # 11. Configure proxy if enabled in config
    if config.USE_PROXY and config.PROXY_SERVER:
        chrome_options.add_argument(f'--proxy-server={config.PROXY_SERVER}')
        print(f"Using proxy: {config.PROXY_SERVER}")
    
    # Set up the driver with automatic ChromeDriver management
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # === POST-INITIALIZATION STEALTH ===
    
    # 12. Override navigator.webdriver property (makes it appear as regular Chrome)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        '''
    })
    
    # 13. Override navigator properties to match a real browser
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        '''
    })
    
    # 14. Set a realistic screen resolution from config
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'width': config.WINDOW_WIDTH,
        'height': config.WINDOW_HEIGHT,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    
    return driver


def scroll_page(driver):
    """
    Simulate human-like scrolling behavior on the page.
    
    This helps avoid detection by making the browser behavior appear more natural.
    
    Args:
        driver: Selenium WebDriver instance
    """
    # Get page height
    total_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll in chunks (like a human would)
    current_position = 0
    scroll_increment = random.randint(config.SCROLL_INCREMENT_MIN, config.SCROLL_INCREMENT_MAX)
    
    while current_position < total_height:
        # Scroll down by increment
        current_position += scroll_increment
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # Random delay between scrolls
        time.sleep(random.uniform(config.SCROLL_DELAY_MIN, config.SCROLL_DELAY_MAX))
        
        # Recalculate height (in case page loads more content)
        total_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(0.5, 1.0))


def extract_text(element, selectors):
    """
    Try multiple CSS selectors to extract text from an element.
    
    Args:
        element: Selenium WebElement to search within
        selectors: List of CSS selectors to try
    
    Returns:
        str: Extracted text or empty string if not found
    """
    for selector in selectors:
        try:
            found_elem = element.find_element(By.CSS_SELECTOR, selector)
            text = found_elem.text.strip()
            if text:
                return text
        except:
            continue
    return ""


def parse_address_block(address_text):
    """
    Parse a full address block into components (address1, address2, city, state, zip).
    
    Handles cases where the address is all in one element like:
    "123 Main Street, Suite 100, Seattle, WA 98101"
    or
    "123 Main Street
     Suite 100
     Seattle, WA 98101"
    
    Args:
        address_text: Full address text string
    
    Returns:
        dict: Dictionary with keys 'address1', 'address2', 'city', 'state', 'zip'
    """
    import re
    
    result = {
        'address1': '',
        'address2': '',
        'city': '',
        'state': '',
        'zip': ''
    }
    
    if not address_text:
        return result
    
    # Split by newlines or commas
    lines = [line.strip() for line in address_text.replace(',', '\n').split('\n') if line.strip()]
    
    if not lines:
        return result
    
    # Try to find ZIP code (5 digits or 5+4 format)
    zip_pattern = r'\b(\d{5}(?:-\d{4})?)\b'
    
    # Try to find state (2 letter state code)
    state_pattern = r'\b([A-Z]{2})\b'
    
    # Look for city, state, zip pattern
    city_state_zip_pattern = r'([^,\n]+),?\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)'
    
    # Join all lines to search for patterns
    full_text = ' '.join(lines)
    
    # Try to extract city, state, zip
    match = re.search(city_state_zip_pattern, full_text)
    if match:
        result['city'] = match.group(1).strip()
        result['state'] = match.group(2).strip()
        result['zip'] = match.group(3).strip()
        
        # Remove the city, state, zip from lines to get address lines
        city_state_zip_line = match.group(0)
        remaining_lines = []
        for line in lines:
            if city_state_zip_line not in line:
                remaining_lines.append(line)
            else:
                # Add any text before city, state, zip on the same line
                before_match = line.split(city_state_zip_line)[0].strip()
                if before_match:
                    remaining_lines.append(before_match)
        
        # First remaining line is address1, second is address2
        if remaining_lines:
            result['address1'] = remaining_lines[0]
        if len(remaining_lines) > 1:
            result['address2'] = remaining_lines[1]
    
    else:
        # Fallback: try to parse line by line
        if len(lines) >= 1:
            result['address1'] = lines[0]
        if len(lines) >= 2:
            result['address2'] = lines[1]
        if len(lines) >= 3:
            # Last line often has city, state, zip
            last_line = lines[-1]
            
            # Extract ZIP
            zip_match = re.search(zip_pattern, last_line)
            if zip_match:
                result['zip'] = zip_match.group(1)
                last_line = last_line.replace(result['zip'], '').strip()
            
            # Extract state
            state_match = re.search(state_pattern, last_line)
            if state_match:
                result['state'] = state_match.group(1)
                last_line = last_line.replace(result['state'], '').strip()
            
            # What remains is likely the city
            result['city'] = last_line.strip(' ,')
    
    return result


def extract_location_data(driver, url, wait_time=None):
    """
    Navigate to the URL and extract all location information with human-like behavior.
    
    Args:
        driver: Selenium WebDriver instance
        url: The URL to scrape
        wait_time: Maximum time to wait for elements to load in seconds. 
                   If None, uses config.PAGE_LOAD_TIMEOUT
    
    Returns:
        list: List of dictionaries containing location data
    """
    if wait_time is None:
        wait_time = config.PAGE_LOAD_TIMEOUT
    
    print(f"Loading page: {url}")
    driver.get(url)
    
    # Add random delay to simulate human reading time
    time.sleep(random.uniform(config.INITIAL_DELAY_MIN, config.INITIAL_DELAY_MAX))
    
    # Simulate human scrolling behavior
    scroll_page(driver)
    
    # Wait for the page to load and location elements to be present
    wait = WebDriverWait(driver, wait_time)
    
    try:
        # Wait for location cards/items to load
        # Try each selector from config
        for selector in config.LOCATION_CONTAINER_SELECTORS:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Found elements using selector: {selector}")
                break
            except:
                continue
    except Exception as e:
        print(f"Warning: Timeout waiting for location elements. Proceeding anyway...")
    
    # Give the page a moment to fully render
    time.sleep(random.uniform(1, 2))
    
    locations = []
    
    # Try to find all location elements using selectors from config
    try:
        # Build CSS selector from config
        selector_string = ", ".join(config.LOCATION_CONTAINER_SELECTORS)
        location_elements = driver.find_elements(By.CSS_SELECTOR, selector_string)
        
        print(f"Found {len(location_elements)} location elements")
        
        for idx, location_elem in enumerate(location_elements, 1):
            try:
                # Extract location details using selectors from config
                facility_name = extract_text(location_elem, config.SELECTORS['facility_name'])
                
                # Try to extract address components individually first
                address1 = extract_text(location_elem, config.SELECTORS['address1'])
                address2 = extract_text(location_elem, config.SELECTORS['address2'])
                city = extract_text(location_elem, config.SELECTORS['city'])
                state = extract_text(location_elem, config.SELECTORS['state'])
                zip_code = extract_text(location_elem, config.SELECTORS['zip'])
                phone = extract_text(location_elem, config.SELECTORS['phone'])
                
                # If address components are missing, try to parse from a full address block
                if not city or not state or not zip_code:
                    # Get all text from the element and try to parse it
                    full_text = location_elem.text.strip()
                    parsed_address = parse_address_block(full_text)
                    
                    # Use parsed values if we didn't find individual components
                    if not address1 and parsed_address['address1']:
                        address1 = parsed_address['address1']
                    if not address2 and parsed_address['address2']:
                        address2 = parsed_address['address2']
                    if not city and parsed_address['city']:
                        city = parsed_address['city']
                    if not state and parsed_address['state']:
                        state = parsed_address['state']
                    if not zip_code and parsed_address['zip']:
                        zip_code = parsed_address['zip']
                
                # Only add if we found at least a name
                if facility_name:
                    location_data = {
                        'Facility Name': facility_name,
                        'Address 1': address1,
                        'Address 2': address2,
                        'City': city,
                        'State': state,
                        'ZIP': zip_code,
                        'Phone': phone
                    }
                    
                    locations.append(location_data)
                    
                    # Show what we extracted
                    if address1 or city:
                        print(f"  {idx}. {facility_name} - {address1}, {city}, {state} {zip_code}")
                    else:
                        print(f"  {idx}. {facility_name} - [Address parsing needed]")
                    
                    # Add small random delay between processing items (human-like behavior)
                    if idx % config.ITEM_BATCH_SIZE == 0:
                        time.sleep(random.uniform(config.ITEM_BATCH_DELAY_MIN, config.ITEM_BATCH_DELAY_MAX))
                    
            except Exception as e:
                print(f"Error extracting location {idx}: {e}")
                continue
    
    except Exception as e:
        print(f"Error finding location elements: {e}")
        print("\nPage source preview (first 500 chars):")
        print(driver.page_source[:500])
    
    return locations


def save_to_csv(locations, filename='uw_medicine_locations.csv'):
    """
    Save the extracted location data to a CSV file.
    
    Args:
        locations: List of dictionaries containing location data
        filename: Name of the output CSV file (default: 'uw_medicine_locations.csv')
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    if not locations:
        print("No locations to save!")
        return False
    
    fieldnames = ['Facility Name', 'Address 1', 'Address 2', 'City', 'State', 'ZIP', 'Phone']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(locations)
        
        print(f"\nSuccessfully saved {len(locations)} locations to {filename}")
        return True
    
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False


def save_page_source(driver, filename='page_source.html'):
    """
    Save the current page source to a file for debugging.
    
    Args:
        driver: Selenium WebDriver instance
        filename: Name of the output HTML file (default: 'page_source.html')
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"Page source saved to '{filename}' for inspection.")
    except Exception as e:
        print(f"Error saving page source: {e}")


