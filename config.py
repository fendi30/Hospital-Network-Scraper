"""
Configuration file for the Medicine scraper.

Modify these settings to customize the scraper's behavior and security features.
"""

# ============================================================================
# TARGET CONFIGURATION
# ============================================================================

# URLs to scrape - you can add multiple URLs here
TARGET_URLS = [
    "https://www.multicare.org/find-a-location/?page_num=7",
    # Add more URLs below:
    # "https://www.example.com/locations",
    # "https://www.another-site.com/find-us",
]

# Output filename for CSV
OUTPUT_FILENAME = "medicine_locations.csv"


# ============================================================================
# PAGINATION CONFIGURATION
# ============================================================================

# Enable automatic pagination detection and handling
ENABLE_PAGINATION = True

# Maximum number of pages to scrape per URL (safety limit)
MAX_PAGES_PER_URL = 1

# Common pagination selectors (will try each until one works)
PAGINATION_SELECTORS = {
    # "Next" button selectors
    'next_button': [
        ".right_button ",
        "a.next.page-numbers",
        ".next.page-numbers",
        ".next-button",
        ".pagination-next",
        "a.next-button",
        "a:contains('Next')",
        "button:contains('Next')",
        "[aria-label*='Next']",
        ".next",
        "a[rel='next']",
        ".arrow-right",
        "[class*='next']"
    ],
    
    # "Load More" button selectors
    'load_more_button': [
        "button:contains('Load More')",
        "a:contains('Load More')",
        "button:contains('Show More')",
        "[class*='load-more']",
        "[class*='show-more']"
    ],
    
    # Page number links (for sites with numbered pagination)
    'page_numbers': [
        ".pagination a",
        "[class*='pagination'] a",
        "[class*='page-link']"
    ]
}

# Delay between page navigations (seconds)
PAGINATION_DELAY_MIN = 1.0
PAGINATION_DELAY_MAX = 3.0


# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================

# Run browser in headless mode (no visible window)
HEADLESS_MODE = False

# Disable image loading for faster scraping
DISABLE_IMAGES = False

# Maximum time to wait for page elements (seconds)
PAGE_LOAD_TIMEOUT = 8


# ============================================================================
# ANTI-DETECTION CONFIGURATION
# ============================================================================

# User agent to use (appears as this browser)
# Options: 'windows_chrome', 'mac_chrome', 'linux_chrome', 'random'
USER_AGENT_TYPE = 'windows_chrome'

# Custom user agents for rotation
USER_AGENTS = {
    'windows_chrome': (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    'mac_chrome': (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    'linux_chrome': (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Window size (common resolutions: 1920x1080, 1366x768, 1440x900)
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080


# ============================================================================
# TIMING CONFIGURATION (for human-like behavior)
# ============================================================================

# Random delay range after page load (seconds)
INITIAL_DELAY_MIN = 1.0
INITIAL_DELAY_MAX = 3.0

# Random delay range between scrolls (seconds)
SCROLL_DELAY_MIN = 0.1
SCROLL_DELAY_MAX = 0.3

# Scroll increment range (pixels)
SCROLL_INCREMENT_MIN = 300
SCROLL_INCREMENT_MAX = 500

# Delay after processing every N items (seconds)
ITEM_BATCH_SIZE = 10
ITEM_BATCH_DELAY_MIN = 0.5
ITEM_BATCH_DELAY_MAX = 1.5


# ============================================================================
# PROXY CONFIGURATION (Optional - for advanced users)
# ============================================================================

# Enable proxy
USE_PROXY = False

# Proxy server address (format: "http://proxy-server:port")
PROXY_SERVER = None

# Examples:
# PROXY_SERVER = "http://proxy.example.com:8080"
# PROXY_SERVER = "socks5://127.0.0.1:9050"  # For Tor


# ============================================================================
# CSS SELECTORS (Customize based on actual page structure)
# ============================================================================

# Main location container selectors (will try each until one works)
LOCATION_CONTAINER_SELECTORS = [
    ".LocationInfoWrap",
    ".columns-11",
    ".flex-top",
    ".cta-listing.locations",
    ".h-auto",
    ".ph-evm-finder-result",
    ".provider-locations > div",
    ".location_cards",
    ".location-list",
    ".location-list-card",
    ".location-card-distance",
    ".location-item",
    ".location-card",
    "[data-location]",
    ".clinic-card",
    ".facility-item"
]

# Field selectors (will try each until one works)
SELECTORS = {
    'facility_name': [
        ".title-style-5",
        "a[href*='astria']",
        "a",
        "h2 a",
        ".location-list-card__name",
        "h2.location-list-card__name",
        ".location-card-distance > a",
        ".location-name",
        ".facility-name",
        "h2",
        "h3",
        ".title",
        ".clinic-title",
        "a[href*='locations']",
        "[class*='name']"
    ],
    'address1': [
        # Try getting full address block first, then parse it
        ".br",
        ".location-list-card__address",
        ".address",
        ".location-list-card__address .address",
        ".location-address",
        ".location-card-distance > div:nth-of-type(1)",
        ".address",
        "[class*='address']",
        ".street-address",
        "[itemprop='streetAddress']",
        ".address-line-1",
        ".address1",
        "[class*='street']",
        "address",  # HTML address tag
        "[class*='location-address']",
        "p:has(text)",  # Paragraph containing text
        "span:has(text)"  # Span containing text
    ],
    'address2': [
        ".br",
        ".address-line-2",
        ".extended-address",
        ".address2",
        "[class*='suite']",
        "[class*='unit']"
    ],
    'city': [
        ".location-card-distance > div:nth-of-type(2)",
        ".locality",
        "[itemprop='addressLocality']",
        ".city",
        "[class*='city']"
    ],
    'state': [
        ".region",
        "[itemprop='addressRegion']",
        ".state",
        "[class*='state']",
        "[class*='region']"
    ],
    'zip': [
        ".postal-code",
        "[itemprop='postalCode']",
        ".zip",
        ".zipcode",
        "[class*='postal']",
        "[class*='zip']"
    ],
    'phone': [
        ".location-card-distance a[href^='tel:']",
        ".phone",
        "[itemprop='telephone']",
        "a[href^='tel:']",
        ".tel",
        "[class*='phone']",
        "[class*='telephone']"
    ]

}
