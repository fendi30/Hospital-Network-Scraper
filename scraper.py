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
from pagination_utils import find_pagination_element, handle_pagination


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
    
    # Split by newlines or multiple spaces, then by commas
    lines = [line.strip() for line in re.split(r'\n|,', address_text) if line.strip()]
    
    if not lines:
        return result
    
    # Patterns for matching
    zip_pattern = r'\b(\d{5}(?:-\d{4})?)\b'
    state_pattern = r'\b([A-Z]{2})\b'
    
    # Look for city, state, zip pattern in the full text
    city_state_zip_pattern = r'([A-Za-z\s]+?)\s*,?\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)'
    
    # Join all lines to search for patterns
    full_text = ' '.join(lines)
    
    # Try to extract city, state, zip
    match = re.search(city_state_zip_pattern, full_text)
    if match:
        result['city'] = match.group(1).strip()
        result['state'] = match.group(2).strip()
        result['zip'] = match.group(3).strip()
        
        # Find which line contains the city/state/zip
        city_state_zip_line = match.group(0)
        
        # Get the lines before city/state/zip (these are address lines)
        remaining_lines = []
        found_city_line = False
        for line in lines:
            if result['city'] in line and result['state'] in line:
                found_city_line = True
                continue
            if not found_city_line:
                remaining_lines.append(line)
        
        # Find the actual street address (line with numbers)
        address_lines = []
        for line in remaining_lines:
            # Street address typically has numbers
            if re.search(r'\d+', line):
                # Check if this looks like a street address (has numbers and street indicators)
                if re.search(r'\d+\s+\w+', line):
                    address_lines.append(line)
        
        if address_lines:
            result['address1'] = address_lines[0]
            if len(address_lines) > 1:
                result['address2'] = address_lines[1]
        elif remaining_lines:
            # Fallback to first remaining line
            result['address1'] = remaining_lines[0]
            if len(remaining_lines) > 1:
                result['address2'] = remaining_lines[1]
    
    else:
        # Fallback: try to parse line by line
        # Look for a line with a street number
        street_address_idx = -1
        for i, line in enumerate(lines):
            if re.match(r'^\d+\s+', line):  # Starts with a number
                street_address_idx = i
                break
        
        if street_address_idx >= 0:
            result['address1'] = lines[street_address_idx]
            
            # Next line might be address2
            if street_address_idx + 1 < len(lines):
                next_line = lines[street_address_idx + 1]
                # Check if it's suite/floor/unit or another address line
                if re.search(r'(suite|ste|floor|fl|unit|apt|#)', next_line, re.IGNORECASE) or not re.search(r'[A-Z]{2}\s+\d{5}', next_line):
                    result['address2'] = next_line
                    
            # Look for city/state/zip in remaining lines
            for i in range(street_address_idx + 1, len(lines)):
                line = lines[i]
                
                # Extract ZIP
                zip_match = re.search(zip_pattern, line)
                if zip_match:
                    result['zip'] = zip_match.group(1)
                    line = line.replace(result['zip'], '').strip()
                
                # Extract state
                state_match = re.search(state_pattern, line)
                if state_match:
                    result['state'] = state_match.group(1)
                    line = line.replace(result['state'], '').strip()
                
                # What remains is likely the city
                if line and not result['city']:
                    result['city'] = line.strip(' ,')
        else:
            # No street address found, just take first few lines
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


def clean_address_fields(address1, address2, city, state, zip_code):
    """
    Clean and validate address fields to ensure proper formatting.
    
    Args:
        address1, address2, city, state, zip_code: Raw extracted values
    
    Returns:
        tuple: (cleaned_address1, cleaned_address2, cleaned_city, cleaned_state, cleaned_zip)
    """
    import re
    
    # Clean city field
    if city:
        # Remove any zip codes
        city = re.sub(r'\b\d{5}(?:-\d{4})?\b', '', city).strip()
        
        # Remove state codes
        city = re.sub(r'\b[A-Z]{2}\b', '', city).strip()
        
        # Remove street type words that shouldn't be in city
        city = re.sub(r'\b(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Suite|Ste|Floor|Fl|Building|Bldg|Unit|Apt|#)\.?\b', '', city, flags=re.IGNORECASE).strip()
        
        # Remove leading numbers (shouldn't start with numbers)
        city = re.sub(r'^\d+\s*', '', city).strip()
        
        # Clean up commas and extra spaces
        city = city.strip(' ,')
        city = re.sub(r'\s+', ' ', city)
    
    # Ensure state is 2 letters uppercase
    if state:
        if len(state) > 2:
            # Try to extract 2-letter state code
            state_match = re.search(r'\b([A-Z]{2})\b', state)
            if state_match:
                state = state_match.group(1)
    
    # Clean zip code
    if zip_code:
        # Extract just the zip code if it has extra text
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', zip_code)
        if zip_match:
            zip_code = zip_match.group(1)
    
    return address1, address2, city, state, zip_code


def format_phone_number(phone):
    """
    Format phone number to (999) 999-9999 format.
    
    Handles various input formats like:
    - 999.999.9999
    - 9999999999
    - (999) 999-9999
    - 999-999-9999
    
    Args:
        phone: Raw phone number string
    
    Returns:
        str: Formatted phone number or original if can't format
    """
    import re
    
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if we have 10 digits (US phone number)
    if len(digits) == 10:
        # Format as (999) 999-9999
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    
    # Check if we have 11 digits starting with 1 (US with country code)
    elif len(digits) == 11 and digits[0] == '1':
        # Format as (999) 999-9999 (strip the leading 1)
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    
    # If not standard format, return original
    else:
        return phone


def parse_office_hours(hours_text, facility_name=''):
    """
    Parse office hours text into a dictionary with separate days.
    Handles formats like:
    - "Mon - Thur: 7:30 a.m. - 5 p.m. / Fri: 8 a.m. - 5 p.m."
    - "Mon - Thur: 8 a.m. - 12 p.m. & 1 p.m. - 5 p.m."
    - "Mon & Wed: 8 a.m. - 5 p.m."
    - "8 a.m. - 8 p.m., 7 days a week"
    - Ignores notes like "appointments only", "provider hours may vary"
    
    Args:
        hours_text: Raw hours text string
        facility_name: Facility name to check for ER
    
    Returns:
        dict: Dictionary with day names as keys and hours as values
    """
    import re
    
    office_hours = {
        'Monday': '',
        'Tuesday': '',
        'Wednesday': '',
        'Thursday': '',
        'Friday': '',
        'Saturday': '',
        'Sunday': ''
    }
    
    if not hours_text:
        return office_hours
    
    # Ignore common notes/disclaimers
    ignore_phrases = [
        'appointments only',
        'appointment only',
        'provider hours may vary',
        'please call',
        'call their office',
        'for details',
        'hours may vary',
        'by appointment'
    ]
    
    # Clean the text - remove ignore phrases
    cleaned_text = hours_text
    for phrase in ignore_phrases:
        cleaned_text = re.sub(phrase, '', cleaned_text, flags=re.IGNORECASE)
    
    # Check for "7 days a week" pattern - means same hours every day
    seven_days_match = re.search(r'([\d:]+\s*[ap]\.?m\.?\s*-\s*[\d:]+\s*[ap]\.?m\.?),?\s*7\s*days?\s*a?\s*week', cleaned_text, re.IGNORECASE)
    if seven_days_match:
        hours = seven_days_match.group(1).strip()
        for day in office_hours.keys():
            office_hours[day] = hours
        return office_hours
    
    # Split by common delimiters (/, "and" when between segments)
    segments = re.split(r'\s*/\s*|\n', cleaned_text)
    
    day_abbrev_map = {
        'mon': 'Monday',
        'monday': 'Monday',
        'tue': 'Tuesday',
        'tues': 'Tuesday',
        'tuesday': 'Tuesday',
        'wed': 'Wednesday',
        'wednesday': 'Wednesday',
        'thu': 'Thursday',
        'thur': 'Thursday',
        'thurs': 'Thursday',
        'thursday': 'Thursday',
        'fri': 'Friday',
        'friday': 'Friday',
        'sat': 'Saturday',
        'saturday': 'Saturday',
        'sun': 'Sunday',
        'sunday': 'Sunday'
    }
    
    for segment in segments:
        segment = segment.strip()
        
        # Skip if segment is just notes/disclaimers
        if not re.search(r'\d', segment):  # No digits = likely just a note
            continue
        
        # Match "Mon & Wed: 8 a.m. - 5 p.m." (ampersand pattern)
        ampersand_match = re.match(r'([A-Za-z]+)\s*&\s*([A-Za-z]+)\s*:\s*(.+)', segment, re.IGNORECASE)
        if ampersand_match:
            day1_abbrev = ampersand_match.group(1).lower()
            day2_abbrev = ampersand_match.group(2).lower()
            hours = ampersand_match.group(3).strip()
            
            day1_full = day_abbrev_map.get(day1_abbrev)
            day2_full = day_abbrev_map.get(day2_abbrev)
            
            if day1_full:
                office_hours[day1_full] = hours
            if day2_full:
                office_hours[day2_full] = hours
            continue
        
        # Match patterns like "Mon - Thur: 7:30 a.m. - 5 p.m."
        range_match = re.match(r'([A-Za-z]+)\s*-\s*([A-Za-z]+)\s*:\s*(.+)', segment, re.IGNORECASE)
        if range_match:
            start_day = range_match.group(1).lower()
            end_day = range_match.group(2).lower()
            hours = range_match.group(3).strip()
            
            # Get full day names
            start_full = day_abbrev_map.get(start_day)
            end_full = day_abbrev_map.get(end_day)
            
            if start_full and end_full:
                # Find the range of days
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                start_idx = days_order.index(start_full)
                end_idx = days_order.index(end_full)
                
                for day in days_order[start_idx:end_idx+1]:
                    office_hours[day] = hours
            continue
        
        # Match single day pattern: "Fri: 8 a.m. - 5 p.m."
        single_match = re.match(r'([A-Za-z]+)\s*:\s*(.+)', segment, re.IGNORECASE)
        if single_match:
            day_abbrev = single_match.group(1).lower()
            hours = single_match.group(2).strip()
            
            day_full = day_abbrev_map.get(day_abbrev)
            if day_full:
                office_hours[day_full] = hours
    
    return office_hours


def parse_multicare_hours(hours_text, facility_name=''):
    """
    Parse MultiCare-specific office hours with priority system:
    1. Regular hours (Monday - Friday: 8am - 5pm)
    2. Clinic hours (if regular not available)
    3. Visitor hours (if clinic not available)
    4. Ignore: Emergency Room hours, holiday hours, special occasions, "by appointment only" sections
    
    Args:
        hours_text: Raw hours text from General Hours section
        facility_name: Facility name to check for ER
    
    Returns:
        dict: Dictionary with day names as keys and hours as values
    """
    import re
    
    office_hours = {
        'Monday': '',
        'Tuesday': '',
        'Wednesday': '',
        'Thursday': '',
        'Friday': '',
        'Saturday': '',
        'Sunday': ''
    }
    
    if not hours_text:
        return office_hours
    
    # Split into sections/lines
    lines = hours_text.split('\n')
    
    # Track which section we're in
    # DEFAULT to 'regular' so hours without section headers are captured
    current_section = 'regular'
    section_hours = {
        'regular': [],
        'clinic': [],
        'visitor': []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Identify sections
        line_lower = line.lower()
        
        # Skip unwanted sections
        if any(skip in line_lower for skip in [
            'emergency room:',
            'holiday',
            'thanksgiving',
            'christmas',
            'second thursday',
            'first monday',
            'third wednesday',
            'closed for lunch',
            'day after thanksgiving'
        ]):
            current_section = 'skip'
            continue
        
        # Check for "by appointment only" - but keep reading for hours below
        if 'by appointment only' in line_lower or 'appointment only' in line_lower:
            # Don't skip, but don't set this as a section either
            continue
        
        # Identify section headers
        if 'clinic:' in line_lower:
            current_section = 'clinic'
            continue
        elif 'visitor hours:' in line_lower or 'visitor:' in line_lower:
            current_section = 'visitor'
            continue
        elif 'lab:' in line_lower:
            current_section = 'lab'
            continue
        elif 'general hours' in line_lower:
            current_section = 'regular'
            continue
        
        # If line has day and time pattern, add to current section
        if current_section and current_section != 'skip':
            # Check if line has days and times (Monday, Friday, 7am, 5pm, etc.)
            has_day = re.search(r'\b(mon|tue|wed|thu|fri|sat|sun|weekday)', line_lower)
            has_time = re.search(r'\d+:\d+\s*[ap]m|\d+\s*[ap]m', line_lower, re.IGNORECASE)
            
            if has_day and has_time:
                # Determine which section this belongs to
                if current_section == 'lab':
                    section_hours['clinic'].append(line)
                else:
                    section_hours.get(current_section, []).append(line)
    
    # Priority: regular > clinic > visitor
    chosen_hours = None
    if section_hours['regular']:
        chosen_hours = '\n'.join(section_hours['regular'])
    elif section_hours['clinic']:
        chosen_hours = '\n'.join(section_hours['clinic'])
    elif section_hours['visitor']:
        chosen_hours = '\n'.join(section_hours['visitor'])
    
    # If we found hours, parse them using the standard parser
    if chosen_hours:
        office_hours = parse_office_hours(chosen_hours, facility_name)
    
    return office_hours


def extract_location_data(driver, url, wait_time=None):
    """
    Navigate to the URL and extract all location information with human-like behavior.
    Automatically handles pagination to extract from all pages.
    
    Args:
        driver: Selenium WebDriver instance
        url: The URL to scrape
        wait_time: Maximum time to wait for elements to load in seconds. 
                   If None, uses config.PAGE_LOAD_TIMEOUT
    
    Returns:
        list: List of dictionaries containing location data from all pages
    """
    if wait_time is None:
        wait_time = config.PAGE_LOAD_TIMEOUT
    
    print(f"Loading page: {url}")
    driver.get(url)
    
    # Add random delay to simulate human reading time
    time.sleep(random.uniform(config.INITIAL_DELAY_MIN, config.INITIAL_DELAY_MAX))
    
    # For JavaScript-heavy sites, add extra wait
    if 'skagitregionalhealth.org' in url:
        print("  Detected JavaScript-heavy site, waiting for content to load...")
        time.sleep(5)  # Extra wait for JS to execute

    # Simulate human scrolling behavior
    scroll_page(driver)
    
    # Additional wait after scrolling for lazy-loaded content
    if 'skagitregionalhealth.org' in url:
        print("  Scrolling triggered content load, waiting...")
        time.sleep(3)

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
    
    all_locations = []
    current_page = 1
    
    # Loop through pages if pagination is enabled
    while True:
        print(f"\n  📄 Page {current_page}")
        
        # Extract locations from current page
        locations = extract_locations_from_current_page(driver)
        
        if locations:
            print(f"    ✓ Extracted {len(locations)} locations from this page")
            all_locations.extend(locations)
        else:
            print(f"    ⚠ No locations found on this page")
        
        # Check if we should continue to next page
        if not config.ENABLE_PAGINATION:
            print(f"    Pagination disabled in config - stopping here")
            break
        
        if current_page >= config.MAX_PAGES_PER_URL:
            print(f"    Reached maximum page limit ({config.MAX_PAGES_PER_URL})")
            break
        
        # Try to navigate to next page
        print(f"    Looking for next page...")
        if not handle_pagination(driver, current_page):
            print(f"    No more pages found")
            break
        
        current_page += 1
        
        # Scroll the new page
        scroll_page(driver)
        time.sleep(random.uniform(1, 2))
    
    print(f"\n  Total locations from all pages: {len(all_locations)}")
    return all_locations


def extract_locations_from_current_page(driver):
    """
    Extract location data from the current page (doesn't handle pagination).
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        list: List of dictionaries containing location data from current page
    """
    locations = []
    
    # Try to find all location elements using selectors from config
    try:
        # Build CSS selector from config
        selector_string = ", ".join(config.LOCATION_CONTAINER_SELECTORS)
        
        # Get initial count of elements
        location_elements = driver.find_elements(By.CSS_SELECTOR, selector_string)
        num_locations = len(location_elements)
        
        print(f"      Found {num_locations} location elements on this page")
        
        # Use index-based iteration to handle page navigation (detail pages)
        for idx, location_elem in enumerate(location_elements):
            try:
                # Re-find elements each iteration (in case we navigated away)
                location_elements = driver.find_elements(By.CSS_SELECTOR, selector_string)
                
                # Make sure we still have this element
                if idx >= len(location_elements):
                    break
                
                location_elem = location_elements[idx]
                
                # Skip parent container elements (e.g., .location-list wrapper on MultiCare)
                elem_classes = location_elem.get_attribute('class') or ''             
                if 'location-list' in elem_classes and 'location-list-card' not in elem_classes:
                    idx += 1
                    continue

                # Extract location details using selectors from config
                facility_name = extract_text(location_elem, config.SELECTORS['facility_name'])


                # For MultiCare/Swedish: Check if there are multiple headings that should be combined
                current_url = driver.current_url
                if 'providence.org' in current_url or 'swedish.org' in current_url:
                    # Look for parent/subheading that should be combined with main title
                    try:
                        # Look for parent location in subhead-h5
                        parent_elem = location_elem.find_element(By.CSS_SELECTOR, '.subhead-h5')

                        if parent_elem:
                            parent_name = parent_elem.text.strip()
                            facility_name = f"{parent_name} - {facility_name}"
                        
                    except:
                        pass  # If anything fails, just use the original facility_name
                
                # Try to extract address components individually first
                address1 = extract_text(location_elem, config.SELECTORS['address1'])
                address2 = extract_text(location_elem, config.SELECTORS['address2'])
                city = extract_text(location_elem, config.SELECTORS['city'])
                state = extract_text(location_elem, config.SELECTORS['state'])
                zip_code = extract_text(location_elem, config.SELECTORS['zip'])
                phone = extract_text(location_elem, config.SELECTORS['phone'])
                
                # Initialize fax and office hours (will be populated for Swedish/Providence)
                fax = ''
                office_hours = {
                    'Monday': '',
                    'Tuesday': '',
                    'Wednesday': '',
                    'Thursday': '',
                    'Friday': '',
                    'Saturday': '',
                    'Sunday': ''
                }
                
                # Skip if no facility name (likely a button or non-location element)
                if not facility_name:
                    continue
                
                # Determine which site we're scraping based on the URL
                import re
                current_url = driver.current_url

                
                # Site-specific parsing
                if 'uwmedicine.org' in current_url:
                    # UW Medicine format: "Facility Name\nMain Hospital, 325 9th Ave., Seattle, WA 98104"
                    if address1:
                        # Store original
                        original_address = address1
                        
                        # Remove facility name
                        if facility_name and facility_name in address1:
                            address1 = address1.replace(facility_name, '').strip()
                        
                        # Extract city, state, zip FIRST
                        csz_match = re.search(r'([A-Za-z\s]+?),?\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', address1)
                        if csz_match:
                            city = csz_match.group(1).strip()
                            state = csz_match.group(2).strip()
                            zip_code = csz_match.group(3).strip()
                        
                        # Extract street address
                        if city:
                            address_parts = address1.split(city)[0]
                        else:
                            address_parts = address1
                        
                        street_match = re.search(r'(\d+\s+[A-Za-z0-9\s\.]+?)(?:,|$)', address_parts)
                        if street_match:
                            address1 = street_match.group(1).strip()
                        
                        address1 = address1.replace('Main Hospital', '').strip(' ,.')
                
                elif 'swedish.org' in current_url or 'providence.org' in current_url:
                    # Swedish and Providence format: address often has city on next line
                    # "37624 SE Fury St\nSnoqualmie"
                    # OR: "23525 NE Novelty Hill Rd, Suite 111"
                    
                    # Get full text for comprehensive parsing
                    full_text = location_elem.text.strip()
                    
                    # First, extract city, state, zip from FULL TEXT (before any modifications)
                    if not city or not state or not zip_code:
                        # Try pattern with state abbreviation: "Seattle, WA 98104"
                        # Use non-greedy match and look for city on its own line or after newline
                        state_zip = re.search(r'([A-Za-z\s]+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b', full_text)
                        if state_zip:
                            raw_city = state_zip.group(1).strip()
                            state = state_zip.group(2).strip()
                            zip_code = state_zip.group(3).strip()
                            
                            # Clean the raw city - it might have street names in it
                            # Take only the LAST word or two (actual city name)
                            city_lines = raw_city.split('\n')
                            if len(city_lines) > 1:
                                # City is on the last line
                                city = city_lines[-1].strip()
                            else:
                                # Split by common delimiters and take the last part
                                # Remove any street suffixes (St, Ave, Rd, etc.)
                                city_parts = raw_city.replace(',', ' ').split()
                                # Filter out street type words
                                filtered_parts = [p for p in city_parts if p.lower() not in ['st', 'ave', 'rd', 'dr', 'ln', 'way', 'blvd', 'street', 'avenue', 'road', 'drive', 'lane']]
                                if filtered_parts:
                                    city = filtered_parts[-1]  # Take the last word as city
                                else:
                                    city = city_parts[-1] if city_parts else raw_city
                        else:
                            # Try pattern with full state name: "Redmond, Washington 98053"
                            full_state = re.search(r'([A-Za-z\s]+),\s*(Washington|Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|West Virginia|Wisconsin|Wyoming)\s+(\d{5}(?:-\d{4})?)\b', full_text, re.IGNORECASE)
                            if full_state:
                                city = full_state.group(1).strip()
                                state_name = full_state.group(2).strip()
                                zip_code = full_state.group(3).strip()
                                # Convert state name to abbreviation
                                state_abbrev = {
                                    'washington': 'WA', 'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ',
                                    'arkansas': 'AR', 'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT',
                                    'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI',
                                    'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
                                    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME',
                                    'maryland': 'MD', 'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN',
                                    'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE',
                                    'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM',
                                    'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
                                    'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI',
                                    'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX',
                                    'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'west virginia': 'WV',
                                    'wisconsin': 'WI', 'wyoming': 'WY'
                                }
                                state = state_abbrev.get(state_name.lower(), state_name[:2].upper())

                    comma_count = address1.count(',')

                    # Now handle address splitting (AFTER we have city/state/zip)
                    if address1 and ',' in address1:
                        # Split by comma: "23525 NE Novelty Hill Rd, Suite 111"
                        if comma_count >= 3:
                            parts = address1.split(',', 2) 
                            address1 = parts[0].strip() + ", " + parts[1].strip()
                            potential_address2 = parts[2].strip()
                        else:
                            parts = address1.split(',', 1)
                            address1 = parts[0].strip()
                            potential_address2 = parts[1].strip()

                        if '\n' in potential_address2:
                            address2 = potential_address2.split('\n')[0].strip()
                            potential_city = potential_address2.split('\n')[1].strip()
                            parts2 = potential_city.split(',', 1)
                            city = parts2[0].strip()
                    
                    # Handle address with city on next line (no comma)
                    if address1 and '\n' in address1:
                        lines = address1.split('\n')
                        if len(lines) >= 2:
                            # First line is street address
                            address1 = lines[0].strip()
                            # Second line contains city, strip by lines first, then strip by comma on the second line to get city
                            potential_city = lines[1].strip()
                            potential_city3 = potential_city.split(',', 1)
                            city = potential_city3[0].strip()
                    
                    # Look for phone in full text
                    if not phone:
                        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', full_text)
                        if phone_match:
                            phone = phone_match.group(0)
                    
                    # NEW: Navigate to detail page to get fax and office hours
                    fax = ''
                    office_hours = {
                        'Monday': '',
                        'Tuesday': '',
                        'Wednesday': '',
                        'Thursday': '',
                        'Friday': '',
                        'Saturday': '',
                        'Sunday': ''
                    }
                    
                    try:
                        # Find the location detail link
                        detail_link = location_elem.find_element(By.CSS_SELECTOR, 'a[href*="/locations/"]')
                        detail_url = detail_link.get_attribute('href')
                        
                        if detail_url:
                            print(f"      Navigating to detail page: {detail_url}")
                            
                            # Save current URL to return later
                            listing_url = driver.current_url
                            
                            # Navigate to detail page
                            driver.get(detail_url)
                            time.sleep(random.uniform(2, 3))
                            
                            # Extract fax number - format: "Fax: 425-259-8600"
                            try:
                                # Method 1: Look for fax in loc-phone divs
                                fax_elems = driver.find_elements(By.CSS_SELECTOR, '.loc-phone.mb-s')
                                for elem in fax_elems:
                                    fax_text = elem.text
                                    if 'Fax:' in fax_text or 'fax' in fax_text.lower():
                                        fax_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', fax_text)
                                        if fax_match:
                                            fax = fax_match.group(1)
                                            break

                                # Method 2: Look for .fax class
                                if not fax:
                                    try:
                                        fax_elem = driver.find_element(By.CSS_SELECTOR, '.fax')
                                        fax_text = fax_elem.text
                                        fax_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', fax_text)
                                        if fax_match:
                                            fax = fax_match.group(1)
                                    except:
                                        pass

                                # Method 3: Alternative - look for any element with "Fax:" text
                                if not fax:
                                    fax_elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'Fax:')]")
                                    for elem in fax_elems:
                                        fax_text = elem.text
                                        fax_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', fax_text)
                                        if fax_match:
                                            fax = fax_match.group(1)
                                            break
                            except:
                                pass
                            
                            # Extract office hours - format: "Mon - Thur: 7:30 a.m. - 5 p.m. / Fri: 8 a.m. - 5 p.m."
                            try:
                                # Check if it's an Emergency Room (24/7)
                                facility_name_lower = facility_name.lower()
                                if 'emergency' in facility_name_lower or 'intensive care' in facility_name_lower:
                                    # Emergency rooms are open 24/7
                                    office_hours = {
                                        'Monday': '24 hours',
                                        'Tuesday': '24 hours',
                                        'Wednesday': '24 hours',
                                        'Thursday': '24 hours',
                                        'Friday': '24 hours',
                                        'Saturday': '24 hours',
                                        'Sunday': '24 hours'
                                    }
                                else:
                                    # Try multiple selectors for hours
                                    hours_text = None
                                    
                                    # Method 1: .hours-text class
                                    try:
                                        hours_elem = driver.find_element(By.CSS_SELECTOR, '.hours-text')
                                        hours_text = hours_elem.text.strip()
                                    except:
                                        pass
                                    
                                    # Method 2: .fal.fa-clock parent div (alternative)
                                    if not hours_text:
                                        try:
                                            # Look for clock icon and get parent text
                                            clock_elem = driver.find_element(By.CSS_SELECTOR, '.fal.fa-clock')
                                            parent_elem = clock_elem.find_element(By.XPATH, './parent::*')
                                            hours_text = parent_elem.text.strip()
                                        except:
                                            pass
                                    
                                    # Parse hours text if found
                                    if hours_text:
                                        office_hours = parse_office_hours(hours_text, facility_name)
                            except:
                                pass
                            
                            # Return to listing page
                            driver.get(listing_url)
                            time.sleep(random.uniform(1, 2))
                            
                            print(f"      Fax: {fax}, Hours extracted: {bool(any(office_hours.values()))}")
                    except Exception as e:
                        print(f"      Could not extract detail page data: {e}")
                
                elif 'multicare.org' in current_url:
                    # MultiCare format: "505 South 336th St, Suite 200 & 330, Federal Way, WA 98003"
                    # Address has: Street, Suite, City, State ZIP all in one line
                    
                    full_text = location_elem.text.strip()
                    
                    # If address1 already has everything, parse it
                    if address1 and ',' in address1:
                        # Parse the full address line
                        # Format: "Street, Suite, City, STATE ZIP"
                        parts = [p.strip() for p in address1.split(',')]
                        
                        # Extract state and ZIP from the last part
                        if len(parts) >= 2:
                            # Last part should have "STATE ZIP"
                            last_part = parts[-1]
                            state_zip_match = re.search(r'([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', last_part)
                            if state_zip_match:
                                state = state_zip_match.group(1)
                                zip_code = state_zip_match.group(2)
                                # City is before state/zip in the last part
                                last_part2 = parts[-2]
                                city = last_part2
                            
                            # If we have city/state/zip, find suite and street
                            if city and state and zip_code:
                                # Street address is the first part (starts with number)
                                potential_address = parts[0]

                                # Slice to avoid hidden text...the word "Location" (8 chars) keeps being scraped along with the actual address
                                address1 = potential_address[8:] if len(potential_address) > 8 else potential_address
                                
                                # Suite/Floor is in the middle parts
                                # Look for parts with suite/floor keywords
                                for part in parts[1:-1]:  # Middle parts (not first or last)
                                    if re.search(r'\b(suite|ste|floor|fl|unit|apt|room|#)\b', part, re.IGNORECASE):
                                        if "(" in part:
                                            address2 = part.split("(")[0]
                                            address1 = address1 + " (" + part.split("(")[1]
                                        else:
                                            address2 = part
                                        break
                    
                    # If still missing data, try line-by-line parsing
                    if not city or not state or not zip_code:
                        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                        
                        # Try to find street address (starts with number)
                        if not address1:
                            for line in lines:
                                if re.match(r'^\d+\s+[A-Za-z]', line):
                                    # This line might have the full address
                                    if ',' in line and re.search(r'[A-Z]{2}\s+\d{5}', line):
                                        # Parse the complete address line
                                        parts = [p.strip() for p in line.split(',')]
                                        address1 = parts[0] if parts else line
                                        
                                        # Extract city, state, zip from last part
                                        if len(parts) >= 2:
                                            last = parts[-1]
                                            csz = re.search(r'([A-Za-z\s]+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', last)
                                            if csz:
                                                city = csz.group(1).strip()
                                                state = csz.group(2).strip()
                                                zip_code = csz.group(3).strip()
                                        
                                        # Suite is in middle parts
                                        for part in parts[1:-1]:
                                            if re.search(r'\b(suite|ste|floor|fl)\b', part, re.IGNORECASE):
                                                address2 = part
                                                break
                                    else:
                                        address1 = line
                                    break
                        
                        # Find city, state, zip if still missing
                        if not city or not state or not zip_code:
                            for line in lines:
                                csz = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', line)
                                if csz:
                                    city = csz.group(1).strip()
                                    state = csz.group(2).strip()
                                    zip_code = csz.group(3).strip()
                                    break
                    
                    # Find phone
                    if not phone:
                        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', full_text)
                        if phone_match:
                            phone = phone_match.group(0)
                    
                    # NEW: Navigate to detail page to get fax and office hours (same as Swedish/Providence)
                    fax = ''
                    office_hours = {
                        'Monday': '',
                        'Tuesday': '',
                        'Wednesday': '',
                        'Thursday': '',
                        'Friday': '',
                        'Saturday': '',
                        'Sunday': ''
                    }
                    
                    try:
                        # Find the location detail link
                        detail_link = location_elem.find_element(By.CSS_SELECTOR, 'a[href*="/location/"]')
                        detail_url = detail_link.get_attribute('href')
                        
                        if detail_url:
                            print(f"      Navigating to MultiCare detail page: {detail_url}")
                            
                            # Save current URL to return later
                            listing_url = driver.current_url
                            
                            # Navigate to detail page
                            driver.get(detail_url)
                            time.sleep(random.uniform(2, 3))
                            
                            # Extract fax number
                            try:
                                # Method 1: Look for .fax class directly
                                try:
                                    fax_elem = driver.find_element(By.CSS_SELECTOR, 'div.fax span:not(.label)')
                                    fax = fax_elem.text.strip()
                                except:
                                    pass
                                
                                # Method 2: Fallback - look for parent div.fax and extract number
                                if not fax:
                                    try:
                                        fax_div = driver.find_element(By.CSS_SELECTOR, 'div.fax')
                                        fax_text = fax_div.text
                                        # Extract just the number part (not the "Fax:" label)
                                        fax_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', fax_text)
                                        if fax_match:
                                            fax = fax_match.group(1)
                                    except:
                                        pass
                            except:
                                pass
                            
                            # Extract office hours with MultiCare-specific logic
                            try:
                                # Check if it's an Emergency Room (24/7)
                                facility_name_lower = facility_name.lower()
                                if 'emergency' in facility_name_lower or 'er ' in facility_name_lower:
                                    office_hours = {
                                        'Monday': '24 hours',
                                        'Tuesday': '24 hours',
                                        'Wednesday': '24 hours',
                                        'Thursday': '24 hours',
                                        'Friday': '24 hours',
                                        'Saturday': '24 hours',
                                        'Sunday': '24 hours'
                                    }
                                else:
                                    # Look for .hours-content directly
                                    hours_text = None
                                    try:
                                        # Method 1: Find .hours-content and get all divs inside
                                        hours_content = driver.find_element(By.CSS_SELECTOR, '.hours-content')
                                        hours_divs = hours_content.find_elements(By.TAG_NAME, 'div')
                                        
                                        # Combine all div texts into one block
                                        hours_lines = [div.text.strip() for div in hours_divs if div.text.strip()]
                                        hours_text = '\n'.join(hours_lines)
                                        
                                        print(f"      DEBUG - Extracted hours text: {hours_text}")
                                        
                                        # Parse MultiCare-specific hours format
                                        if hours_text:
                                            office_hours = parse_multicare_hours(hours_text, facility_name)
                                            print(f"      DEBUG - Parsed hours: {office_hours}")
                                    except Exception as e:
                                        print(f"      DEBUG - Method 1 failed: {e}")
                                        # Method 2: Fallback - look for "General Hours" section
                                        try:
                                            general_hours_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'General Hours')]")
                                            parent = general_hours_elem.find_element(By.XPATH, './parent::*')
                                            hours_text = parent.text
                                            
                                            print(f"      DEBUG - Fallback hours text: {hours_text}")
                                            
                                            if hours_text:
                                                office_hours = parse_multicare_hours(hours_text, facility_name)
                                        except:
                                            pass
                            except:
                                pass
                            
                            # Return to listing page
                            driver.get(listing_url)
                            time.sleep(random.uniform(1, 2))
                            
                            print(f"      Fax: {fax}, Hours extracted: {bool(any(office_hours.values()))}")
                    except Exception as e:
                        print(f"      Could not extract MultiCare detail page data: {e}")

                elif 'astria.health' in current_url:
                    # Astria Health format is very straightforward:
                    # Line 1: Address 1 (e.g., "2201 E Edison Ave")
                    # Line 2: Address 2 (e.g., "Ste 2") - optional  
                    # Line 3: City, State ZIP (e.g., "Sunnyside, WA 98944")
                    # Line 4: Phone (e.g., "Phone: 509.837.3090")
                    
                    full_text = location_elem.text.strip()
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Remove facility name from lines if it's first
                    if facility_name and lines and lines[0] == facility_name:
                        lines = lines[1:]
                    
                    if len(lines) >= 2:
                        # Line 1 is always address1
                        address1 = lines[0]
                        
                        # Find the line with city, state, ZIP
                        for i, line in enumerate(lines):
                            csz_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', line)
                            if csz_match:
                                city = csz_match.group(1).strip()
                                state = csz_match.group(2).strip()
                                zip_code = csz_match.group(3).strip()
                                
                                # Everything between address1 and city/state/zip is address2
                                if i > 1:
                                    address2_lines = lines[1:i]
                                    address2 = ', '.join(address2_lines)
                                break
                        
                        # Find phone (usually has "Phone:" prefix)
                        for line in lines:
                            if 'phone' in line.lower():
                                phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', line)
                                if phone_match:
                                    phone = phone_match.group(1)
                                    break

                elif 'skagitregionalhealth.org' in current_url:
                    print(f"      DEBUG - Running Skagit Regional Health parser")
                    # Skagit format:
                    # <div class="location-item_address">
                    #   " 875 Wesley Street, Suite 210 "
                    #   " Arlington, WA 98223 "
                    # </div>
                    # Phone in <a href="tel:360-403-8158">
                    
                    try:
                        address_elem = location_elem.find_element(By.CSS_SELECTOR, '.location-item_address')
                        address_text = address_elem.text.strip()
                        lines = [line.strip(' "') for line in address_text.split('\n') if line.strip()]
                        
                        if len(lines) >= 2:
                            # First line is street address (may have suite)
                            street_line = lines[0]
                            
                            # Check if there's a comma (indicating suite/floor)
                            if ',' in street_line:
                                parts = street_line.split(',', 1)
                                address1 = parts[0].strip()
                                address2 = parts[1].strip()
                            else:
                                address1 = street_line
                            
                            # Last line has city, state, zip
                            csz_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', lines[-1])
                            if csz_match:
                                city = csz_match.group(1).strip()
                                state = csz_match.group(2).strip()
                                zip_code = csz_match.group(3).strip()
                        
                    except Exception as e:
                        print(f"      DEBUG Skagit - Error: {e}")
                    
                    # Phone from tel: link
                    if not phone:
                        try:
                            phone_elem = location_elem.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
                            phone = phone_elem.text.strip()
                        except:
                            pass

                elif 'evergreenhealth.com' in current_url:
                    # EvergreenHealth format is very clean with specific classes:
                    # <span class="street-address">12333 NE 130th Lane, Suite Tan 440</span>
                    # <span class="locality">Kirkland</span>
                    # <span class="region">WA</span>
                    # <span class="postal-code">98034</span>
                    # Address1 and Address2 are on same line, separated by comma
                    
                    try:
                        # Extract using specific class names
                        street_elem = location_elem.find_element(By.CSS_SELECTOR, '.street-address')
                        street_text = street_elem.text.strip()
                        
                        # Split by comma to separate address1 from address2
                        if ',' in street_text:
                            parts = [p.strip() for p in street_text.split(',', 1)]  # Split only on first comma
                            address1 = parts[0]
                            if len(parts) > 1:
                                address2 = parts[1]
                        else:
                            address1 = street_text
                        
                        # Get city, state, zip from their specific classes
                        try:
                            city_elem = location_elem.find_element(By.CSS_SELECTOR, '.locality')
                            city = city_elem.text.strip()
                        except:
                            pass
                        
                        try:
                            state_elem = location_elem.find_element(By.CSS_SELECTOR, '.region')
                            state = state_elem.text.strip()
                        except:
                            pass
                        
                        try:
                            zip_elem = location_elem.find_element(By.CSS_SELECTOR, '.postal-code')
                            zip_code = zip_elem.text.strip()
                        except:
                            pass
                        
                        
                    except Exception as e:
                        print(f"      DEBUG Evergreen - Error: {e}")
                    
                    # Phone from MainTelephoneNumber class
                    if not phone:
                        try:
                            phone_elem = location_elem.find_element(By.CSS_SELECTOR, '.MainTelephoneNumber')
                            phone = phone_elem.text.strip()
                        except:
                            pass

                elif 'kaiserpermanente.org' in current_url:
                    # Kaiser format:
                    # Line 1: Street address, optionally with suite (e.g., "4301 S Pine St, Ste 301,")
                    # Line 2: City, State ZIP (e.g., "Tacoma, WA, 98409")
                    # Phone is in a link
                    
                    full_text = location_elem.text.strip()
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Remove facility name from lines if it's first
                    if facility_name and lines and lines[0] == facility_name:
                        lines = lines[1:]
                    
                    # Find the line with city, state, ZIP
                    city_line_idx = None
                    for i, line in enumerate(lines):
                        csz_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2}),?\s+(\d{5}(?:-\d{4})?)', line)
                        if csz_match:
                            city = csz_match.group(1).strip()
                            state = csz_match.group(2).strip()
                            zip_code = csz_match.group(3).strip()
                            city_line_idx = i
                            break
                    
                    if city_line_idx is not None and city_line_idx > 0:
                        # Everything before city line is address
                        address_lines = lines[:city_line_idx]
                        
                        # Join all address lines and parse
                        full_address = ' '.join(address_lines)
                        
                        # Check if there's a suite/floor/ste in the address
                        # Common patterns: "Ste 301", "Suite 200", "Ste. 301"
                        suite_match = re.search(r'^(.+?),?\s+((?:\d+(?:st|nd|rd|th)?\s*(?:Floor|Fl\.?)|(?:Suite|Ste\.?|Unit|#)\s*\d+[A-Z]?))', full_address, re.IGNORECASE)
                        
                        if suite_match:
                            # Address has suite
                            address1 = suite_match.group(1).strip(' ,')
                            address2 = suite_match.group(2).strip(' ,')
                        else:
                            # No suite, entire thing is address1
                            address1 = full_address.strip(' ,')
                    
                    # Phone
                    if not phone:
                        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', full_text)
                        if phone_match:
                            phone = phone_match.group(1)

                elif 'confluencehealth.org' in current_url:
                    # Confluence Health format:
                    # <address> tag contains <span> elements with:
                    # - Street address
                    # - City, State ZIP
                    # Phone is in a separate span after address
                    
                    try:
                        address_elem = location_elem.find_element(By.TAG_NAME, 'address')
                        spans = address_elem.find_elements(By.TAG_NAME, 'span')
                        
                        # Extract text from all spans
                        address_parts = [span.text.strip() for span in spans if span.text.strip()]
                        
                        if len(address_parts) >= 2:
                            # First span is street address
                            address1 = address_parts[0]
                            
                            # Last span typically has city, state, zip
                            for part in address_parts:
                                csz_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', part)
                                if csz_match:
                                    city = csz_match.group(1).strip()
                                    state = csz_match.group(2).strip()
                                    zip_code = csz_match.group(3).strip()
                                    break
                            
                            # Middle parts (if any) are address2
                            if len(address_parts) > 2 and city:
                                # Everything between address1 and the city/state/zip line
                                address2_parts = []
                                for i, part in enumerate(address_parts[1:], 1):
                                    if city not in part:
                                        address2_parts.append(part)
                                    else:
                                        break
                                if address2_parts:
                                    address2 = ', '.join(address2_parts)
                        
                        
                    except Exception as e:
                        print(f"      DEBUG Confluence - Error: {e}")
                    
                    # Phone - look for phone number in the element
                    if not phone:
                        full_text = location_elem.text
                        phone_match = re.search(r'(\d{3}\.\d{3}\.\d{4})', full_text)
                        if phone_match:
                            phone = phone_match.group(1)

                elif 'peacehealth.org' in current_url:
                    # PeaceHealth format is very clean:
                    # Inside <address> tag:
                    # Line 1: Street address (e.g., "3333 RiverBend Dr")
                    # Line 2: City, State ZIP (e.g., "Springfield, OR 97477")
                    # Phone is in <a href="tel:...">
                    
                    # Try to find the <address> element
                    try:
                        address_elem = location_elem.find_element(By.TAG_NAME, 'address')
                        address_text = address_elem.text.strip()
                        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
                        
                        
                        if len(lines) >= 2:
                            # First line is street address
                            address1 = lines[0]
                            
                            # Last line has city, state, zip
                            csz_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', lines[-1])
                            if csz_match:
                                city = csz_match.group(1).strip()
                                state = csz_match.group(2).strip()
                                zip_code = csz_match.group(3).strip()
                            
                            # Middle lines (if any) are address2
                            if len(lines) > 2:
                                address2_lines = lines[1:-1]
                                address2 = ', '.join(address2_lines)
                        
                    except Exception as e:
                        print(f"      DEBUG PeaceHealth - Error finding address element: {e}")
                    
                    # Phone is in a tel: link
                    if not phone:
                        full_text = location_elem.text
                        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', full_text)
                        if phone_match:
                            phone = phone_match.group(1)

                else:
                    # Generic parsing for unknown sites
                    full_text = location_elem.text.strip()
                    
                    # Try to parse from full text
                    parsed = parse_address_block(full_text)
                    if not address1:
                        address1 = parsed['address1']
                    if not city:
                        city = parsed['city']
                    if not state:
                        state = parsed['state']
                    if not zip_code:
                        zip_code = parsed['zip']
                
                # Clean and validate all address fields
                address1, address2, city, state, zip_code = clean_address_fields(
                    address1, address2, city, state, zip_code
                )
                
                # Format phone number to (999) 999-9999
                phone = format_phone_number(phone)

                # Format fax number to (999) 999-9999
                fax = format_phone_number(fax)
                
                # Only add if we found at least a name
                if facility_name:
                    location_data = {
                        'Facility Name': facility_name,
                        'Address 1': address1,
                        'Address 2': address2,
                        'City': city,
                        'State': state,
                        'ZIP': zip_code,
                        'Phone': phone,
                        'Fax': fax,
                        'Monday': office_hours.get('Monday', ''),
                        'Tuesday': office_hours.get('Tuesday', ''),
                        'Wednesday': office_hours.get('Wednesday', ''),
                        'Thursday': office_hours.get('Thursday', ''),
                        'Friday': office_hours.get('Friday', ''),
                        'Saturday': office_hours.get('Saturday', ''),
                        'Sunday': office_hours.get('Sunday', '')
                    }
                    
                    locations.append(location_data)
                    
                    # Add small random delay between processing items (human-like behavior)
                    if (idx + 1) % config.ITEM_BATCH_SIZE == 0:
                        time.sleep(random.uniform(config.ITEM_BATCH_DELAY_MIN, config.ITEM_BATCH_DELAY_MAX))
                
                # Increment index for next iteration
                idx += 1
                    
            except Exception as e:
                # Silently skip problematic elements and move to next
                print(f"      Error processing location {idx + 1}: {e}")
                idx += 1
                continue
    
    except Exception as e:
        print(f"      Error finding location elements: {e}")
    
    return locations

def save_to_csv(locations, filename='medicine_locations.csv'):
    """
    Save the extracted location data to a CSV file.
    
    Args:
        locations: List of dictionaries containing location data
        filename: Name of the output CSV file (default: 'medicine_locations.csv')
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    if not locations:
        print("No locations to save!")
        return False
    
    fieldnames = ['Facility Name', 'Address 1', 'Address 2', 'City', 'State', 'ZIP', 'Phone', 'Fax', 
                  'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
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


def save_to_csv_with_separators(locations_by_url, filename='medicine_locations.csv'):
    """
    Save location data to CSV with URL separators and indentation.
    
    Args:
        locations_by_url: List of dicts with 'url', 'url_index', and 'locations' keys
        filename: Name of the output CSV file
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    if not locations_by_url:
        print("No locations to save!")
        return False
    
    fieldnames = ['Facility Name', 'Address 1', 'Address 2', 'City', 'State', 'ZIP', 'Phone', 'Fax',
                  'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write locations grouped by URL
            for group in locations_by_url:
                url = group['url']
                url_index = group['url_index']
                locations = group['locations']
                
                # Write URL separator row
                separator_row = {
                    'Facility Name': f"URL {url_index}: {url}",
                    'Address 1': '',
                    'Address 2': '',
                    'City': '',
                    'State': '',
                    'ZIP': '',
                    'Phone': '',
                    'Fax': '',
                    'Monday': '',
                    'Tuesday': '',
                    'Wednesday': '',
                    'Thursday': '',
                    'Friday': '',
                    'Saturday': '',
                    'Sunday': ''
                }
                writer.writerow(separator_row)
                
                # Write empty row for spacing
                empty_row = {field: '' for field in fieldnames}
                writer.writerow(empty_row)
                
                # Write locations for this URL (with indent via leading space)
                for location in locations:
                    # Add a leading space to facility name for indentation
                    indented_location = location.copy()
                    indented_location['Facility Name'] = '  ' + location.get('Facility Name', '')
                    writer.writerow(indented_location)
                
                # Write empty row between URL groups
                writer.writerow(empty_row)
        
        total_count = sum(len(group['locations']) for group in locations_by_url)
        print(f"\nSuccessfully saved {total_count} locations from {len(locations_by_url)} URLs to {filename}")
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
        
    


