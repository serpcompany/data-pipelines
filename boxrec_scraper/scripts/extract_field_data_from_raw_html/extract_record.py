#!/usr/bin/env python3
"""Extract win-loss-draw record from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_record(soup):
    """Extract boxing record (wins, losses, draws, KOs) from HTML."""
    
    # Method 1: Look for profileWLD table
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        record = {
            'wins': '0',
            'losses': '0',
            'draws': '0',
            'wins_by_ko': '0',
            'losses_by_ko': '0'
        }
        
        # First row has W-L-D
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if len(cells) >= 3:
                # Look for wins (usually has bgW class)
                win_cell = first_row.find(class_='bgW')
                if win_cell:
                    record['wins'] = win_cell.get_text().strip()
                
                # Look for losses (usually has bgL class)
                loss_cell = first_row.find(class_='bgL')
                if loss_cell:
                    record['losses'] = loss_cell.get_text().strip()
                
                # Look for draws (usually has bgD class)
                draw_cell = first_row.find(class_='bgD')
                if draw_cell:
                    record['draws'] = draw_cell.get_text().strip()
        
        # Second row has KOs
        second_row = wld_table.find_all('tr')[1] if len(wld_table.find_all('tr')) > 1 else None
        if second_row:
            ko_cells = second_row.find_all(['td', 'th'])
            if ko_cells:
                # First cell - wins by KO
                if len(ko_cells) > 0:
                    ko_text = ko_cells[0].get_text()
                    ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                    if ko_match:
                        record['wins_by_ko'] = ko_match.group(1)
                
                # Second cell - losses by KO
                if len(ko_cells) > 1:
                    ko_text = ko_cells[1].get_text()
                    ko_match = re.search(r'(\d+)\s*KOs?', ko_text)
                    if ko_match:
                        record['losses_by_ko'] = ko_match.group(1)
        
        return record
    
    return None

if __name__ == "__main__":
    test_extraction(extract_record)