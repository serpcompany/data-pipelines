#!/usr/bin/env python3
"""Extract total professional rounds from HTML."""

from ....base import load_html, test_extraction

def extract(soup):
    """Extract total professional rounds from HTML."""
    
    # Look for rounds in table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            label = cells[0].get_text().strip().lower()
            if 'rounds' in label and 'scheduled' not in label:
                value = cells[1].get_text().strip()
                try:
                    return int(value)
                except:
                    pass
    
    # Look in statistics sections
    stats_divs = soup.find_all('div', class_='profileStatistic')
    for div in stats_divs:
        label = div.find('span', class_='profileStatisticLabel')
        if label and 'rounds' in label.get_text().lower():
            value = div.find('span', class_='profileStatisticValue')
            if value:
                text = value.get_text().strip()
                try:
                    return int(text)
                except:
                    pass
    
    return None

if __name__ == "__main__":
    test_extraction(extract)