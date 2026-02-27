"""
Pagination utilities for handling multi-page scraping.

This module provides functions to detect and handle various types of pagination:
- Next/Previous buttons
- Load More buttons  
- Page number links
"""

from selenium.webdriver.common.by import By
import time
import random
import config


def find_pagination_element(driver):
    """
    Try to find pagination elements (Next button, Load More, etc.) on the page.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        tuple: (element, pagination_type) or (None, None) if no pagination found
               pagination_type can be: 'next_button', 'load_more_button', 'page_numbers'
    """
    # Try to find "Next" button
    for selector in config.PAGINATION_SELECTORS['next_button']:
        try:
            # Special handling for :contains() which isn't valid CSS
            if ':contains(' in selector:
                text = selector.split("'")[1]  # Extract text from :contains('text')
                tag = selector.split(':')[0]   # Extract tag name
                
                elements = driver.find_elements(By.TAG_NAME, tag)
                for elem in elements:
                    if text.lower() in elem.text.lower() and elem.is_displayed():
                        # Check if button is enabled (not disabled or at last page)
                        classes = elem.get_attribute('class') or ''
                        if (elem.get_attribute('disabled') or 
                            'disabled' in classes or 
                            'inactive' in classes or
                            elem.get_attribute('aria-disabled') == 'true'):
                            continue
                        return (elem, 'next_button')
            else:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem.is_displayed():
                    # Check if button is enabled
                    classes = elem.get_attribute('class') or ''
                    if (elem.get_attribute('disabled') or 
                        'disabled' in classes or 
                        'inactive' in classes or
                        elem.get_attribute('aria-disabled') == 'true'):
                        continue
                    return (elem, 'next_button')
        except:
            continue
    
    # Try to find "Load More" button
    for selector in config.PAGINATION_SELECTORS['load_more_button']:
        try:
            if ':contains(' in selector:
                text = selector.split("'")[1]
                tag = selector.split(':')[0]
                
                elements = driver.find_elements(By.TAG_NAME, tag)
                for elem in elements:
                    if text.lower() in elem.text.lower() and elem.is_displayed():
                        return (elem, 'load_more_button')
            else:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                if elem.is_displayed():
                    return (elem, 'load_more_button')
        except:
            continue
    
    # Try to find page number links
    for selector in config.PAGINATION_SELECTORS['page_numbers']:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                # Look for a "next" page link or the next number
                for elem in elements:
                    if elem.is_displayed() and ('next' in elem.text.lower() or elem.text.isdigit()):
                        return (elem, 'page_numbers')
        except:
            continue
    
    return (None, None)


def handle_pagination(driver, current_page):
    """
    Handle clicking to the next page of results.
    
    Args:
        driver: Selenium WebDriver instance
        current_page: Current page number
    
    Returns:
        bool: True if successfully navigated to next page, False if no more pages
    """
    try:
        # Find pagination element
        elem, pagination_type = find_pagination_element(driver)
        
        if not elem:
            print(f"    No pagination element found (tried all selectors)")
            return False
        
        # Check if element is clickable
        classes = elem.get_attribute('class') or ''
        href = elem.get_attribute('href') or ''
        
        print(f"    Found pagination: {pagination_type}")
        print(f"      Element: {elem.tag_name}, Classes: '{classes}'")
        if href:
            print(f"      Href: {href}")
        
        # Scroll to element to make sure it's in view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Save current URL to detect if page changed
        current_url = driver.current_url
        
        # Click the pagination element
        try:
            elem.click()
            print(f"    ✓ Clicked pagination element")
        except:
            # If regular click doesn't work, try JavaScript click
            driver.execute_script("arguments[0].click();", elem)
            print(f"    ✓ Clicked pagination element (via JavaScript)")
        
        # Wait for page to load
        time.sleep(random.uniform(config.PAGINATION_DELAY_MIN, config.PAGINATION_DELAY_MAX))
        
        # Check if page changed (URL changed or new content loaded)
        if pagination_type == 'load_more_button':
            # For "Load More", page doesn't change but content is added
            # Just wait for new content to load
            time.sleep(2)
            return True
        else:
            # For navigation pagination, check if URL changed
            new_url = driver.current_url
            if new_url != current_url:
                print(f"    ✓ URL changed: {new_url}")
                return True
            else:
                print(f"    ⚠ URL didn't change - might be at last page or click failed")
                return False
    
    except Exception as e:
        print(f"    ✗ Error handling pagination: {e}")
        return False