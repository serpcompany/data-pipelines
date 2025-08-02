#!/usr/bin/env python3
"""Extract professional debut date from HTML."""

import re
from base_extractor import load_html, test_extraction

def format_date_iso(date_text):
    """Convert various date formats to ISO 8601 format (YYYY-MM-DD)."""
    if not date_text:
        return None
    
    # Try to parse different formats
    patterns = [
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: m.group(0)),  # Already ISO format
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),  # MM/DD/YYYY or MM-DD-YYYY
        (r'(\d{1,2})\s+(\w+)\s+(\d{4})', lambda m: convert_month_to_iso(m)),  # DD Month YYYY
        (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', lambda m: convert_month_to_iso_alt(m)),  # Month DD, YYYY
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, date_text)
        if match:
            return formatter(match)
    
    return date_text  # Return as-is if no pattern matches

def convert_month_to_iso(match):
    """Convert 'DD Month YYYY' to ISO format."""
    months = {
        'january': '01', 'jan': '01', 'february': '02', 'feb': '02', 'march': '03', 'mar': '03',
        'april': '04', 'apr': '04', 'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
        'august': '08', 'aug': '08', 'september': '09', 'sep': '09', 'october': '10', 'oct': '10',
        'november': '11', 'nov': '11', 'december': '12', 'dec': '12'
    }
    day = match.group(1).zfill(2)
    month_name = match.group(2).lower()
    year = match.group(3)
    month = months.get(month_name)
    if month:
        return f"{year}-{month}-{day}"
    return match.group(0)

def convert_month_to_iso_alt(match):
    """Convert 'Month DD, YYYY' to ISO format."""
    months = {
        'january': '01', 'jan': '01', 'february': '02', 'feb': '02', 'march': '03', 'mar': '03',
        'april': '04', 'apr': '04', 'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
        'august': '08', 'aug': '08', 'september': '09', 'sep': '09', 'october': '10', 'oct': '10',
        'november': '11', 'nov': '11', 'december': '12', 'dec': '12'
    }
    month_name = match.group(1).lower()
    day = match.group(2).zfill(2)
    year = match.group(3)
    month = months.get(month_name)
    if month:
        return f"{year}-{month}-{day}"
    return match.group(0)

def extract_debut_date(soup):
    """Extract professional debut date from HTML."""
    
    # Method 1: Look for debut in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            # Look for debut but exclude amateur
            if 'debut' in label and 'amateur' not in label:
                value = cells[1].get_text().strip()
                return format_date_iso(value)
    
    # Method 2: Look at first fight in the data table
    data_table = soup.find('table', {'class': 'dataTable'})
    if data_table:
        # Get all rows except header
        rows = data_table.find_all('tr')[1:]
        if rows:
            # Get the last row (oldest fight)
            last_row = rows[-1]
            # Skip if it's a colspan row (notes)
            if not last_row.find('td', {'colspan': True}):
                cells = last_row.find_all('td')
                if cells:
                    # First cell is usually the date
                    date_text = cells[0].get_text().strip()
                    return format_date_iso(date_text)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_debut_date)