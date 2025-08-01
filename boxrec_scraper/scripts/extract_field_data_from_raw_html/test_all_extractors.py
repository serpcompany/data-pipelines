#!/usr/bin/env python3
"""Test all extractors on a sample HTML file."""

import sys
from pathlib import Path
from base_extractor import load_html, get_test_file

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

def test_all_extractors(html_path=None):
    """Run all extractors and display results."""
    
    if not html_path:
        html_path = get_test_file()
    
    print(f"Testing all extractors on: {html_path}\n")
    print("=" * 80)
    
    soup = load_html(html_path)
    
    # Define all extractors with their names
    extractors = [
        ("Name", extract_name),
        ("BoxRec ID", extract_boxrec_id),
        ("Birth Date", extract_birth_date),
        ("Birth Name", extract_birth_name),
        ("Birth Place", extract_birth_place),
        ("Nicknames", extract_nicknames),
        ("Gender", extract_gender),
        ("Nationality", extract_nationality),
        ("Height", extract_height),
        ("Reach", extract_reach),
        ("Stance", extract_stance),
        ("Division", extract_division),
        ("Residence", extract_residence),
        ("Debut Date", extract_debut_date),
        ("Status", extract_status),
        ("Avatar Image", extract_avatar_image),
        ("Wiki URL", extract_wiki_url),
        ("Promoter", extract_promoter),
        ("Trainer", extract_trainer),
        ("Manager", extract_manager),
        ("Gym", extract_gym),
        ("Total Bouts", extract_total_bouts),
        ("Total Rounds", extract_total_rounds),
    ]
    
    # Test each extractor
    results = {}
    for name, extractor in extractors:
        try:
            result = extractor(soup)
            results[name] = result
            status = "✓" if result else "✗"
            print(f"{status} {name:20} : {result}")
        except Exception as e:
            results[name] = f"ERROR: {e}"
            print(f"✗ {name:20} : ERROR - {e}")
    
    # Test record extractor separately
    print("\n" + "-" * 80)
    print("Record:")
    try:
        record = extract_record(soup)
        if record:
            print(f"  Wins: {record.get('wins', '0')}")
            print(f"  Losses: {record.get('losses', '0')}")
            print(f"  Draws: {record.get('draws', '0')}")
            print(f"  Wins by KO: {record.get('wins_by_ko', '0')}")
            print(f"  Losses by KO: {record.get('losses_by_ko', '0')}")
        else:
            print("  No record found")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Test bouts extractor separately
    print("\n" + "-" * 80)
    print("Bouts:")
    try:
        bouts = extract_bouts(soup)
        if bouts:
            print(f"  Total bouts extracted: {len(bouts)}")
            if bouts:
                print(f"  First bout: {bouts[0].get('date', '')} vs {bouts[0].get('opponent_name', '')}")
                print(f"  Last bout: {bouts[-1].get('date', '')} vs {bouts[-1].get('opponent_name', '')}")
        else:
            print("  No bouts found")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    print("\n" + "=" * 80)
    
    # Summary
    successful = sum(1 for v in results.values() if v and not str(v).startswith("ERROR"))
    total = len(results)
    print(f"\nSummary: {successful}/{total} fields extracted successfully")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_all_extractors(sys.argv[1])
    else:
        test_all_extractors()