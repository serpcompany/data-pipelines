#!/usr/bin/env python3
"""Simple validation script to check data structure."""

import json
import sys
from pathlib import Path


def validate_boxer_data(data):
    """Basic validation of boxer data structure."""
    errors = []
    
    # Check required fields
    required_fields = ['boxrec_id', 'name', 'record', 'bouts']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate record structure
    if 'record' in data:
        record = data['record']
        record_fields = ['wins', 'losses', 'draws', 'kos', 'total_fights']
        for field in record_fields:
            if field not in record:
                errors.append(f"Missing record field: {field}")
    
    # Validate bouts
    if 'bouts' in data and isinstance(data['bouts'], list):
        for i, bout in enumerate(data['bouts']):
            if 'date' not in bout:
                errors.append(f"Bout {i}: missing date")
            if 'opponent' not in bout:
                errors.append(f"Bout {i}: missing opponent")
            
            # Check new fields
            if 'opponent_id' in bout and 'opponent_url' in bout:
                if bout['opponent_id'] and not bout['opponent_url']:
                    errors.append(f"Bout {i}: has opponent_id but missing opponent_url")
    
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_validate.py <json_file_or_directory>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        with open(path, 'r') as f:
            data = json.load(f)
        
        errors = validate_boxer_data(data)
        if errors:
            print(f"❌ {path.name} has {len(errors)} errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print(f"✅ {path.name} is valid")
            return 0
    
    elif path.is_dir():
        files = list(path.glob('*box-pro*.json'))
        valid = 0
        invalid = 0
        
        for file in files:
            with open(file, 'r') as f:
                data = json.load(f)
            
            errors = validate_boxer_data(data)
            if errors:
                invalid += 1
                print(f"❌ {file.name}")
            else:
                valid += 1
        
        print(f"\nTotal: {len(files)} files")
        print(f"Valid: {valid}")
        print(f"Invalid: {invalid}")
        
        return 0 if invalid == 0 else 1


if __name__ == '__main__':
    sys.exit(main())