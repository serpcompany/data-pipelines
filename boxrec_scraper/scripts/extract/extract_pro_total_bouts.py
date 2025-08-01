#!/usr/bin/env python3
"""Extract professional total bouts from HTML."""

import re
from base_extractor import load_html, test_extraction

def extract_pro_total_bouts(soup):
    """Extract professional total bouts from HTML."""
    
    # Method 1: Calculate from W-L-D
    wld_table = soup.find('table', {'class': 'profileWLD'})
    if wld_table:
        first_row = wld_table.find('tr')
        if first_row:
            cells = first_row.find_all(['td', 'th'])
            if len(cells) >= 3:
                wins = 0
                losses = 0
                draws = 0
                
                # Try bgW/bgL/bgD classes first
                win_cell = first_row.find(class_='bgW')
                if win_cell and win_cell.get_text().strip().isdigit():
                    wins = int(win_cell.get_text().strip())
                
                loss_cell = first_row.find(class_='bgL')
                if loss_cell and loss_cell.get_text().strip().isdigit():
                    losses = int(loss_cell.get_text().strip())
                
                draw_cell = first_row.find(class_='bgD')
                if draw_cell and draw_cell.get_text().strip().isdigit():
                    draws = int(draw_cell.get_text().strip())
                
                # If classes not found, try by position
                if wins == 0 and losses == 0 and draws == 0:
                    if cells[0].get_text().strip().isdigit():
                        wins = int(cells[0].get_text().strip())
                    if cells[1].get_text().strip().isdigit():
                        losses = int(cells[1].get_text().strip())
                    if cells[2].get_text().strip().isdigit():
                        draws = int(cells[2].get_text().strip())
                
                total = wins + losses + draws
                if total > 0:
                    return total
    
    # Method 2: Look for explicit bouts field in profileTable
    profile_table = soup.find('table', {'class': 'profileTable'})
    if profile_table:
        row_tables = profile_table.find_all('table', {'class': 'rowTable'})
        
        for row_table in row_tables:
            rows = row_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'bouts' in label and 'count' not in label:
                        if value.isdigit():
                            return int(value)
    
    return None

if __name__ == "__main__":
    test_extraction(extract_pro_total_bouts)