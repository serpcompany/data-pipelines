#!/usr/bin/env python3
import json
import os
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timezone

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

def extract_numeric_value(text):
    """Extract numeric value from text (e.g., '5′ 8″ / 173cm' -> '173')."""
    if not text:
        return None
    # Look for cm value first
    cm_match = re.search(r'(\d+)\s*cm', text)
    if cm_match:
        return cm_match.group(1)
    # Otherwise get first number
    match = re.search(r'(\d+)', text)
    return match.group(1) if match else text

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

def extract_multiple_values(text):
    """Extract multiple comma-separated values."""
    if not text:
        return ""
    # Clean up and split by comma
    values = [v.strip() for v in text.split(',') if v.strip()]
    return ', '.join(values)

def extract_nicknames(text):
    """Extract nicknames in the format '"Money","Pretty Boy"'."""
    if not text:
        return ""
    # Split by comma and clean up
    nicknames = [n.strip() for n in text.split(',') if n.strip()]
    # Format as comma-separated quoted strings
    return ','.join(f'"{n}"' for n in nicknames)

def extract_profile_image(soup):
    """Extract profile image URL if available."""
    # Try various possible image selectors
    img_selectors = [
        'img.profileBoxerPicture',
        'img[alt*="profile"]',
        'div.profileImage img',
        'td.profileBoxerPicture img',
        'img[src*="boxrec.com/images"]'  # Fallback for any BoxRec hosted image
    ]
    
    for selector in img_selectors:
        img = soup.select_one(selector)
        if img and img.get('src'):
            src = img['src']
            # Skip placeholder images
            if 'blank' in src.lower() or 'default' in src.lower():
                continue
            if src.startswith('/'):
                return f"https://boxrec.com{src}"
            elif src.startswith('http'):
                return src
    
    return ""

def parse_date_of_birth(soup):
    """Extract date of birth from various possible locations."""
    # Look for birth date in different locations
    birth_patterns = [
        r'born[:\s]+([^,\n]+)',
        r'birth\s*date[:\s]+([^,\n]+)',
        r'date\s*of\s*birth[:\s]+([^,\n]+)',
    ]
    
    text = str(soup)
    for pattern in birth_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            # Remove age info if present
            date_text = re.sub(r'\s*\(.*?\)\s*$', '', date_text)
            return format_date_iso(date_text)
    
    return ""

def parse_boxer_html(html_path):
    """Parse boxer HTML file and extract structured data matching expected schema."""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Initialize data with expected field names
    data = {
        'id': '',  # Will be set by database
        'boxrecId': '',
        'boxrecUrl': '',
        'boxrecWikiUrl': '',
        'slug': '',
        'name': '',
        'birthName': '',
        'nicknames': '',
        'avatarImage': '',
        'residence': '',
        'birthPlace': '',
        'dateOfBirth': '',
        'gender': '',
        'nationality': '',
        'height': '',
        'reach': '',
        'stance': '',
        'bio': '',
        'promoters': '',
        'trainers': '',
        'managers': '',
        'gym': '',
        'proDebutDate': '',
        'proDivision': '',
        'proWins': '0',
        'proWinsByKnockout': '0',
        'proLosses': '0',
        'proLossesByKnockout': '0',
        'proDraws': '0',
        'proStatus': '',
        'proTotalBouts': '',
        'proTotalRounds': '',
        'amateurDebutDate': '',
        'amateurDivision': '',
        'amateurWins': '0',
        'amateurWinsByKnockout': '0',
        'amateurLosses': '0',
        'amateurLossesByKnockout': '0',
        'amateurDraws': '0',
        'amateurStatus': '',
        'amateurTotalBouts': '',
        'amateurTotalRounds': '',
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'updatedAt': datetime.now(timezone.utc).isoformat()
    }
    
    # Extract BoxRec ID and URL from canonical link
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        data['boxrecUrl'] = canonical['href']
        match = re.search(r'/box-pro/(\d+)', canonical['href'])
        if match:
            data['boxrecId'] = match.group(1)
    
    # Extract name from title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        if 'BoxRec:' in title_text:
            data['name'] = title_text.replace('BoxRec:', '').strip()
            # Generate slug from name
            if data['name']:
                data['slug'] = re.sub(r'[^a-z0-9]+', '-', data['name'].lower()).strip('-')
    
    # Extract profile image
    data['avatarImage'] = extract_profile_image(soup)
    
    # Extract date of birth
    data['dateOfBirth'] = parse_date_of_birth(soup)
    
    # Check for wiki link
    wiki_link = soup.find('a', href=re.compile(r'/wiki/index\.php\?title=Human:'))
    if wiki_link:
        data['boxrecWikiUrl'] = 'https://boxrec.com' + wiki_link['href']
    
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
                        data['birthName'] = value or ''
                    elif 'alias' in label or 'nickname' in label:
                        data['nicknames'] = extract_nicknames(value)
                    elif 'nationality' in label:
                        data['nationality'] = value or ''
                    elif 'stance' in label:
                        data['stance'] = value.lower() if value else ''
                    elif 'height' in label:
                        data['height'] = extract_numeric_value(value) or ''
                    elif 'reach' in label:
                        data['reach'] = extract_numeric_value(value) or ''
                    elif 'division' in label and 'weight' not in label:
                        data['proDivision'] = value or ''
                    elif 'bouts' in label and 'count' not in label:
                        data['proTotalBouts'] = value if value and value.isdigit() else ''
                    elif 'rounds' in label:
                        data['proTotalRounds'] = value if value and value.isdigit() else ''
                    elif 'promoter' in label:
                        data['promoters'] = extract_multiple_values(value)
                    elif 'trainer' in label:
                        data['trainers'] = extract_multiple_values(value)
                    elif 'manager' in label:
                        data['managers'] = extract_multiple_values(value)
                    elif 'gym' in label:
                        data['gym'] = value or ''
                    elif 'status' in label:
                        status_value = value.lower() if value else None
                        if status_value:
                            # Check for inactive indicators
                            if any(word in status_value for word in ['inactive', 'retired', 'not active']):
                                data['proStatus'] = 'inactive'
                            elif 'active' in status_value:
                                data['proStatus'] = 'active'
                            else:
                                data['proStatus'] = ''
                    elif 'residence' in label:
                        data['residence'] = value or ''
                    elif 'birth place' in label:
                        data['birthPlace'] = value or ''
                    elif ('born' in label or 'date of birth' in label) and value:
                        data['dateOfBirth'] = format_date_iso(value) or ''
                    elif 'debut' in label and 'amateur' not in label:
                        data['proDebutDate'] = format_date_iso(value) or ''
                    elif 'sex' in label or 'gender' in label:
                        gender_value = value.lower() if value else None
                        if gender_value:
                            data['gender'] = 'M' if 'male' in gender_value else 'F' if 'female' in gender_value else ''
        
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
                    
                    # Set record fields
                    data['proWins'] = wins if wins and wins.isdigit() else '0'
                    data['proLosses'] = losses if losses and losses.isdigit() else '0'
                    data['proDraws'] = draws if draws and draws.isdigit() else '0'
                    
                    # Second row has KOs
                    second_row = wld_table.find_all('tr')[1] if len(wld_table.find_all('tr')) > 1 else None
                    if second_row:
                        ko_cells = second_row.find_all(['td', 'th'])
                        if ko_cells:
                            # First cell should have win KOs
                            if len(ko_cells) > 0:
                                ko_text = ko_cells[0].get_text()
                                ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                                if ko_match:
                                    data['proWinsByKnockout'] = ko_match.group(1)
                            # Second cell should have loss KOs
                            if len(ko_cells) > 1:
                                ko_text = ko_cells[1].get_text()
                                ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                                if ko_match:
                                    data['proLossesByKnockout'] = ko_match.group(1)
    
    # Look for amateur record section
    # This would typically be in a separate section or table
    amateur_section = soup.find(string=re.compile(r'amateur', re.IGNORECASE))
    if amateur_section:
        # Try to find amateur record table near this text
        parent = amateur_section.parent
        while parent and parent.name != 'table':
            parent = parent.parent
        
        if parent and parent.name == 'table':
            # Parse amateur record similar to pro record
            # This is a placeholder - actual structure may vary
            pass
    
    # Parse dataTable for fight history
    bouts = []
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
                result = None
                result_method = None
                result_round = None
                
                if result_cell:
                    result_div = result_cell.find('div', {'class': 'boutResult'})
                    if result_div:
                        result_text = clean_text(result_div.get_text())
                        # Parse result like "W PTS", "L KO 3", "W TKO 7"
                        if result_text:
                            parts = result_text.split()
                            if parts:
                                # Map W/L/D/NC to win/loss/draw/no-contest
                                result_map = {'W': 'win', 'L': 'loss', 'D': 'draw', 'NC': 'no-contest'}
                                result = result_map.get(parts[0], None)
                                
                                # Extract method and round
                                if len(parts) > 1:
                                    method_text = ' '.join(parts[1:])
                                    
                                    # Check for round number at the end
                                    round_match = re.search(r'(\d+)$', method_text)
                                    if round_match:
                                        result_round = int(round_match.group(1))
                                        method_text = method_text[:round_match.start()].strip()
                                    
                                    # Map method
                                    method_text = method_text.upper()
                                    if 'TKO' in method_text:
                                        result_method = 'tko'
                                    elif 'KO' in method_text:
                                        result_method = 'ko'
                                    elif any(x in method_text for x in ['PTS', 'UD', 'MD', 'SD', 'DEC']):
                                        result_method = 'decision'
                                    elif 'DQ' in method_text:
                                        result_method = 'dq'
                                    elif 'RTD' in method_text:
                                        result_method = 'rtd'
                
                # Extract event and bout links
                event_link = None
                bout_link = None
                
                # Look for event link (typically /en/event/XXXXX)
                event_anchor = row.find('a', href=re.compile(r'/event/\d+'))
                if event_anchor:
                    event_link = f"https://boxrec.com{event_anchor['href']}"
                
                # Look for bout link (typically /en/event/XXXXX/YYYYYYY)
                bout_anchor = row.find('a', href=re.compile(r'/event/\d+/\d+'))
                if bout_anchor:
                    bout_link = f"https://boxrec.com{bout_anchor['href']}"
                
                bout = {
                    'boxerId': data['boxrecId'],  # Link to the boxer
                    'boutDate': format_date_iso(clean_text(date_cell.get_text())) if date_cell else '',
                    'opponentName': opponent_name or '',
                    'opponentId': opponent_id or '',
                    'opponentUrl': opponent_url or '',
                    'opponentWeight': '',  # Not available in this view
                    'opponentRecord': opponent_record or '',
                    'recentForm': recent_form or '',
                    'eventName': '',  # Not available in this view
                    'venueName': venue or '',
                    'refereeName': '',  # Not available in this view
                    'judge1Name': '',  # Not available in this view
                    'judge1Score': '',
                    'judge2Name': '',
                    'judge2Score': '',
                    'judge3Name': '',
                    'judge3Score': '',
                    'numRoundsScheduled': '',  # Not available in this view
                    'result': result or '',
                    'resultMethod': result_method or '',
                    'resultRound': str(result_round) if result_round else '',
                    'eventPageLink': event_link or '',
                    'boutPageLink': bout_link or '',
                    'scorecardsPageLink': '',  # Not available in this view
                    'titleFight': '',  # Not available in this view
                    'boutRating': str(bout_rating) if bout_rating else ''
                }
                
                # Only add if we have meaningful data
                if bout['boutDate'] and bout['opponentName']:
                    bouts.append(bout)
    
    data['bouts'] = bouts
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_boxer_v3.py <html_file>")
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