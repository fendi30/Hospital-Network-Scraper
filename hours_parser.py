"""
Helper functions for parsing office hours into structured format
"""
import re

def parse_office_hours(hours_text):
    """
    Parse office hours text into individual days.
    
    Handles formats like:
    - "Mon - Thur: 8 a.m. - 12 p.m. & 1 p.m. - 5 p.m."
    - "Mon - Fri: 9:00 am - 5:00 pm"
    - "Monday: 8:00 am - 5:00 pm / Tuesday: Closed"
    
    Returns:
        dict: {
            'Monday': '8:00 am - 5:00 pm',
            'Tuesday': '8:00 am - 5:00 pm',
            ...
            'Sunday': 'Closed'
        }
    """
    days_dict = {
        'Monday': '',
        'Tuesday': '',
        'Wednesday': '',
        'Thursday': '',
        'Friday': '',
        'Saturday': '',
        'Sunday': ''
    }
    
    if not hours_text:
        return days_dict
    
    # Normalize the text
    text = hours_text.strip()
    
    # Day abbreviation mapping
    day_abbrev = {
        'mon': 'Monday',
        'tue': 'Tuesday', 'tues': 'Tuesday',
        'wed': 'Wednesday',
        'thu': 'Thursday', 'thur': 'Thursday', 'thurs': 'Thursday',
        'fri': 'Friday',
        'sat': 'Saturday',
        'sun': 'Sunday'
    }
    
    # Split by common separators (/, |, newline)
    segments = re.split(r'[/|\n]', text)
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # Try to match pattern: "Day(s): hours"
        match = re.match(r'^([A-Za-z\s\-,]+?):\s*(.+)$', segment)
        if not match:
            continue
        
        day_part = match.group(1).strip().lower()
        hours_part = match.group(2).strip()
        
        # Handle day ranges (e.g., "Mon - Fri", "Mon - Thur")
        if ' - ' in day_part or ' to ' in day_part:
            # Split range
            range_match = re.match(r'([a-z]+)\s*(?:-|to)\s*([a-z]+)', day_part)
            if range_match:
                start_abbrev = range_match.group(1)
                end_abbrev = range_match.group(2)
                
                # Map to full day names
                start_day = day_abbrev.get(start_abbrev)
                end_day = day_abbrev.get(end_abbrev)
                
                if start_day and end_day:
                    # Find day range
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    start_idx = day_order.index(start_day)
                    end_idx = day_order.index(end_day)
                    
                    # Fill in all days in range
                    for i in range(start_idx, end_idx + 1):
                        days_dict[day_order[i]] = hours_part
        
        # Handle comma-separated days (e.g., "Mon, Wed, Fri")
        elif ',' in day_part:
            day_list = [d.strip() for d in day_part.split(',')]
            for day in day_list:
                full_day = day_abbrev.get(day)
                if full_day:
                    days_dict[full_day] = hours_part
        
        # Handle single day
        else:
            full_day = day_abbrev.get(day_part)
            if full_day:
                days_dict[full_day] = hours_part
    
    return days_dict


def extract_fax_number(text):
    """
    Extract fax number from text.
    
    Looks for patterns like:
    - "Fax: 425-259-8600"
    - "Fax: (425) 259-8600"
    
    Returns:
        str: Fax number or empty string if not found
    """
    if not text:
        return ''
    
    # Look for "Fax:" followed by phone number
    fax_match = re.search(r'Fax:\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text, re.IGNORECASE)
    if fax_match:
        return fax_match.group(1).strip()
    
    return ''