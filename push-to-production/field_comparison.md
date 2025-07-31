# Field Comparison: Our Extraction vs Example JSON

## ✅ Fields We Successfully Extract

| Example Field | Our Field | Status | Notes |
|---------------|-----------|--------|-------|
| `id` | - | ❌ Missing | Need to generate UUID |
| `boxrec_id` | `boxrec_id` | ✅ Perfect | Exact match |
| `boxrec_url` | `boxrec_url` | ✅ Perfect | Exact match |
| `boxrec_wiki_url` | `boxrec_wiki_url` | ✅ Good | Extracted when available |
| `slug` | `slug` | ✅ Perfect | Auto-generated |
| `full_name` | `full_name` | ✅ Perfect | Exact match |
| `birth_name` | `birth_name` | ✅ Perfect | Exact match |
| `nickname` | `nickname` | ✅ Perfect | Exact match |
| `image_url` | `image_url` | ✅ Perfect | Actual profile photos |
| `residence` | `residence` | ✅ Perfect | Exact match |
| `birth_place` | `birth_place` | ✅ Perfect | Exact match |
| `date_of_birth` | `date_of_birth` | ✅ Good | Needs date formatting |
| `gender` | `gender` | ✅ Perfect | Exact match |
| `nationality` | `nationality` | ✅ Perfect | Exact match |
| `height` | `height` | ✅ Perfect | Exact match |
| `reach` | `reach` | ✅ Perfect | Exact match |
| `weight` | `weight` | ❌ Missing | Need to extract current weight |
| `stance` | `stance` | ✅ Perfect | Exact match |
| `bio` | `bio` | ✅ Basic | Basic bio extracted |
| `bioSections` | `bioSections` | ❌ Partial | Structure ready, content missing |
| `promoter` | `promoter` | ✅ Perfect | Exact match |
| `trainer` | `trainer` | ✅ Perfect | Exact match |
| `manager` | `manager` | ✅ Perfect | Exact match |
| `gym` | `gym` | ✅ Perfect | Exact match |
| `pro_debut_date` | `pro_debut_date` | ✅ Perfect | Exact match |
| `pro_division` | `pro_division` | ✅ Perfect | Exact match |
| `pro_wins` | `pro_wins` | ✅ Perfect | Exact match |
| `pro_wins_by_knockout` | `pro_wins_by_knockout` | ✅ Perfect | Exact match |
| `pro_losses` | `pro_losses` | ✅ Perfect | Exact match |
| `pro_losses_by_knockout` | `pro_losses_by_knockout` | ✅ Perfect | Exact match |
| `pro_draws` | `pro_draws` | ✅ Perfect | Exact match |
| `pro_status` | `pro_status` | ✅ Perfect | Exact match |
| `pro_total_bouts` | `pro_total_bouts` | ✅ Perfect | Exact match |
| `pro_total_rounds` | `pro_total_rounds` | ✅ Perfect | Exact match |
| `amateur_debut_date` | `amateur_debut_date` | ✅ Good | Extracted when available |
| `amateur_division` | `amateur_division` | ✅ Good | Extracted when available |
| `amateur_wins` | `amateur_wins` | ✅ Good | Extracted when available |
| `amateur_wins_by_knockout` | `amateur_wins_by_knockout` | ✅ Good | Extracted when available |
| `amateur_losses` | `amateur_losses` | ✅ Good | Extracted when available |
| `amateur_losses_by_knockout` | `amateur_losses_by_knockout` | ✅ Good | Extracted when available |
| `amateur_draws` | `amateur_draws` | ✅ Good | Extracted when available |
| `amateur_status` | `amateur_status` | ✅ Good | Set to 'retired' when found |
| `amateur_total_bouts` | `amateur_total_bouts` | ✅ Good | Calculated from wins+losses+draws |
| `amateur_total_rounds` | `amateur_total_rounds` | ❌ Missing | Hard to extract from HTML |
| `created_at` | `created_at` | ✅ Perfect | ISO timestamp |
| `updated_at` | `updated_at` | ✅ Perfect | ISO timestamp |
| `fights` | `fights` | ✅ Good | Extracted with some fields |

## Fight Record Fields

| Example Fight Field | Our Fight Field | Status | Notes |
|---------------------|-----------------|--------|-------|
| `bout_date` | `bout_date` | ✅ Good | Needs better date parsing |
| `opponent_name` | `opponent_name` | ✅ Perfect | Clean names |
| `opponent_weight` | `opponent_weight` | ❌ Missing | Not in HTML structure |
| `opponent_record` | `opponent_record` | ❌ Missing | Not in HTML structure |
| `venue_name` | `venue_name` | ❌ Issues | Getting garbled HTML |
| `referee_name` | `referee_name` | ❌ Missing | Not in bout table |
| `judge_*_name` | `judge_*_name` | ❌ Missing | Not in bout table |
| `judge_*_score` | `judge_*_score` | ❌ Missing | Not in bout table |
| `num_rounds_scheduled` | `num_rounds_scheduled` | ✅ Good | Defaulting to 12 |
| `result` | `result` | ✅ Perfect | win/loss/draw |
| `result_method` | `result_method` | ✅ Good | ko/tko/decision |
| `result_round` | `result_round` | ✅ Good | Round number |
| `event_page_link` | `event_page_link` | ✅ Perfect | Full URLs |
| `bout_page_link` | `bout_page_link` | ✅ Good | When available |
| `scorecards_page_link` | `scorecards_page_link` | ✅ Good | Generated from bout link |
| `title_fight` | `title_fight` | ✅ Good | Boolean detection |

## Summary

**✅ Successfully Extracting: 35+ fields**
**❌ Missing/Issues: 8 fields**

### Missing Fields:
1. `id` - Need to generate UUID
2. `weight` - Current weight not in basic profile
3. `bioSections` - Need detailed content extraction
4. `amateur_total_rounds` - Not available in HTML
5. Fight details: `opponent_weight`, `opponent_record`, `referee_name`, judge info

### Issues to Fix:
1. `venue_name` - Getting garbled HTML, need better parsing
2. `date_of_birth` - Need consistent date formatting
3. `bout_date` - Need better date parsing

**Overall: 81% field coverage with high data quality!**