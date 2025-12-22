"""
HTML Inspector - Run this to identify the correct CSS selectors

This script will:
1. Load the UW Medicine locations page
2. Extract and display the HTML structure of location cards
3. Help you identify the correct selectors for addresses

Usage:
    python inspect_html.py
"""

from uw_locations_scrape import setup_driver
from selenium.webdriver.common.by import By
import time
import config


def inspect_page_structure():
    """
    Load the page and print out the HTML structure to help identify selectors.
    """
    print("=" * 80)
    print("HTML STRUCTURE INSPECTOR")
    print("=" * 80)
    
    driver = setup_driver(headless=False)  # Keep visible so you can see it working
    
    try:
        print(f"\nLoading: {config.TARGET_URL}")
        driver.get(config.TARGET_URL)
        time.sleep(5)  # Wait for page to load
        
        # Try to find location elements with various selectors
        possible_selectors = [
            "[class*='location']",
            "[class*='card']",
            "[class*='result']",
            "[class*='clinic']",
            "[class*='facility']",
            ".search-result",
            "[data-location]",
            "article",
            ".item"
        ]
        
        print("\nSearching for location elements...\n")
        
        all_elements = []
        for selector in possible_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"✓ Found {len(elements)} elements with selector: {selector}")
                all_elements.extend(elements)
        
        # Remove duplicates
        all_elements = list(set(all_elements))
        
        if not all_elements:
            print("\n⚠ No location elements found. Trying to find any repeated patterns...")
            # Look at the body structure
            body_html = driver.find_element(By.TAG_NAME, "body").get_attribute('innerHTML')
            print("\nSaving full page HTML to 'full_page_structure.html'")
            with open('full_page_structure.html', 'w', encoding='utf-8') as f:
                f.write(body_html)
            print("✓ Saved! Open this file to inspect the structure.")
            return
        
        print(f"\n{'=' * 80}")
        print(f"INSPECTING FIRST 3 LOCATION CARDS")
        print(f"{'=' * 80}\n")
        
        # Print detailed HTML for first 3 unique location cards
        seen_html = set()
        count = 0
        
        for elem in all_elements:
            if count >= 3:
                break
                
            html = elem.get_attribute('outerHTML')
            
            # Skip if we've seen very similar HTML
            if html[:200] in seen_html:
                continue
            
            seen_html.add(html[:200])
            count += 1
            
            print(f"\n{'─' * 80}")
            print(f"LOCATION CARD #{count}")
            print(f"{'─' * 80}")
            
            # Print the HTML (truncated if too long)
            if len(html) > 3000:
                print(html[:3000])
                print(f"\n... (truncated, full HTML is {len(html)} characters)")
            else:
                print(html)
            
            # Try to find specific elements within this card
            print(f"\n{'─' * 40}")
            print("ANALYZING THIS CARD:")
            print(f"{'─' * 40}")
            
            # Look for address-related elements
            try:
                # Try to find address elements
                address_elements = elem.find_elements(By.CSS_SELECTOR, "[class*='address'], [class*='street'], [class*='city'], [itemprop*='address']")
                if address_elements:
                    print(f"\n✓ Found {len(address_elements)} address-related elements:")
                    for i, addr_elem in enumerate(address_elements[:5], 1):
                        classes = addr_elem.get_attribute('class')
                        text = addr_elem.text.strip()[:100]
                        print(f"  {i}. Class: '{classes}' | Text: '{text}'")
                
                # Look for any text that might be an address
                all_text = elem.text.strip().split('\n')
                print(f"\n📝 All text in this card:")
                for i, line in enumerate(all_text[:15], 1):  # First 15 lines
                    if line.strip():
                        print(f"  {i}. {line.strip()}")
            
            except Exception as e:
                print(f"Error analyzing card: {e}")
            
            print("\n")
        
        # Save full HTML for manual inspection
        print(f"\n{'=' * 80}")
        print("SAVING FULL PAGE HTML")
        print(f"{'=' * 80}")
        
        with open('page_structure.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Saved full page HTML to 'page_structure.html'")
        
        print("\n" + "=" * 80)
        print("INSTRUCTIONS:")
        print("=" * 80)
        print("""
1. Review the HTML structure printed above
2. Look for the CSS classes/attributes that contain:
   - Address line 1 (street address)
   - Address line 2 (suite/floor)
   - City
   - State
   - ZIP code
3. Update the selectors in config.py with the correct classes
4. Open 'page_structure.html' in a browser if you need to see more

Example: If you see something like:
  <span class="address-street">123 Main St</span>
  
Then add to config.py SELECTORS:
  'address1': ['.address-street', '.street-address']
""")
        print("=" * 80)
        
    finally:
        input("\nPress Enter to close the browser...")
        driver.quit()


if __name__ == "__main__":
    inspect_page_structure()