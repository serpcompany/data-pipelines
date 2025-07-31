## boxer single page

### 1. Boxer Data

- id (primary key)
- boxrec_id (unique)
- boxrec_url (unique)
- boxrec_wiki_url (unique)
- slug (unique, url-friendly)
- full_name
- birth_name
- nickname
- image_url
- residence
- birth_place
- date_of_birth
- gender
- nationality
- height
- reach
- weight
- stance (orthodox/southpaw/switch)
- bio (text)
- promoter
- trainer
- manager
- gym
- pro_debut_date
- pro_division
- pro_wins
- pro_wins_by_knockout
- pro_losses
- pro_losses_by_knockout
- pro_draws
- pro_status (active, retired)
- pro_total_bouts
- pro_total_rounds
- amateur_debut_date
- amateur_division
- amateur_wins
- amateur_wins_by_knockout
- amateur_losses
- amateur_losses_by_knockout
- amateur_draws
- amateur_status (active, retired)
- amateur_total_bouts
- amateur_total_rounds
- created_at
- updated_at

### 2. Fights table data

**For each fight:**

- bout_date
- opponent_name
- opponent_weight
- opponent_record
- venue_name
- referee_name
- judge_1_name
- judge_1_score
- judge_2_name
- judge_2_score
- judge_3_name
- judge_3_score
- num_rounds_scheduled
- result (win/loss/draw/no-contest)
- result_method (ko/tko/decision/dq/rtd)
- result_round
- event_page_link
- bout_page_link
- scorecards_page_link
- title_fight (boolean)