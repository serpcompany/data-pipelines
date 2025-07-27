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

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return None
    return ' '.join(text.split()).strip()

def parse_record(wins, losses, draws, kos):
    """Parse record into structured format."""
    return {
        'wins': int(wins) if wins else 0,
        'losses': int(losses) if losses else 0,
        'draws': int(draws) if draws else 0,
        'kos': int(kos) if kos else 0,
        'total_fights': int(wins or 0) + int(losses or 0) + int(draws or 0)
    }

def parse_boxer_html(html_path):
    """Parse boxer HTML file and extract structured data."""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Initialize data
    data = {
        'boxrec_id': None,
        'boxrec_url': None,
        'name': None,
        'slug': None,
        'birth_name': None,
        'alias': None,
        'birth_date': None,
        'birth_place': None,
        'nationality': None,
        'stance': None,
        'height': None,
        'reach': None,
        'record': None,
        'division': None,
        'rating': None,
        'ranking': None,
        'titles': [],
        'bouts_count': None,
        'rounds_count': None,
        'ko_percentage': None,
        'residence': None,
        'status': None,
        'career': None,
        'debut': None,
        'sex': None,
        'age': None,
        'company': None,
        'promoter': None,
        'manager_agent': None,
        'wiki': None,
        'bouts': []
    }
    
    # Extract BoxRec ID and URL from canonical link
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        data['boxrec_url'] = canonical['href']
        match = re.search(r'/box-pro/(\d+)', canonical['href'])
        if match:
            data['boxrec_id'] = match.group(1)
    
    # Extract name from title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            data['name'] = title_text.replace('BoxRec:', '').strip()
            # Generate slug from name
            if data['name']:
                data['slug'] = re.sub(r'[^a-z0-9]+', '-', data['name'].lower()).strip('-')
    
    # Parse profileTable for boxer details
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        # Get all row tables within profileTable
        row_tables = profile_table.find_all('table', {'class': 'rowTable'})
        
        for row_table in row_tables:
            rows = row_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label_text = cells[0].get_text()
                    if not label_text:
                        continue
                    label = clean_text(label_text).lower()
                    value = clean_text(cells[1].get_text())
                    
                    if 'birth name' in label:
                        data['birth_name'] = value
                    elif 'alias' in label:
                        data['alias'] = value
                    elif 'nationality' in label:
                        data['nationality'] = value
                    elif 'stance' in label:
                        data['stance'] = value
                    elif 'height' in label:
                        data['height'] = value
                    elif 'reach' in label:
                        data['reach'] = value
                    elif 'division' in label:
                        data['division'] = value
                    elif 'rating' in label:
                        data['rating'] = value
                    elif 'bouts' in label and 'count' not in label:
                        data['bouts_count'] = int(value) if value.isdigit() else None
                    elif 'rounds' in label:
                        data['rounds_count'] = int(value) if value.isdigit() else None
                    elif label == 'kos':
                        data['ko_percentage'] = value
                    elif 'titles' in label:
                        # Extract titles - they're in a special format
                        title_divs = cells[1].find_all('div', {'class': 'titleColor'})
                        for title_div in title_divs:
                            title_links = title_div.find_all('a', {'class': 'titleLink'})
                            data['titles'].extend([link.get_text(strip=True) for link in title_links])
                    elif 'company' in label:
                        data['company'] = value
                    elif 'promoter' in label:
                        data['promoter'] = value
                    elif 'manager' in label or 'agent' in label:
                        data['manager_agent'] = value
                    elif 'status' in label:
                        data['status'] = value
                    elif 'residence' in label:
                        data['residence'] = value
                    elif 'birth place' in label:
                        data['birth_place'] = value
                    elif 'career' in label:
                        data['career'] = value
                    elif 'debut' in label:
                        data['debut'] = value
                    elif 'sex' in label:
                        data['sex'] = value
                    elif 'id#' in label:
                        data['boxrec_id'] = value.lstrip('0')  # Remove leading zeros
                        
    # Check for wiki link
    wiki_link = soup.find('a', href=re.compile(r'/wiki/index\.php\?title=Human:'))
    if wiki_link:
        data['wiki'] = 'https://boxrec.com' + wiki_link['href']
        
        # Extract record from profileWLD table
        wld_table = profile_table.find('table', {'class': 'profileWLD'})
        if wld_table:
            # First row has W-L-D
            first_row = wld_table.find('tr')
            if first_row:
                cells = first_row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    wins = clean_text(cells[0].get_text())
                    losses = clean_text(cells[1].get_text())
                    draws = clean_text(cells[2].get_text())
                    
                    # Second row has KOs
                    second_row = wld_table.find_all('tr')[1] if len(wld_table.find_all('tr')) > 1 else None
                    kos = 0
                    if second_row:
                        ko_cell = second_row.find('td')
                        if ko_cell and ko_cell.get_text():
                            ko_text = ko_cell.get_text()
                            ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                            if ko_match:
                                kos = ko_match.group(1)
                    
                    data['record'] = parse_record(wins, losses, draws, kos)
    
    # Parse dataTable for fight history
    data_table = soup.find('table', {'class': 'dataTable'})
    if data_table:
        rows = data_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            # Skip rows that are notes/comments (usually have colspan)
            if row.find('td', {'colspan': True}):
                continue
                
            cells = row.find_all('td')
            if len(cells) >= 6:
                # Extract fight data
                date_cell = cells[0]
                opponent_cell = cells[2]
                record_cell = cells[3] if len(cells) > 3 else None
                form_cell = cells[4] if len(cells) > 4 else None
                venue_cell = cells[5] if len(cells) > 5 else None
                result_cell = cells[6] if len(cells) > 6 else None
                rating_cell = cells[7] if len(cells) > 7 else None
                
                # Extract opponent info including BoxRec ID
                opponent_name = None
                opponent_id = None
                opponent_url = None
                if opponent_cell:
                    opponent_link = opponent_cell.find('a', {'class': 'personLink'})
                    if opponent_link:
                        opponent_name = clean_text(opponent_link.get_text())
                        href = opponent_link.get('href')
                        if href:
                            # Extract ID from href like "/en/box-pro/828415"
                            id_match = re.search(r'/box-pro/(\d+)', href)
                            if id_match:
                                opponent_id = id_match.group(1)
                                opponent_url = f"https://boxrec.com{href}"
                    else:
                        opponent_name = clean_text(opponent_cell.get_text())
                
                # Extract opponent record (W-L-D)
                opponent_record = None
                if record_cell:
                    wins = record_cell.find('span', {'class': 'textWon'})
                    losses = record_cell.find('span', {'class': 'textLost'}) 
                    draws = record_cell.find('span', {'class': 'textDraw'})
                    if wins and losses and draws:
                        opponent_record = f"{wins.get_text()}-{losses.get_text()}-{draws.get_text()}"
                
                # Extract recent form (last 6 fights)
                recent_form = None
                if form_cell:
                    form_imgs = form_cell.find_all('img')
                    if form_imgs:
                        form_results = []
                        for img in form_imgs:
                            if 'l6w' in img.get('src', ''):
                                form_results.append('W')
                            elif 'l6l' in img.get('src', ''):
                                form_results.append('L')
                            elif 'l6d' in img.get('src', ''):
                                form_results.append('D')
                        recent_form = ''.join(form_results)
                
                # Extract bout rating (stars)
                bout_rating = None
                if rating_cell:
                    filled_stars = len(rating_cell.find_all('i', {'class': re.compile(r'fas fa-star')}))
                    bout_rating = filled_stars
                
                # Get venue
                venue = clean_text(venue_cell.get_text()) if venue_cell else None
                
                # Get result
                result_text = result_cell.get_text() if result_cell else ''
                result_div = result_cell.find('div', {'class': 'boutResult'}) if result_cell else None
                result = clean_text(result_div.get_text()) if result_div else None
                
                bout = {
                    'date': clean_text(date_cell.get_text()),
                    'opponent': opponent_name,
                    'opponent_id': opponent_id,
                    'opponent_url': opponent_url,
                    'opponent_record': opponent_record,
                    'recent_form': recent_form,
                    'result': result,
                    'method': None,  # TODO: Extract from bout detail page if needed
                    'rounds': None,  # TODO: Extract from bout detail page if needed
                    'venue': venue,
                    'bout_rating': bout_rating
                }
                
                # Only add if we have meaningful data
                if bout['date'] and bout['opponent']:
                    data['bouts'].append(bout)
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_boxer_final.py <html_file>")
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
        output_file = html_file.replace('.html', '.json').replace('boxrec_html', 'boxrec_json')
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