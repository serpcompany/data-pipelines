# Database Slug Merge Results

## Summary

Successfully merged database slug mappings into the new 36,539 boxer CSV file.

### 📊 Results:
- **Total boxers**: 36,539
- **Matched with database slugs**: 9,464 (25.9%)
- **New boxers (no existing slug)**: 27,075 (74.1%)
- **Duplicate BoxRec IDs found**: 3,607

### 📁 Files Created:
- **`data/boxrec-urls-to-scrape-with-slugs.csv`** - Main output with slug column
- **`data/slug_merge_summary.json`** - Detailed statistics
- **`data/unmatched_boxers.json`** - List of boxers without existing slugs

## Key Findings

### ✅ **Successful Matches (9,464 boxers)**
These boxers already exist in your database and have established slugs:
- Jake Paul → `jake-paul`
- Gervonta Davis → `gervonta-davis` 
- Ryan Garcia → `ryan-garcia`
- Mike Tyson → `mike-tyson`
- Canelo Alvarez → `canelo-alvarez`

### 🆕 **New Boxers (27,075 boxers)**
These are new boxers not in your existing database - they'll need new slugs generated.

### ⚠️ **Duplicates (3,607 entries)**
Found duplicate BoxRec IDs in the CSV - likely the same boxer listed multiple times with slight name variations.

## Next Steps

1. **Clean Duplicates**: Remove duplicate BoxRec IDs from the CSV
2. **Generate Slugs**: Create slugs for the 27,075 new boxers
3. **Validate Matches**: Review slug matches to ensure accuracy
4. **Prioritize Scraping**: Focus on boxers with existing slugs first (established audience)

## Files Ready for Use

The main output file `data/boxrec-urls-to-scrape-with-slugs.csv` contains:
- `name` - Boxer name
- `url` - BoxRec URL 
- `boxrec_id` - Extracted BoxRec ID
- `slug` - Website slug (if exists in database)
- `db_matched` - Whether matched with existing database

This preserves your existing URL structure while adding 27,075 new boxers to potentially scrape!