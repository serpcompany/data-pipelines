#!/usr/bin/env python3
import json
import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_json_ld(soup):
    """Extract structured data from JSON-LD script tags."""
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'Person':
                return data
        except:
            continue
    return None

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return None
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    return text.strip()

def extract_from_table_row(row, label):
    """Extract value from a table row with a specific label."""
    if not row:
        return None
    
    # Look for the label in th or td elements
    label_cell = row.find(['th', 'td'], string=re.compile(label, re.I))
    if label_cell:
        # Get the next sibling cell
        value_cell = label_cell.find_next_sibling(['td', 'th'])
        if value_cell:
            return clean_text(value_cell.get_text())
    
    # Alternative: check if label is in the text
    row_text = row.get_text()
    if label.lower() in row_text.lower():
        # Try to extract value after the label
        parts = row_text.split(':')
        if len(parts) > 1:
            return clean_text(parts[1])
    
    return None

def parse_boxer_html(html_path):
    """Parse boxer HTML file and extract structured data."""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Initialize data structure
    data = {
        'boxrec_id': None,
        'name': None,
        'full_name': None,
        'nickname': None,
        'birth_date': None,
        'birth_place': None,
        'nationality': None,
        'stance': None,
        'height': None,
        'reach': None,
        'record': None,
        'division': None,
        'residence': None,
        'status': None,
        'ranking': None,
        'bouts': []
    }
    
    # Extract BoxRec ID from URL
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        match = re.search(r'/box-pro/(\d+)', canonical['href'])
        if match:
            data['boxrec_id'] = match.group(1)
    
    # Extract name from title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            data['name'] = title_text.replace('BoxRec:', '').strip()
    
    # Try to extract from JSON-LD
    json_ld_data = extract_json_ld(soup)
    if json_ld_data:
        data['name'] = json_ld_data.get('name', data['name'])
        data['birth_date'] = json_ld_data.get('birthDate')
        data['nationality'] = json_ld_data.get('nationality', {}).get('name')
    
    # Look for the main content area - try different approaches
    # Approach 1: Look for specific table structures
    info_tables = soup.find_all('table')
    for table in info_tables:
        rows = table.find_all('tr')
        for row in rows:
            row_text = row.get_text().strip()
            
            # Full name
            if 'full name' in row_text.lower() or 'birth name' in row_text.lower():
                value = extract_from_table_row(row, 'name')
                if value:
                    data['full_name'] = value
            
            # Nickname/Alias
            elif 'nickname' in row_text.lower() or 'alias' in row_text.lower():
                value = extract_from_table_row(row, 'nickname|alias')
                if value:
                    data['nickname'] = value
            
            # Birth date
            elif 'born' in row_text.lower() or 'birth' in row_text.lower():
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    cell_text = cell.get_text()
                    # Look for date pattern
                    date_match = re.search(r'\d{4}/\d{2}/\d{2}', cell_text)
                    if date_match:
                        data['birth_date'] = date_match.group()
            
            # Nationality
            elif 'nationality' in row_text.lower():
                value = extract_from_table_row(row, 'nationality')
                if value:
                    data['nationality'] = value
            
            # Stance
            elif 'stance' in row_text.lower():
                value = extract_from_table_row(row, 'stance')
                if value:
                    data['stance'] = value
            
            # Height
            elif 'height' in row_text.lower():
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    cell_text = cell.get_text()
                    # Look for height pattern (e.g., 5′ 8″ or 173cm)
                    if '″' in cell_text or 'cm' in cell_text:
                        data['height'] = clean_text(cell_text)
            
            # Reach
            elif 'reach' in row_text.lower():
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    cell_text = cell.get_text()
                    if '″' in cell_text or 'cm' in cell_text:
                        data['reach'] = clean_text(cell_text)
            
            # Division
            elif 'division' in row_text.lower():
                value = extract_from_table_row(row, 'division')
                if value:
                    data['division'] = value
    
    # Extract record - look for pattern like "50-0-0 (27 KOs)"
    record_pattern = re.compile(r'(\d+)-(\d+)-(\d+)\s*\((\d+)\s*KOs?\)')
    record_match = record_pattern.search(html_content)
    if record_match:
        data['record'] = {
            'wins': int(record_match.group(1)),
            'losses': int(record_match.group(2)),
            'draws': int(record_match.group(3)),
            'kos': int(record_match.group(4)),
            'total_fights': int(record_match.group(1)) + int(record_match.group(2)) + int(record_match.group(3))
        }
    
    # Look for bout history table
    # Common patterns: table with class containing 'bout', id containing 'bout'
    bout_table = None
    
    # Try different selectors
    selectors = [
        'table[id*="bout"]',
        'table[class*="bout"]',
        'table:has(th:contains("date"))',
        'table:has(th:contains("opponent"))'
    ]
    
    for selector in selectors:
        try:
            bout_table = soup.select_one(selector)
            if bout_table:
                break
        except:
            continue
    
    if bout_table:
        rows = bout_table.find_all('tr')[1:]  # Skip header
        for row in rows[:20]:  # Limit to first 20 bouts
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                bout = {
                    'date': clean_text(cells[0].get_text()) if len(cells) > 0 else None,
                    'opponent': clean_text(cells[1].get_text()) if len(cells) > 1 else None,
                    'result': clean_text(cells[2].get_text()) if len(cells) > 2 else None,
                    'method': clean_text(cells[3].get_text()) if len(cells) > 3 else None,
                    'rounds': clean_text(cells[4].get_text()) if len(cells) > 4 else None,
                    'venue': clean_text(cells[5].get_text()) if len(cells) > 5 else None
                }
                # Only add if we have at least date and opponent
                if bout['date'] and bout['opponent']:
                    data['bouts'].append(bout)
    
    # Extract any visible ranking information
    ranking_pattern = re.compile(r'#(\d+)\s*(?:ranked|rating|world)', re.I)
    ranking_match = ranking_pattern.search(html_content)
    if ranking_match:
        data['ranking'] = ranking_match.group(1)
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_boxer_v2.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not os.path.exists(html_file):
        print(f"File not found: {html_file}")
        sys.exit(1)
    
    try:
        data = parse_boxer_html(html_file)
        
        # Output as JSON
        print(json.dumps(data, indent=2))
        
        # Save to file
        output_file = html_file.replace('.html', '.json').replace('boxrec_html', 'boxrec_data')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logging.info(f"Saved JSON to: {output_file}")
        
    except Exception as e:
        logging.error(f"Error parsing {html_file}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()