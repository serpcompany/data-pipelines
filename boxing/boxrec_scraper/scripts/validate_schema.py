#!/usr/bin/env python3
"""
Schema validation script for BoxRec data.

This script validates JSON data against the current schema version
and can also perform migrations between schema versions.
"""

import json
import os
import sys
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator


def load_schema(version):
    """Load a specific schema version."""
    schema_path = Path(__file__).parent.parent / 'schema' / f'v{version}.json'
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema version {version} not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)


def load_migrations():
    """Load the migrations metadata."""
    migrations_path = Path(__file__).parent.parent / 'schema' / 'migrations.json'
    with open(migrations_path, 'r') as f:
        return json.load(f)


def validate_file(json_file, schema):
    """Validate a single JSON file against the schema."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)


def validate_directory(directory, schema_version=None):
    """Validate all JSON files in a directory."""
    if schema_version is None:
        migrations = load_migrations()
        schema_version = migrations['current_version']
    
    schema = load_schema(schema_version)
    validator = Draft7Validator(schema)
    
    directory = Path(directory)
    json_files = list(directory.glob('*.json'))
    
    results = {
        'total': len(json_files),
        'valid': 0,
        'invalid': 0,
        'errors': []
    }
    
    print(f"Validating {len(json_files)} files against schema v{schema_version}...")
    
    for json_file in json_files:
        # Skip non-boxer files
        if 'summary' in json_file.name or 'parse_summary' in json_file.name:
            results['total'] -= 1
            continue
            
        valid, error = validate_file(json_file, schema)
        
        if valid:
            results['valid'] += 1
        else:
            results['invalid'] += 1
            results['errors'].append({
                'file': json_file.name,
                'error': error
            })
            print(f"❌ {json_file.name}: {error}")
    
    return results


def migrate_data(data, from_version, to_version):
    """
    Migrate data from one schema version to another.
    
    This is a placeholder for actual migration logic.
    Each migration would have its own transformation rules.
    """
    migrations = load_migrations()
    
    # Find the migration path
    migration_path = []
    for migration in migrations['migrations']:
        if migration['version'] > from_version and migration['version'] <= to_version:
            migration_path.append(migration)
    
    # Apply migrations in order
    migrated_data = data.copy()
    for migration in migration_path:
        # Apply migration transformations based on version
        if migration['version'] == '1.1.0':
            # Example migration: Add new field with default value
            # migrated_data['new_field'] = 'default_value'
            pass
    
    return migrated_data


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate BoxRec JSON data against schema')
    parser.add_argument('path', help='File or directory to validate')
    parser.add_argument('--version', help='Schema version to validate against (default: current)')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix validation errors')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        schema_version = args.version or load_migrations()['current_version']
        schema = load_schema(schema_version)
        
        valid, error = validate_file(path, schema)
        if valid:
            print(f"✅ {path.name} is valid")
            return 0
        else:
            print(f"❌ {path.name} is invalid: {error}")
            return 1
    
    elif path.is_dir():
        results = validate_directory(path, args.version)
        
        print(f"\nValidation Results:")
        print(f"Total files: {results['total']}")
        print(f"Valid: {results['valid']}")
        print(f"Invalid: {results['invalid']}")
        
        if results['invalid'] > 0:
            print(f"\nErrors found in {results['invalid']} files")
            return 1
        else:
            print("\n✅ All files are valid!")
            return 0
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        return 1


if __name__ == '__main__':
    sys.exit(main())