# UW Medicine Location Scraper

A Python web scraper that extracts location information from the UW Medicine website and saves it to a CSV file.

## Project Structure

```
├── main.py              # Main script to run the scraper
├── scraper.py           # Scraper functions and utilities
├── config.py            # Configuration file (customize settings here)
├── inspect_html.py      # HTML inspector tool (for troubleshooting)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Features

- Uses Selenium for browser automation (not blocked by robots.txt)
- Automatically manages ChromeDriver installation
- **Advanced anti-detection measures** (see Security Features below)
- **Smart address parser** - Automatically extracts addresses even when they're in one block
- Clean, modular code structure
- Well-commented and easy to customize
- Exports data to CSV format
- Error handling and logging
- HTML inspector tool for troubleshooting

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
2. Extract all location data (names, addresses, phone numbers)
3. Save results to `uw_medicine_locations.csv`

### How Address Extraction Works

The scraper uses a **two-tier approach** to extract addresses:

1. **Direct Extraction**: First tries to find individual address fields (street, city, state, zip) using CSS selectors
2. **Smart Parser**: If direct extraction fails, it automatically parses the full text block to extract address components

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

### Troubleshooting

If the scraper doesn't extract addresses correctly, use the HTML inspector:

```bash
python inspect_html.py
```

This will:
- Show you the actual HTML structure of location cards
- Identify which CSS selectors the site is using
- Help you find the correct class names to add to `config.py`
- Save the full page HTML to `page_structure.html` for manual inspection

**Workflow:**
1. Run `python main.py` first
2. If addresses are missing, run `python inspect_html.py`
3. Update the selectors in `config.py` based on what the inspector shows
4. Run `python main.py` again

## Output Format

The CSV file includes the following columns:
- Facility Name
- Address 1
- Address 2
- City
- State
- ZIP
- Phone

## Important Notes

### Smart Address Parser

The scraper includes an intelligent address parser that can extract addresses even when they're combined in a single text block. It uses pattern matching to identify:
- ZIP codes (5-digit or ZIP+4 format)
- State codes (2-letter abbreviations)
- City names
- Street addresses
- Suite/floor numbers

This means you often don't need to update selectors - the parser will figure it out!

### CSS Selectors (When Needed)

If the automatic parser doesn't work perfectly, you may need to adjust CSS selectors. The script includes **extensive selector lists** in `config.py` that cover most common patterns.

**To update selectors:**

1. Run `inspect_html.py` to see the actual HTML structure
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

**All settings are now centralized in `config.py` for easy customization!**

### Basic Settings

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

### Advanced: Update CSS Selectors

If the scraper isn't finding addresses, use the inspector tool:

```bash
python inspect_html.py
```

This will show you the actual HTML structure. Then update `config.py`:

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

**Pro tip:** The scraper has comprehensive default selectors and a smart parser, so you usually won't need to change these!

### Modify Scraping Logic

All scraping functions are in `scraper.py`:
- `setup_driver()` - Configure browser options with anti-detection
- `extract_location_data()` - Main scraping logic
- `extract_text()` - Helper for extracting text from elements
- `parse_address_block()` - Smart parser for full address blocks
- `scroll_page()` - Human-like scrolling simulation
- `save_to_csv()` - Save data to CSV file
- `save_page_source()` - Save HTML for debugging

**Tools:**
- `inspect_html.py` - HTML inspector for troubleshooting selector issues

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

# Faster (less realistic but quicker)
INITIAL_DELAY_MIN = 0.5
INITIAL_DELAY_MAX = 1.0
SCROLL_DELAY_MIN = 0.05
SCROLL_DELAY_MAX = 0.1
```

## Troubleshooting

### Problem: No locations extracted

**Solution:**
1. Check if the page loaded correctly (you should see the browser open)
2. Run the HTML inspector: `python inspect_html.py`
3. Look at the output to see what selectors the site uses
4. Update `LOCATION_CONTAINER_SELECTORS` in `config.py`

### Problem: Locations found but addresses are missing

**Solution:**

The scraper has a **two-tier approach**:
1. First tries individual field extraction (street, city, state, zip separately)
2. Falls back to smart parsing of the full text block

If addresses still aren't extracted:

1. Run the inspector: `python inspect_html.py`
2. Look at the "All text in this card" section to see the address format
3. Check if addresses are in the text at all
4. Update `SELECTORS['address1']` in `config.py` with the correct CSS classes shown in the inspector

**Example:** If inspector shows addresses in `<div class="location-info">`, add:
```python
'address1': [
    ".location-info",
    ".address",
    # ... other selectors
]
```

### Problem: Only getting some fields (name and phone work, but not address)

**Likely cause:** The address is in a different HTML structure than expected.

**Solution:**
1. The smart address parser should handle this automatically
2. If not, run `python inspect_html.py` to see the exact HTML
3. The inspector will show you which CSS class contains the address
4. Add that class to `config.py` under `SELECTORS['address1']`

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
PAGE_LOAD_TIMEOUT = 20  # Increase from 10 to 20 seconds
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
```

**Note:** Faster = less stealthy, but usually fine for one-time scraping.

### Using the HTML Inspector

The inspector tool (`inspect_html.py`) is your best friend for debugging:

**What it does:**
- Opens the page and finds all location elements
- Prints the HTML structure of the first 3 location cards
- Shows all text content line-by-line
- Identifies address-related elements
- Saves full page HTML to `page_structure.html`

**How to use it:**
```bash
python inspect_html.py
```

Then:
1. Read the printed HTML structure
2. Look for CSS classes containing addresses
3. Update `config.py` with those classes
4. Run `main.py` again

## Legal & Ethical Considerations

- This script is for personal, educational use
- Check the website's Terms of Service before scraping
- Be respectful: don't run the script too frequently
- Consider reaching out to UW Medicine for official data access if available

## License

Free to use and modify for personal and educational purposes.



