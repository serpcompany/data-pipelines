# Boxer Data Extraction Mismatches

## Field Mapping Issues

### 1. Field Name Mismatches
- **Expected**: `name` → **Script**: `full_name`
- **Expected**: `nicknames` (plural, comma-separated) → **Script**: `nickname` (singular)
- **Expected**: `avatarImage` → **Script**: `image_url`
- **Expected**: `dateOfBirth` (format: "4-24-1977") → **Script**: `date_of_birth` (looking for "YYYY-MM-DD")
- **Expected**: `promoters` (plural, comma-separated) → **Script**: `promoter` (singular)
- **Expected**: `trainers` (plural) → **Script**: `trainer` (singular)
- **Expected**: `managers` (plural) → **Script**: `manager` (singular)

### 2. Missing Fields in Script
- `boxrecWikiUrl` - Script extracts it but as `boxrec_wiki_url`
- `proLossesByKnockout` - Not extracted (script doesn't parse losses by KO)
- Amateur record fields - Script has placeholders but doesn't extract:
  - `amateurDebutDate`
  - `amateurDivision`
  - `amateurWins`
  - `amateurWinsByKnockout`
  - `amateurLosses`
  - `amateurLossesByKnockout`
  - `amateurDraws`
  - `amateurStatus`
  - `amateurTotalBouts`
  - `amateurTotalRounds`

### 3. Date Format Issues
- Expected date format: "M-D-YYYY" (e.g., "4-24-1977", "10-11-1996")
- Script searches for: "YYYY-MM-DD" format

### 4. Value Extraction Issues
- **Height/Reach**: Expected as numeric values (e.g., "173", "183") but script may extract with units
- **Multiple values**: Promoters, trainers, managers should handle comma-separated lists
- **Nicknames**: Should handle multiple nicknames in quotes (e.g., '"Money","Pretty Boy"')

### 5. Additional Fields in Script Not in Expected
- `rating`
- `titles`
- `ko_percentage`
- `bouts` (fight history)
- `career`
- `company`

## Required Fixes

1. Update field names to match expected camelCase format
2. Implement amateur record extraction logic
3. Fix date parsing to handle "M-D-YYYY" format
4. Handle multiple values for promoters, trainers, managers, nicknames
5. Extract numeric-only values for height and reach
6. Add extraction for losses by knockout
7. Ensure proper URL formatting for boxrecWikiUrl