"""
Main script to run the UW Medicine location scraper.

This script imports the scraper module and configuration, then runs the scraping process.

Usage:
    python main.py
"""

from uw_locations_scrape import (
    setup_driver,
    extract_location_data,
    save_to_csv,
    save_page_source
)
import config


def main():
    """
    Main function to run the scraper using settings from config.py.
    """
    print("=" * 60)
    print("UW Medicine Location Scraper")
    print("=" * 60)
    print(f"\nTarget URL: {config.TARGET_URL}")
    print(f"Output file: {config.OUTPUT_FILENAME}")
    print(f"Headless mode: {config.HEADLESS_MODE}")
    print(f"User agent: {config.USER_AGENT_TYPE}")
    if config.USE_PROXY:
        print(f"Proxy: {config.PROXY_SERVER}")
    print("=" * 60)
    
    # Set up the browser driver
    print("\nSetting up Chrome driver with anti-detection measures...")
    driver = setup_driver()
    
    try:
        # Extract location data
        print("\nExtracting location data...")
        locations = extract_location_data(driver, config.TARGET_URL)
        
        # Check if we got any data
        if locations:
            # Save to CSV
            success = save_to_csv(locations, filename=config.OUTPUT_FILENAME)
            
            if success:
                print("\n" + "=" * 60)
                print("✓ Scraping completed successfully!")
                print(f"✓ Data saved to: {config.OUTPUT_FILENAME}")
                print(f"✓ Total locations extracted: {len(locations)}")
                print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠ No locations were extracted.")
            print("⚠ The page structure may have changed.")
            print("⚠ Please inspect the page HTML and update the CSS selectors in config.py")
            print("=" * 60)
            
            # Save the page source for debugging
            save_page_source(driver)
    
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        
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