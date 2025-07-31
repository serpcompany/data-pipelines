# Field Mapping Analysis: Current vs Required

## Boxer Profile Fields

### ✅ Fields We Already Extract:
- `boxrec_id` → boxrec_id ✅
- `boxrec_url` → boxrec_url ✅
- `wiki` → boxrec_wiki_url ✅
- `slug` → slug ✅
- `name` → full_name ✅
- `birth_name` → birth_name ✅
- `alias` → nickname ✅
- `residence` → residence ✅
- `birth_place` → birth_place ✅
- `sex` → gender ✅
- `nationality` → nationality ✅
- `height` → height ✅
- `reach` → reach ✅
- `stance` → stance ✅
- `promoter` → promoter ✅
- `manager_agent` → manager ✅
- `debut` → pro_debut_date ✅
- `division` → pro_division ✅
- `record.wins` → pro_wins ✅
- `record.kos` → pro_wins_by_knockout ✅
- `record.losses` → pro_losses ✅
- `record.draws` → pro_draws ✅
- `status` → pro_status ✅
- `bouts_count` → pro_total_bouts ✅
- `rounds_count` → pro_total_rounds ✅

### ❌ Missing Boxer Fields:
- `image_url` - Profile image
- `date_of_birth` - We have birth_place but not birth_date
- `weight` - Current weight class/weight
- `bio` - Biography text
- `trainer` - Trainer name
- `gym` - Boxing gym
- `pro_losses_by_knockout` - KO losses count
- Amateur record fields (all missing):
  - `amateur_debut_date`
  - `amateur_division`
  - `amateur_wins`
  - `amateur_wins_by_knockout`
  - `amateur_losses`
  - `amateur_losses_by_knockout`
  - `amateur_draws`
  - `amateur_status`
  - `amateur_total_bouts`
  - `amateur_total_rounds`

## Fight/Bout Fields

### ✅ Fields We Already Extract:
- `date` → bout_date ✅
- `opponent` → opponent_name ✅
- `opponent_record` → opponent_record ✅
- `venue` → venue_name ✅
- `result` → result (partial - only W/L/D) ⚠️

### ❌ Missing Fight Fields:
- `opponent_weight` - Opponent's weight for the fight
- `referee_name` - Referee for the bout
- `judge_1_name`, `judge_1_score` - Judge scoring
- `judge_2_name`, `judge_2_score` - Judge scoring
- `judge_3_name`, `judge_3_score` - Judge scoring
- `num_rounds_scheduled` - Scheduled rounds
- `result_method` - KO/TKO/Decision/DQ/RTD
- `result_round` - Which round the fight ended
- `event_page_link` - Link to event page
- `bout_page_link` - Link to specific bout page
- `scorecards_page_link` - Link to scorecards
- `title_fight` - Whether it was a title fight

## Data Source Analysis

Many missing fields require:
1. **Profile page parsing improvements**:
   - Image URL from profile photo
   - Birth date (if available)
   - Trainer/Gym info
   - Bio text
   - KO losses count

2. **Individual bout page scraping**:
   - Referee, judges, scores
   - Fight details (method, round, weight)
   - Title fight status
   
3. **Amateur record page**:
   - Separate amateur career data
   - May require additional URL pattern

## Recommended Approach

1. **Phase 1**: Update parser to extract all available fields from current HTML
2. **Phase 2**: Add bout detail page scraping for fight-specific data
3. **Phase 3**: Add amateur record scraping if needed
4. **Schema Version**: This will be a breaking change → v2.0.0