#!/usr/bin/env python3
"""Extract all fields and save to JSON."""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from base_extractor import load_html

# Import all extractors
from extract_name import extract_name
from extract_boxrec_id import extract_boxrec_id
from extract_birth_date import extract_birth_date
from extract_birth_name import extract_birth_name
from extract_birth_place import extract_birth_place
from extract_nicknames import extract_nicknames
from extract_gender import extract_gender
from extract_nationality import extract_nationality
from extract_height import extract_height
from extract_reach import extract_reach
from extract_stance import extract_stance
from extract_division import extract_division
from extract_residence import extract_residence
from extract_debut_date import extract_debut_date
from extract_status import extract_status
from extract_avatar_image import extract_avatar_image
from extract_wiki_url import extract_wiki_url
from extract_promoter import extract_promoter
from extract_trainer import extract_trainer
from extract_manager import extract_manager
from extract_gym import extract_gym
from extract_total_bouts import extract_total_bouts
from extract_total_rounds import extract_total_rounds
from extract_record import extract_record
from extract_bouts import extract_bouts

def extract_all_fields(html_path):
    """Extract all fields from HTML and return as dictionary."""
    
    soup = load_html(html_path)
    
    # Extract basic fields
    data = {
        'id': '',  # Will be set by database
        'boxrecId': extract_boxrec_id(soup) or '',
        'boxrecUrl': '',  # Will be constructed from ID
        'boxrecWikiUrl': extract_wiki_url(soup) or '',
        'slug': '',  # Will be generated from name
        'name': extract_name(soup) or '',
        'birthName': extract_birth_name(soup) or '',
        'nicknames': extract_nicknames(soup) or '',
        'avatarImage': extract_avatar_image(soup) or '',
        'residence': extract_residence(soup) or '',
        'birthPlace': extract_birth_place(soup) or '',
        'dateOfBirth': extract_birth_date(soup) or '',
        'gender': extract_gender(soup) or '',
        'nationality': extract_nationality(soup) or '',
        'height': extract_height(soup) or '',
        'reach': extract_reach(soup) or '',
        'stance': extract_stance(soup) or '',
        'bio': '',  # Not extracted yet
        'promoters': extract_promoter(soup) or '',
        'trainers': extract_trainer(soup) or '',
        'managers': extract_manager(soup) or '',
        'gym': extract_gym(soup) or '',
        'proDebutDate': extract_debut_date(soup) or '',
        'proDivision': extract_division(soup) or '',
        'proWins': '0',
        'proWinsByKnockout': '0',
        'proLosses': '0',
        'proLossesByKnockout': '0',
        'proDraws': '0',
        'proStatus': extract_status(soup) or '',
        'proTotalBouts': extract_total_bouts(soup) or '',
        'proTotalRounds': extract_total_rounds(soup) or '',
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
    
    # Construct BoxRec URL
    if data['boxrecId']:
        data['boxrecUrl'] = f"https://boxrec.com/en/box-pro/{data['boxrecId']}"
    
    # Generate slug from name
    if data['name']:
        import re
        data['slug'] = re.sub(r'[^a-z0-9]+', '-', data['name'].lower()).strip('-')
    
    # Extract record
    record = extract_record(soup)
    if record:
        data['proWins'] = record.get('wins', '0')
        data['proLosses'] = record.get('losses', '0')
        data['proDraws'] = record.get('draws', '0')
        data['proWinsByKnockout'] = record.get('wins_by_ko', '0')
        data['proLossesByKnockout'] = record.get('losses_by_ko', '0')
    
    # Extract bouts
    bouts = extract_bouts(soup) or []
    
    # Format bouts for storage
    formatted_bouts = []
    for bout in bouts:
        formatted_bout = {
            'boxrecId': data['boxrecId'],
            'boutDate': bout.get('date', ''),
            'opponentName': bout.get('opponent_name', ''),
            'opponentBoxrecId': bout.get('opponent_id', ''),
            'opponentUrl': bout.get('opponent_url', ''),
            'opponentWeight': '',
            'opponentRecord': bout.get('opponent_record', ''),
            'recentForm': bout.get('recent_form', ''),
            'eventName': '',
            'venueName': bout.get('venue', ''),
            'refereeName': '',
            'judge1Name': '',
            'judge1Score': '',
            'judge2Name': '',
            'judge2Score': '',
            'judge3Name': '',
            'judge3Score': '',
            'numRoundsScheduled': '',
            'result': bout.get('result', ''),
            'resultMethod': bout.get('result_method', ''),
            'resultRound': bout.get('result_round', ''),
            'eventPageLink': bout.get('event_link', ''),
            'boutPageLink': bout.get('bout_link', ''),
            'scorecardsPageLink': '',
            'titleFight': '',
            'boutRating': str(bout.get('rating', ''))
        }
        formatted_bouts.append(formatted_bout)
    
    data['bouts'] = formatted_bouts
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_all_to_json.py <html_file> [output_file]")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not Path(html_file).exists():
        print(f"File not found: {html_file}")
        sys.exit(1)
    
    # Extract all data
    data = extract_all_fields(html_file)
    
    # Output file
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = Path(html_file).stem + '_extracted.json'
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted data saved to: {output_file}")
    print(f"Boxer: {data['name']}")
    print(f"BoxRec ID: {data['boxrecId']}")
    print(f"Record: {data['proWins']}-{data['proLosses']}-{data['proDraws']}")
    print(f"Bouts: {len(data['bouts'])}")

if __name__ == "__main__":
    main()