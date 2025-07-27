#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_text(element):
    """Extract and clean text from an element."""
    if element:
        return element.get_text().strip()
    return None

def parse_record(record_text):
    """Parse win-loss-draw record from text like '50-0-0 (27 KOs)'"""
    if not record_text:
        return None
    
    try:
        # Extract record and KOs
        parts = record_text.split('(')
        record_part = parts[0].strip()
        ko_part = parts[1].replace(')', '').replace('KOs', '').strip() if len(parts) > 1 else '0'
        
        # Parse win-loss-draw
        record_nums = record_part.split('-')
        wins = int(record_nums[0]) if len(record_nums) > 0 else 0
        losses = int(record_nums[1]) if len(record_nums) > 1 else 0
        draws = int(record_nums[2]) if len(record_nums) > 2 else 0
        
        return {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'kos': int(ko_part) if ko_part.isdigit() else 0,
            'total_fights': wins + losses + draws
        }
    except Exception as e:
        logging.warning(f"Could not parse record '{record_text}': {e}")
        return None

def parse_boxer_html(html_path):
    """Parse boxer HTML file and extract structured data."""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Extract basic info
    data = {
        'boxrec_id': None,
        'name': None,
        'birth_name': None,
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
        'bouts': []
    }
    
    # Extract BoxRec ID from URL in canonical link
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        url_parts = canonical['href'].split('/')
        if 'box-pro' in url_parts:
            idx = url_parts.index('box-pro')
            if idx + 1 < len(url_parts):
                data['boxrec_id'] = url_parts[idx + 1]
    
    # Extract name from title or h1
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            data['name'] = title_text.replace('BoxRec:', '').strip()
    
    # Find the main content area with boxer details
    # Look for the section with boxer information
    info_section = soup.find('section', {'class': 'boxerDetails'})
    if not info_section:
        # Try alternative selectors
        info_section = soup.find('div', {'class': 'row boxerDetails'})
    
    if info_section:
        # Extract various fields from the info section
        rows = info_section.find_all(['tr', 'div'], recursive=True)
        
        for row in rows:
            text = row.get_text().strip()
            
            # Birth name
            if 'birth name' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['birth_name'] = value
            
            # Nickname
            elif 'alias' in text.lower() or 'nickname' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['nickname'] = value
            
            # Born/birth date
            elif 'born' in text.lower() or 'birth' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value and '/' in value:
                    data['birth_date'] = value.split()[0] if ' ' in value else value
            
            # Birth place
            elif 'birthplace' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['birth_place'] = value
            
            # Nationality
            elif 'nationality' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['nationality'] = value
            
            # Stance
            elif 'stance' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['stance'] = value
            
            # Height
            elif 'height' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['height'] = value
            
            # Reach
            elif 'reach' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['reach'] = value
            
            # Division
            elif 'division' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['division'] = value
            
            # Residence
            elif 'residence' in text.lower():
                value = extract_text(row.find_next(['td', 'span']))
                if value:
                    data['residence'] = value
    
    # Try to find record in various places
    record_elem = soup.find(text=lambda t: t and ' KOs)' in t)
    if record_elem:
        record_text = record_elem.strip()
        data['record'] = parse_record(record_text)
    
    # Extract bout/fight history if available
    bout_table = soup.find('table', {'id': 'listBoutsTable'})
    if not bout_table:
        bout_table = soup.find('table', class_=lambda x: x and 'bout' in x.lower())
    
    if bout_table:
        rows = bout_table.find_all('tr')[1:]  # Skip header
        for row in rows[:10]:  # Limit to first 10 bouts
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 6:
                bout = {
                    'date': extract_text(cols[0]),
                    'opponent': extract_text(cols[1]),
                    'result': extract_text(cols[2]),
                    'method': extract_text(cols[3]),
                    'rounds': extract_text(cols[4]),
                    'venue': extract_text(cols[5]) if len(cols) > 5 else None
                }
                data['bouts'].append(bout)
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_boxer.py <html_file>")
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
        sys.exit(1)

if __name__ == "__main__":
    main()