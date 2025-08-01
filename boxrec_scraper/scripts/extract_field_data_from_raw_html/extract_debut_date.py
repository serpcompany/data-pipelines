#!/usr/bin/env python3
"""Extract professional debut date from HTML."""

from base_extractor import load_html, test_extraction

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
                return value
    
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
                    return cells[0].get_text().strip()
    
    return None

if __name__ == "__main__":
    test_extraction(extract_debut_date)