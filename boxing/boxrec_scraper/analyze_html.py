#!/usr/bin/env python3
"""Analyze BoxRec HTML structure to understand data location."""

import sys
from bs4 import BeautifulSoup
import re

def analyze_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    # Remove script and style tags
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Look for key patterns
    print("=== SEARCHING FOR KEY DATA PATTERNS ===\n")
    
    # Record pattern
    record_matches = re.findall(r'\d+-\d+-\d+\s*\(\d+\s*KOs?\)', text)
    if record_matches:
        print(f"Found record patterns: {record_matches}")
    
    # Height pattern
    height_matches = re.findall(r'\d+[′\']\s*\d+[″"]\s*/\s*\d+cm', text)
    if height_matches:
        print(f"Found height patterns: {height_matches}")
    
    # Date patterns
    date_matches = re.findall(r'\d{4}/\d{2}/\d{2}', text)
    if date_matches:
        print(f"Found date patterns (first 5): {date_matches[:5]}")
    
    print("\n=== ANALYZING TABLE STRUCTURES ===\n")
    
    # Find all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables):
        # Get table attributes
        attrs = table.attrs
        print(f"\nTable {i}: {attrs}")
        
        # Check first few rows
        rows = table.find_all('tr')[:3]
        for j, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            cell_texts = [cell.get_text().strip()[:30] for cell in cells]
            print(f"  Row {j}: {cell_texts}")
    
    print("\n=== SEARCHING FOR DATA SECTIONS ===\n")
    
    # Look for sections/divs with interesting classes
    for tag in ['section', 'div']:
        elements = soup.find_all(tag, class_=True)
        interesting_classes = [e for e in elements if any(word in str(e.get('class', '')).lower() 
                              for word in ['boxer', 'profile', 'info', 'detail', 'stat', 'record'])]
        
        for elem in interesting_classes[:5]:
            print(f"\n{tag} with class: {elem.get('class')}")
            # Get some text preview
            text_preview = elem.get_text().strip()[:200]
            print(f"Text preview: {text_preview}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_html.py <html_file>")
        sys.exit(1)
    
    analyze_html(sys.argv[1])