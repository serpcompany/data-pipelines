#!/usr/bin/env python3

import json
import os
from pathlib import Path


def combine_boxer_json_files(input_dir, output_file):
    """
    Combine multiple boxer JSON files into a single JSON file.
    
    Args:
        input_dir (str): Directory containing individual boxer JSON files
        output_file (str): Path to the output combined JSON file
    
    Returns:
        dict: Statistics about the combination process
    """
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"Input directory '{input_dir}' does not exist or is not a directory")
    
    boxers = []
    stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'failed_files': []
    }
    
    # Get all JSON files that match the boxer pattern
    json_files = list(input_path.glob('*_box-pro_*.json'))
    stats['total_files'] = len(json_files)
    
    print(f"Found {len(json_files)} boxer JSON files to process...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                boxer_data = json.load(f)
                
                # Add the filename for reference
                boxer_data['source_file'] = json_file.name
                
                boxers.append(boxer_data)
                stats['successful'] += 1
                
                if stats['successful'] % 10 == 0:
                    print(f"Processed {stats['successful']} files...")
                    
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {json_file.name}: {e}")
            stats['failed'] += 1
            stats['failed_files'].append(json_file.name)
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
            stats['failed'] += 1
            stats['failed_files'].append(json_file.name)
    
    # Sort boxers by name for consistent output
    boxers.sort(key=lambda x: x.get('name', ''))
    
    # Create the combined data structure
    combined_data = {
        'boxers': boxers,
        'metadata': {
            'total_boxers': len(boxers),
            'source_directory': str(input_dir),
            'generation_stats': stats
        }
    }
    
    # Write the combined JSON file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCombination complete!")
    print(f"Total files processed: {stats['total_files']}")
    print(f"Successfully combined: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    if stats['failed_files']:
        print(f"Failed files: {', '.join(stats['failed_files'])}")
    print(f"Output written to: {output_file}")
    
    return stats


def combine_boxer_json_by_criteria(input_dir, output_file, filter_func=None):
    """
    Combine boxer JSON files with optional filtering.
    
    Args:
        input_dir (str): Directory containing individual boxer JSON files
        output_file (str): Path to the output combined JSON file
        filter_func (callable): Optional function to filter boxers
                               Should take a boxer dict and return True to include
    
    Returns:
        dict: Statistics about the combination process
    """
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"Input directory '{input_dir}' does not exist or is not a directory")
    
    boxers = []
    stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'filtered_out': 0,
        'failed_files': []
    }
    
    json_files = list(input_path.glob('*_box-pro_*.json'))
    stats['total_files'] = len(json_files)
    
    print(f"Found {len(json_files)} boxer JSON files to process...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                boxer_data = json.load(f)
                
                # Apply filter if provided
                if filter_func and not filter_func(boxer_data):
                    stats['filtered_out'] += 1
                    continue
                
                # Add the filename for reference
                boxer_data['source_file'] = json_file.name
                
                boxers.append(boxer_data)
                stats['successful'] += 1
                
                if stats['successful'] % 10 == 0:
                    print(f"Processed {stats['successful']} files...")
                    
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {json_file.name}: {e}")
            stats['failed'] += 1
            stats['failed_files'].append(json_file.name)
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
            stats['failed'] += 1
            stats['failed_files'].append(json_file.name)
    
    # Sort boxers by name
    boxers.sort(key=lambda x: x.get('name', ''))
    
    # Create the combined data structure
    combined_data = {
        'boxers': boxers,
        'metadata': {
            'total_boxers': len(boxers),
            'source_directory': str(input_dir),
            'generation_stats': stats
        }
    }
    
    # Write the combined JSON file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCombination complete!")
    print(f"Total files processed: {stats['total_files']}")
    print(f"Successfully combined: {stats['successful']}")
    print(f"Filtered out: {stats['filtered_out']}")
    print(f"Failed: {stats['failed']}")
    if stats['failed_files']:
        print(f"Failed files: {', '.join(stats['failed_files'])}")
    print(f"Output written to: {output_file}")
    
    return stats


def example_filters():
    """Example filter functions for combine_boxer_json_by_criteria"""
    
    # Filter for active boxers only
    def active_only(boxer):
        return boxer.get('status', '').lower() == 'active'
    
    # Filter for boxers with winning records
    def winning_record(boxer):
        record = boxer.get('record', {})
        wins = record.get('wins', 0)
        losses = record.get('losses', 0)
        return wins > losses
    
    # Filter for specific nationality
    def nationality_filter(nationality):
        def filter_func(boxer):
            return boxer.get('nationality', '').lower() == nationality.lower()
        return filter_func
    
    # Filter for minimum number of fights
    def min_fights(min_count):
        def filter_func(boxer):
            record = boxer.get('record', {})
            return record.get('total_fights', 0) >= min_count
        return filter_func
    
    return {
        'active_only': active_only,
        'winning_record': winning_record,
        'nationality_filter': nationality_filter,
        'min_fights': min_fights
    }


if __name__ == "__main__":
    # Default paths
    input_directory = "/Users/devin/repos/projects/data-pipelines/boxing/boxrec_scraper/data/processed"
    output_file = "/Users/devin/repos/projects/data-pipelines/boxing/boxrec_scraper/outputs/combined_boxers.json"
    
    # Example 1: Combine all boxer JSON files
    print("Combining all boxer JSON files...")
    combine_boxer_json_files(input_directory, output_file)
    
    # Example 2: Combine only boxers with winning records
    # filters = example_filters()
    # output_file_winners = "/Users/devin/repos/projects/data-pipelines/boxing/boxrec_scraper/combined_winners.json"
    # print("\n\nCombining only boxers with winning records...")
    # combine_boxer_json_by_criteria(input_directory, output_file_winners, filters['winning_record'])