# Medicine Location Scraper

A Python web scraper that extracts comprehensive location information from healthcare networks and saves it to a CSV file, including detailed office hours and contact information.

## Project Structure

```
├── main.py              # Main script to run the scraper
├── scraper.py           # Scraper functions and utilities
├── config.py            # Configuration file (customize settings here)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Features

- Uses Selenium for browser automation (not blocked by robots.txt)
- Automatically manages ChromeDriver installation
- **Advanced anti-detection measures** (see Security Features below)
- **Smart address parser** - Automatically extracts addresses even when they're in one block
- **Automatic pagination handling** - Scrapes all pages, handles Next buttons, Load More buttons, and page numbers
- **Detail page navigation** - Automatically visits individual location pages to extract comprehensive data
- **Office hours extraction** - Parses complex office hour formats with intelligent edge case handling
- **Fax number extraction** - Captures fax numbers from detail pages
- **Multi-site support** - Custom parsers for Swedish/Providence, MultiCare, Kaiser Permanente, and more
- Clean, modular code structure
- Well-commented and easy to customize
- Exports data to CSV format with extended fields
- Error handling and logging

## Security Features

The scraper includes multiple anti-detection measures to appear as a normal user:

### Browser Fingerprint Protection
- Removes automation flags (`navigator.webdriver`)
- Sets realistic user agent (appears as Chrome on Windows)
- Overrides navigator properties to match real browsers
- Disables webdriver-specific features

### Human-Like Behavior
- Random delays between actions (2-4 seconds)
- Simulates natural scrolling patterns
- Variable timing between processing items
- Realistic window size and screen resolution
- Polite delays when navigating between pages (1-3 seconds)

### Network & Privacy
- Normal browser headers and settings
- Cookie and JavaScript enabled (like real users)
- English (US) language settings
- Disables automation detection features

These measures help the scraper avoid detection by anti-bot systems while remaining ethical for personal use.

## Installation

1. Make sure you have Python 3.7+ installed

2. Install the required packages:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install selenium webdriver-manager
```

## Usage

### Quick Start

Simply run the main script:
```bash
python main.py  
```

The script will:
1. Open Chrome browser (you'll see it navigate to the page)
2. Extract all location data from all configured URLs
3. Navigate to individual location detail pages (for Swedish/Providence/MultiCare)
4. Extract comprehensive information including office hours and fax numbers
5. Remove duplicates across all URLs
6. Save results to `medicine_locations.csv`

### Scraping Multiple URLs

You can scrape multiple websites in one run - just add URLs to the `TARGET_URLS` list in `config.py`:

```python
TARGET_URLS = [
    "https://www.swedish.org/locations?postal=56966&latlng=0%2c0&page=1",
    "https://www.multicare.org/find-a-location/?page_num=1",
    "https://www.providence.org/locations",
]
```

The scraper will:
- Visit each URL sequentially
- Extract locations from each
- **Automatically handle pagination** (see below)
- **Navigate to detail pages** for comprehensive data (Swedish/Providence/MultiCare)
- Combine all results into one CSV file
- Automatically remove duplicates
- Add delays between URLs (3-5 seconds)

***PRO TIP 1: Scrape only one URL at a time unless you know for certain that the HTML elements and parser functions for all URLS are up to date.***

***PRO TIP 2: In addition to pro tip 1, when testing the scraper on a new URL, don't try to scrape the entire URL network at once - try to scrape at most 1 or 2 pages first and see what the output is like. It will save you a lot of time should you need to fix any HTML selectors and account for any edge cases.*** 

### Detail Page Navigation

For supported healthcare networks (Swedish, Providence, MultiCare), the scraper automatically:

1. **Finds the location detail link** on the listing page
2. **Navigates to the detail page** to extract:
   - Fax numbers
   - Complete office hours (Monday-Sunday)
   - Emergency room detection (auto-fills "24 hours" for ERs)
3. **Returns to listing page** to continue scraping
4. **Maintains proper delays** (2-3 seconds per navigation)

**Example output:**
```
Navigating to detail page: https://www.swedish.org/locations/swedish-issaquah/
Fax: (425) 313-4321, Hours extracted: True
```

**Note:** This makes scraping slower (~5-10 seconds per location) but provides complete data.

### Automatic Pagination Handling

The scraper **automatically detects and handles pagination** for sites with multiple pages of locations.

**Supported pagination types:**
- ✅ **Next/Previous buttons** - Clicks "Next" to go to the next page
- ✅ **Page numbers** - Clicks through numbered pagination (1, 2, 3...)
- ✅ **Load More buttons** - Clicks "Load More" or "Show More" to reveal more results
- ✅ **Mixed single and multi-page sites** - Works for both!

**How it works:**
1. Scrapes all locations from the current page (including detail page navigation)
2. Looks for pagination elements (Next button, Load More, etc.)
3. Clicks to next page and waits politely (2-4 seconds)
4. Repeats until no more pages are found or hits `MAX_PAGES_PER_URL` limit
5. Combines all results

**Configuration:**

In `config.py`, you can control pagination behavior:

```python
# Enable/disable pagination
ENABLE_PAGINATION = True  # Set to False to only scrape first page

# Maximum pages to scrape per URL (safety limit)
MAX_PAGES_PER_URL = 100  # Increase if you have more than 100 pages

# Delays between pages (be polite to servers!)
PAGINATION_DELAY_MIN = 1.0  # Minimum delay in seconds
PAGINATION_DELAY_MAX = 3.0  # Maximum delay in seconds
```

**Example output:**
```
📄 Page 1
   Found 20 location elements on this page
   Navigating to detail page: https://...
   Fax: (206) 555-1234, Hours extracted: True
   ...
   ✓ Extracted 20 locations from this page
   Looking for next page...
   Found pagination: next_button

📄 Page 2
   Found 20 location elements on this page
   ...
   ✓ Extracted 20 locations from this page

Total locations from all pages: 1,058
```

If pagination isn't working for a specific site, you can customize the selectors in `config.py` under `PAGINATION_SELECTORS`.

### Office Hours Extraction

The scraper includes sophisticated office hours parsing that handles numerous edge cases:

**Supported formats:**
- ✅ **Range format:** "Monday - Friday: 8am - 5pm"
- ✅ **Individual days:** "Mon: 8am-5pm / Tue: 9am-6pm"
- ✅ **Ampersand format:** "Monday & Wednesday: 8am - 5pm"
- ✅ **Dash without spaces:** "Tuesday-Wednesday: 8am-4:30pm"
- ✅ **7 days a week:** "8am - 8pm, 7 days a week"
- ✅ **Multi-line hours:** Weekday and weekend hours on separate lines
- ✅ **Break times:** "8am - 12pm & 1pm - 5pm"

**Smart filtering:**
- ✅ **Ignores disclaimers:** "Appointments only", "Provider hours may vary", "Please call"
- ✅ **Ignores holidays:** "Closed Thanksgiving", "Christmas Eve: 9am-1pm"
- ✅ **Ignores special events:** "Second Thursday of every month"
- ✅ **Emergency room detection:** Automatically sets "24 hours" for all days

**MultiCare-specific handling:**
- Priority system: Regular hours > Clinic hours > Visitor hours > Lab hours
- Sections: Automatically identifies and prioritizes "Clinic:", "Visitor Hours:", "Lab:" sections
- Complex layouts: Handles facilities with multiple departments

**Example:**
```
Input: "Mon - Fri: 7:45 a.m. - 5 p.m. / Provider hours may vary; please call."
Output:
  Monday: "7:45 a.m. - 5 p.m."
  Tuesday: "7:45 a.m. - 5 p.m."
  ...
  Friday: "7:45 a.m. - 5 p.m."
  Saturday: ""
  Sunday: ""
```

### How Address Extraction Works

The scraper uses a **multi-tier approach** to extract addresses:

1. **Direct Extraction**: First tries to find individual address fields (street, city, state, zip) using CSS selectors
2. **Smart Parser**: If direct extraction fails, it automatically parses the full text block to extract address components
3. **Site-Specific Parsers**: Custom logic for Swedish/Providence, MultiCare, Kaiser Permanente, Astria Health, PeaceHealth, and more

This means it can handle various address formats like:
```
123 Main Street, Suite 100, Seattle, WA 98101
```
or
```
123 Main Street
Suite 100
Seattle, WA 98101
```
or
```
123 Main St, Building 5, Floor 2
Seattle, WA 98101
```

### Supported Healthcare Networks

The scraper includes custom parsers optimized for:

- **Swedish Medical Center** - Detail page navigation, office hours, fax
- **Providence Health** - Detail page navigation, office hours, fax
- **MultiCare** - Detail page navigation, office hours (with section prioritization), fax
- **Kaiser Permanente** - Pagination handling
- **UW Medicine** - Address parsing
- **Astria Health** - Multi-line address formats
- **PeaceHealth** - Address extraction
- **Confluence Health** - Standard extraction
- **Skagit Regional Health** - JavaScript-heavy sites
- **EvergreenHealth** - Semantic HTML parsing

Additional sites can be added by implementing site-specific parsers in `scraper.py`.

### Troubleshooting

If the scraper doesn't extract data correctly:

**Step 1: Check the terminal output**
- Look for "DEBUG" messages showing what data was extracted
- Check for error messages indicating missing elements

**Step 2: Use browser inspector**
1. Open the location page in your browser
2. Right-click on the element (fax number, office hours, address, etc.)
3. Select "Inspect" or "Inspect Element"
4. Look at the HTML structure:
   - What CSS class contains the data? (e.g., `.fax`, `.hours-content`)
   - Is it in a `<div>`, `<span>`, or other element?
   - Copy the outer HTML

**Step 3: Update the scraper**
- If it's a new site, you may need to add a custom parser in `scraper.py`
- If it's an existing site with changed selectors, update the CSS selectors in the parser
- Share the HTML structure (copy/paste) for help

**For fax numbers:**
```html
<!-- Example of what to look for -->
<div class="fax">
    <span class="label">Fax:</span>
    <span>253-403-9201</span>
</div>
```

**For office hours:**
```html
<!-- Example of what to look for -->
<div class="hours-content">
    <div>Monday - Friday: 8am - 5pm</div>
    <div>Saturday: 9am - 1pm</div>
</div>
```

## Output Format

The CSV file includes the following columns:
- **Facility Name** - Name of the healthcare facility
- **Address 1** - Street address (may include building name for some sites)
- **Address 2** - Suite, floor, or additional address details
- **City** - City name
- **State** - Two-letter state code
- **ZIP** - 5-digit or ZIP+4 format
- **Phone** - Formatted as (999) 999-9999
- **Fax** - Formatted as (999) 999-9999
- **Monday through Sunday** - Office hours for each day of the week

## Important Notes

### Smart Address Parser

The scraper includes an intelligent address parser that can extract addresses even when they're combined in a single text block. It uses pattern matching to identify:
- ZIP codes (5-digit or ZIP+4 format)
- State codes (2-letter abbreviations)
- City names
- Street addresses
- Suite/floor numbers
- Building names

This means you often don't need to update selectors - the parser will figure it out!

### Performance Considerations

**Detail page navigation adds time:**
- Basic scraping: ~2-3 seconds per location
- With detail pages: ~5-10 seconds per location
- For 1000 locations: ~2-3 hours total

**Optimization tips:**
- Reduce `MAX_PAGES_PER_URL` for testing
- Run headless mode: `HEADLESS_MODE = True`
- Disable images: `DISABLE_IMAGES = True`
- Reduce delays (less polite but faster): Lower values in `INITIAL_DELAY_MIN/MAX`

### CSS Selectors (When Needed)

If the automatic parser doesn't work perfectly, you may need to adjust CSS selectors. The script includes **extensive selector lists** in `config.py` that cover most common patterns.

**To update selectors:**

1. Use browser inspector on the webpage
2. Look for the CSS classes/attributes containing location data
3. Add them to `config.py` in the `SELECTORS` dictionary

**Example:** If you see:
```html
<span class="clinic-address">123 Main St</span>
```

Add to `config.py`:
```python
'address1': [
    ".clinic-address",  # Add your new selector here
    ".address",
    ".street-address",
    # ... existing selectors
]
```

## Customization Options

**All settings are centralized in `config.py` for easy customization!**

### Basic Settings

**Add Multiple URLs**

In `config.py`, add URLs to the list:
```python
TARGET_URLS = [
    "https://www.swedish.org/locations",
    "https://www.multicare.org/find-a-location/",
    "https://www.providence.org/locations",
]
```

The scraper will visit each URL and combine results into one CSV file.

**Run in Headless Mode (No Browser Window)**

In `config.py`, change:
```python
HEADLESS_MODE = True
```

**Disable Images (Faster Loading)**

In `config.py`, change:
```python
DISABLE_IMAGES = True
```

**Change Output Filename**

In `config.py`, modify:
```python
OUTPUT_FILENAME = "my_custom_name.csv"
```

**Change User Agent**

In `config.py`, choose from:
```python
USER_AGENT_TYPE = 'windows_chrome'  # Windows Chrome
USER_AGENT_TYPE = 'mac_chrome'      # Mac Chrome  
USER_AGENT_TYPE = 'linux_chrome'    # Linux Chrome
USER_AGENT_TYPE = 'random'          # Random selection
```

**Adjust Page Load Timeout**

If pages are slow to load:
```python
PAGE_LOAD_TIMEOUT = 20  # Increase from default 8 seconds
```

### Advanced: Update CSS Selectors

If the scraper isn't finding addresses, use your browser inspector to find the correct CSS classes, then update `config.py`:

```python
LOCATION_CONTAINER_SELECTORS = [
    ".your-actual-selector",  # Add selectors found in the inspector
    ".location-card"
]

SELECTORS = {
    'facility_name': [
        ".your-name-selector",
        "h2"
    ],
    'address1': [
        ".your-address-selector",
        ".address"
    ],
    # ... update other fields as needed
}
```

### Modify Scraping Logic

All scraping functions are in `scraper.py`:
- `setup_driver()` - Configure browser options with anti-detection
- `extract_location_data()` - Main scraping logic
- `extract_locations_from_current_page()` - Processes locations on current page
- `extract_text()` - Helper for extracting text from elements
- `parse_address_block()` - Smart parser for full address blocks
- `parse_office_hours()` - Parses office hours with edge case handling
- `parse_multicare_hours()` - MultiCare-specific hours parsing with priority system
- `format_phone_number()` - Formats phone/fax to (999) 999-9999
- `scroll_page()` - Human-like scrolling simulation
- `save_to_csv()` - Save data to CSV file

**Site-specific parsers:**
- Swedish/Providence parser (lines ~700-950)
- MultiCare parser (lines ~1100-1280)
- Kaiser Permanente parser
- Astria Health parser
- And more...

## Advanced Security Options

### Using a Proxy

For additional anonymity, you can route traffic through a proxy. In `config.py`:

```python
USE_PROXY = True
PROXY_SERVER = "http://your-proxy-server:port"

# Examples:
# PROXY_SERVER = "http://proxy.example.com:8080"
# PROXY_SERVER = "socks5://127.0.0.1:9050"  # For Tor
```

### Using a VPN

For maximum privacy, run the scraper while connected to a VPN. This is the simplest way to mask your real IP address.

### Rotating User Agents

Set in `config.py`:
```python
USER_AGENT_TYPE = 'random'  # Will randomly select from available user agents
```

Or add custom user agents:
```python
USER_AGENTS = {
    'custom': "Your custom user agent string here"
}
USER_AGENT_TYPE = 'custom'
```

### Adjusting Timing (Stealth vs Speed)

In `config.py`, you can adjust timing to be more or less cautious:

```python
# More stealthy (slower but safer)
INITIAL_DELAY_MIN = 3.0
INITIAL_DELAY_MAX = 6.0
SCROLL_DELAY_MIN = 0.2
SCROLL_DELAY_MAX = 0.5
PAGINATION_DELAY_MIN = 2.0
PAGINATION_DELAY_MAX = 4.0

# Faster (less realistic but quicker)
INITIAL_DELAY_MIN = 0.5
INITIAL_DELAY_MAX = 1.0
SCROLL_DELAY_MIN = 0.05
SCROLL_DELAY_MAX = 0.1
PAGINATION_DELAY_MIN = 0.5
PAGINATION_DELAY_MAX = 1.0
```

## Troubleshooting

### Problem: No locations extracted

**Solution:**
1. Check if the page loaded correctly (you should see the browser open)
2. Use your browser's inspector (F12) to examine the page structure
3. Look for CSS classes containing location data
4. Update `LOCATION_CONTAINER_SELECTORS` in `config.py`

### Problem: Locations found but addresses are missing

**Solution:**

The scraper has a **multi-tier approach**:
1. First tries individual field extraction (street, city, state, zip separately)
2. Falls back to smart parsing of the full text block
3. Uses site-specific parsers for known healthcare networks

If addresses still aren't extracted:
1. Use browser inspector to find the element containing the address
2. Right-click → Inspect → Copy outer HTML
3. Update `SELECTORS['address1']` in `config.py` with the correct CSS class

### Problem: Office hours not extracting

**Solution:**
1. Check terminal output for DEBUG messages showing what was extracted
2. Use browser inspector to find the hours element (usually `.hours-content`, `.hours-text`, or similar)

### Problem: Fax numbers not extracting

**Solution:**
1. Use browser inspector to find the fax element (usually `.fax`, `.loc-phone`, or similar)
2. Check if the fax has a label like "Fax:" before the number
3. The scraper tries multiple methods - if still failing, check the HTML structure

### Problem: Detail pages not being visited

**Solution:**
Check that:
1. The site is supported (Swedish, Providence, MultiCare)
2. The location cards have links containing `/locations/` in the href
3. Terminal shows "Navigating to detail page:" messages

### Problem: ChromeDriver errors

**Solution:**
- Make sure Chrome browser is installed
- The script uses webdriver-manager to auto-install ChromeDriver
- If issues persist, try updating Chrome browser
- On Linux, you may need: `sudo apt-get install chromium-browser`

### Problem: Timeout errors

**Solution:**
Increase the timeout in `config.py`:
```python
PAGE_LOAD_TIMEOUT = 20  # Increase from 8 to 20 seconds
```

Or add more delays:
```python
INITIAL_DELAY_MIN = 5.0
INITIAL_DELAY_MAX = 8.0
```

### Problem: Script is too slow

**Solution:**
Speed it up in `config.py`:
```python
HEADLESS_MODE = True  # Run without visible browser
DISABLE_IMAGES = True  # Don't load images

# Reduce delays
INITIAL_DELAY_MIN = 0.5
INITIAL_DELAY_MAX = 1.0
SCROLL_DELAY_MIN = 0.05
SCROLL_DELAY_MAX = 0.1
PAGINATION_DELAY_MIN = 0.5
PAGINATION_DELAY_MAX = 1.0
```

**Note:** Faster = less stealthy, but usually fine for one-time scraping.

### Problem: Scraper only getting first page

**Solution:**
Make sure pagination is enabled in `config.py`:
```python
ENABLE_PAGINATION = True
MAX_PAGES_PER_URL = 100  # Increase if needed
```



