#!/usr/bin/env python3
"""Extract all bouts/fights from HTML."""

import re
from ....base import load_html, test_extraction

def extract(soup):
    """Extract all bouts from the fight history table."""
    
    bouts = []
    
    # Find the main data table with fight history
    data_table = soup.find('table', {'class': 'dataTable'})
    if not data_table:
        return bouts
    
    # Skip header row
    rows = data_table.find_all('tr')[1:]
    
    for row in rows:
        # Skip rows that are notes/comments (usually have colspan)
        if row.find('td', {'colspan': True}):
            continue
        
        cells = row.find_all('td')
        if len(cells) < 6:
            continue
        
        bout = {}
        
        # Extract date (cell 0)
        date_cell = cells[0]
        bout['date'] = date_cell.get_text().strip() if date_cell else ''
        
        # Extract opponent info (cell 2)
        opponent_cell = cells[2] if len(cells) > 2 else None
        if opponent_cell:
            opponent_link = opponent_cell.find('a', {'class': 'personLink'})
            if opponent_link:
                bout['opponent_name'] = opponent_link.get_text().strip()
                href = opponent_link.get('href')
                if href:
                    id_match = re.search(r'/box-pro/(\d+)', href)
                    if id_match:
                        bout['opponent_id'] = id_match.group(1)
                        bout['opponent_url'] = f"https://boxrec.com{href}"
            else:
                bout['opponent_name'] = opponent_cell.get_text().strip()
        
        # Extract opponent record (cell 3)
        if len(cells) > 3:
            record_cell = cells[3]
            wins = record_cell.find('span', {'class': 'textWon'})
            losses = record_cell.find('span', {'class': 'textLost'})
            draws = record_cell.find('span', {'class': 'textDraw'})
            if wins and losses and draws:
                bout['opponent_record'] = f"{wins.get_text()}-{losses.get_text()}-{draws.get_text()}"
        
        # Extract recent form (cell 4)
        if len(cells) > 4:
            form_cell = cells[4]
            form_imgs = form_cell.find_all('img')
            if form_imgs:
                form_results = []
                for img in form_imgs:
                    src = img.get('src', '')
                    if 'l6w' in src:
                        form_results.append('W')
                    elif 'l6l' in src:
                        form_results.append('L')
                    elif 'l6d' in src:
                        form_results.append('D')
                bout['recent_form'] = ''.join(form_results)
        
        # Extract venue (cell 5)
        if len(cells) > 5:
            venue_cell = cells[5]
            bout['venue'] = venue_cell.get_text().strip() if venue_cell else ''
        
        # Extract result (cell 6)
        if len(cells) > 6:
            result_cell = cells[6]
            result_div = result_cell.find('div', {'class': 'boutResult'})
            if result_div:
                result_text = result_div.get_text().strip()
                if result_text:
                    parts = result_text.split()
                    if parts:
                        # Map W/L/D/NC
                        result_map = {'W': 'win', 'L': 'loss', 'D': 'draw', 'NC': 'no-contest'}
                        bout['result'] = result_map.get(parts[0], parts[0])
                        
                        # Extract method and round
                        if len(parts) > 1:
                            method_text = ' '.join(parts[1:])
                            
                            # Check for round number
                            round_match = re.search(r'(\d+)$', method_text)
                            if round_match:
                                bout['result_round'] = round_match.group(1)
                                method_text = method_text[:round_match.start()].strip()
                            
                            # Map method
                            method_text = method_text.upper()
                            if 'TKO' in method_text:
                                bout['result_method'] = 'tko'
                            elif 'KO' in method_text:
                                bout['result_method'] = 'ko'
                            elif any(x in method_text for x in ['PTS', 'UD', 'MD', 'SD', 'DEC']):
                                bout['result_method'] = 'decision'
                            elif 'DQ' in method_text:
                                bout['result_method'] = 'dq'
                            elif 'RTD' in method_text:
                                bout['result_method'] = 'rtd'
                            else:
                                bout['result_method'] = method_text.lower()
        
        # Extract rating (cell 7)
        if len(cells) > 7:
            rating_cell = cells[7]
            filled_stars = len(rating_cell.find_all('i', {'class': re.compile(r'fas fa-star')}))
            if filled_stars > 0:
                bout['rating'] = filled_stars
        
        # Extract event and bout links
        event_anchor = row.find('a', href=re.compile(r'/event/\d+'))
        if event_anchor:
            bout['event_link'] = f"https://boxrec.com{event_anchor['href']}"
            # Extract event ID from URL
            event_match = re.search(r'/event/(\d+)', event_anchor['href'])
            if event_match:
                bout['event_id'] = event_match.group(1)
        
        bout_anchor = row.find('a', href=re.compile(r'/event/\d+/\d+'))
        if bout_anchor:
            bout['bout_link'] = f"https://boxrec.com{bout_anchor['href']}"
            # Extract bout ID from URL
            bout_match = re.search(r'/event/\d+/(\d+)', bout_anchor['href'])
            if bout_match:
                bout['bout_id'] = bout_match.group(1)
        
        # Only add if we have meaningful data
        if bout.get('date') and bout.get('opponent_name'):
            bouts.append(bout)
    
    return bouts

if __name__ == "__main__":
    result = test_extraction(extract)
    if result and isinstance(result, list):
        print(f"\nTotal bouts found: {len(result)}")
        if result:
            print(f"First bout: {result[0]}")
            print(f"Last bout: {result[-1]}")