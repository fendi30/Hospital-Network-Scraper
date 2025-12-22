"""
Configuration file for the UW Medicine scraper.

Modify these settings to customize the scraper's behavior and security features.
"""

# ============================================================================
# TARGET CONFIGURATION
# ============================================================================

# URL to scrape
TARGET_URL = "https://www.uwmedicine.org/search/locations"

# Output filename for CSV
OUTPUT_FILENAME = "uw_medicine_locations.csv"


# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================

# Run browser in headless mode (no visible window)
HEADLESS_MODE = False

# Disable image loading for faster scraping
DISABLE_IMAGES = False

# Maximum time to wait for page elements (seconds)
PAGE_LOAD_TIMEOUT = 10


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
INITIAL_DELAY_MIN = 2.0
INITIAL_DELAY_MAX = 4.0

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
    ".location-item",
    ".location-card",
    "[data-location]",
    ".clinic-card",
    ".facility-item"
]

# Field selectors (will try each until one works)
SELECTORS = {
    'facility_name': [
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
        ".address-line-2",
        ".extended-address",
        ".address2",
        "[class*='suite']",
        "[class*='unit']"
    ],
    'city': [
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
        ".phone",
        "[itemprop='telephone']",
        "a[href^='tel:']",
        ".tel",
        "[class*='phone']",
        "[class*='telephone']"
    ]
}