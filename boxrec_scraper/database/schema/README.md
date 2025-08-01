# BoxRec Data Schema

This directory contains the versioned JSON schemas for BoxRec boxer data.

## Current Version: 1.0.0

## Schema Structure

Each boxer record contains:

### Profile Fields
- `boxrec_id` (required): Unique BoxRec identifier
- `boxrec_url`: Full URL to BoxRec page
- `name` (required): Professional name
- `slug`: URL-friendly name
- `birth_name`: Birth name if different
- `alias`: Nickname
- `nationality`, `stance`, `height`, `reach`: Physical attributes
- `division`, `rating`, `ranking`: Current status
- `titles`: Array of current titles
- `bouts_count`, `rounds_count`, `ko_percentage`: Career statistics

### Record Object (required)
- `wins`, `losses`, `draws`: Fight results
- `kos`: Knockouts achieved
- `total_fights`: Total professional fights

### Bouts Array (required)
Each bout contains:
- `date` (required): Fight date
- `opponent` (required): Opponent name
- `opponent_id`: BoxRec ID for interlinking
- `opponent_url`: Full URL to opponent's page
- `opponent_record`: W-L-D at time of fight
- `recent_form`: Last 6 fight results (e.g., "WWLWWW")
- `result`: W/L/D/NC/VS from this boxer's perspective
- `venue`: Location of the fight
- `bout_rating`: 0-5 star rating

## Schema Versioning

We follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes requiring data migration
- MINOR: New optional fields added
- PATCH: Documentation or validation fixes

## Validation

Use the validation script to check data compliance:

```bash
# Validate a single file
python scripts/validate_schema.py data/processed/en_box-pro_628407.json

# Validate all files in a directory
python scripts/validate_schema.py data/processed/

# Validate against a specific version
python scripts/validate_schema.py data/processed/ --version 1.0.0
```

## Migrations

The `migrations.json` file tracks all schema changes. When making breaking changes:

1. Create a new schema version file (e.g., `v2.0.0.json`)
2. Update `migrations.json` with the changes
3. Implement migration logic in `validate_schema.py`
4. Run migration on existing data
5. Update `current_version` in `migrations.json`

## Adding New Fields

### Non-breaking (Minor version bump):
- Add field as optional with `"type": ["string", "null"]`
- Document the field purpose
- Update the migrations log

### Breaking (Major version bump):
- Create new schema version
- Write migration function
- Test on sample data
- Document migration path

## Best Practices

1. **Always validate** after parsing new data
2. **Document all fields** with descriptions
3. **Use appropriate types** (integer vs string)
4. **Set reasonable constraints** (min/max values, patterns)
5. **Keep backwards compatibility** when possible