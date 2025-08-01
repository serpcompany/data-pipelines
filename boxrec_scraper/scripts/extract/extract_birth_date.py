#!/usr/bin/env python3
"""Extract birth date from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_birth_date(soup):
    """Extract date of birth from various possible locations."""
    
    # Method 1: Look for "born" in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if ('born' in label or 'date of birth' in label) and 'birth name' not in label:
                value = cells[1].get_text().strip()
                # Remove age info if present
                value = re.sub(r'\s*\(.*?\)\s*$', '', value)
                return value
    
    # Method 2: Search for date patterns near "born" text
    text = soup.get_text()
    patterns = [
        r'born[:\s]+([^,\n]+)',
        r'birth\s*date[:\s]+([^,\n]+)',
        r'date\s*of\s*birth[:\s]+([^,\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            # Remove age info if present
            date_text = re.sub(r'\s*\(.*?\)\s*$', '', date_text)
            return date_text
    
    # Method 3: Look for dates in specific format
    date_patterns = [
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # MM-DD-YYYY or MM/DD/YYYY
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD
        r'(\w+\s+\d{1,2},?\s+\d{4})',      # Month DD, YYYY
        r'(\d{1,2}\s+\w+\s+\d{4})',        # DD Month YYYY
    ]
    
    for row in rows:
        row_text = row.get_text()
        if 'born' in row_text.lower():
            for pattern in date_patterns:
                match = re.search(pattern, row_text)
                if match:
                    return match.group(1)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_birth_date)