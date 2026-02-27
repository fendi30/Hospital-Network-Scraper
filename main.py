"""
Main script to run the UW Medicine location scraper.

This script imports the scraper module and configuration, then runs the scraping process.

Usage:
    python main.py
"""

from scraper import (
    setup_driver,
    extract_location_data,
    save_to_csv,
    save_to_csv_with_separators,
    save_page_source
)
import config


def main():
    """
    Main function to run the scraper using settings from config.py.
    Supports scraping multiple URLs.
    """
    print("=" * 60)
    print("UW Medicine Location Scraper")
    print("=" * 60)
    print(f"\nTarget URLs: {len(config.TARGET_URLS)}")
    for i, url in enumerate(config.TARGET_URLS, 1):
        print(f"  {i}. {url}")
    print(f"Output file: {config.OUTPUT_FILENAME}")
    print(f"Headless mode: {config.HEADLESS_MODE}")
    print(f"User agent: {config.USER_AGENT_TYPE}")
    if config.USE_PROXY:
        print(f"Proxy: {config.PROXY_SERVER}")
    print("=" * 60)
    
    # Set up the browser driver (reuse for all URLs)
    print("\nSetting up Chrome driver with anti-detection measures...")
    driver = setup_driver()
    
    # Store all locations from all URLs (grouped by URL)
    locations_by_url = []
    
    try:
        # Loop through each URL
        for url_index, url in enumerate(config.TARGET_URLS, 1):
            print(f"\n{'=' * 60}")
            print(f"SCRAPING URL {url_index} of {len(config.TARGET_URLS)}")
            print(f"{'=' * 60}")
            
            # Extract location data from this URL
            print(f"\nExtracting location data from: {url}")
            locations = extract_location_data(driver, url)
            
            if locations:
                print(f"✓ Found {len(locations)} locations from this URL")
                # Store locations with their URL
                locations_by_url.append({
                    'url': url,
                    'url_index': url_index,
                    'locations': locations
                })
            else:
                print(f"⚠ No locations found from this URL")
            
            # Add a delay between URLs to be polite
            if url_index < len(config.TARGET_URLS):
                print("\nWaiting before next URL...")
                import time
                import random
                time.sleep(random.uniform(3, 5))
        
        # Save all collected data
        print(f"\n{'=' * 60}")
        print("SAVING RESULTS")
        print(f"{'=' * 60}")
        
        if locations_by_url:
            # Count total locations
            total_count = sum(len(group['locations']) for group in locations_by_url)
            print(f"\nTotal locations found: {total_count}")
            
            # Save to CSV with URL separators
            success = save_to_csv_with_separators(locations_by_url, filename=config.OUTPUT_FILENAME)
            
            if success:
                print("\n" + "=" * 60)
                print("✓ Scraping completed successfully!")
                print(f"✓ Data saved to: {config.OUTPUT_FILENAME}")
                print(f"✓ Total locations: {total_count}")
                print(f"✓ URLs scraped: {len(locations_by_url)}")
                print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠ No locations were extracted from any URL.")
            print("⚠ The page structure may have changed.")
            print("⚠ Please run: python inspect_html.py")
            print("⚠ Then update the CSS selectors in config.py")
            print("=" * 60)
            
            # Save the page source for debugging
            save_page_source(driver)
    
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to save page source for debugging
        try:
            save_page_source(driver)
        except:
            pass
    
    finally:
        # Always close the browser
        print("\nClosing browser...")
        driver.quit()
        print("Done!")


if __name__ == "__main__":
    main()