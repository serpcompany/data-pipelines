# README

- [boxrec.com urls for scraping spreadsheet](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)


## Boxer URL pattern

- `https://boxrec.com/en/box-pro/3192`
- `https://boxrec.com/en/proboxer/3192`
- `boxrec_id` = `3192` 

## Event URL pattern

- `https://boxrec.com/en/event/10101`
- ``boxrec_event_id` = `10101`

## Bout URL pattern

- `https://boxrec.com/en/event/10101/15745`
- `boxrec_bout_id` = `15745`

## Scoring URL pattern

- `https://boxrec.com/en/scoring/15745/`
- `boxrec_scoring_id` = `15745`


### Note:

- The `boxrec_bout_URL` contains the `boxrec_event_id` and the `boxrec_bout_id`

- The `boxrec_scoring_URL` == `boxrec_bout_id`

- the `scoring` URLs only show on the boxer single page when LOGGED IN.****


# Data Pipeline Flow

1. Get URLs of boxers from boxrec site (manual) - [urls list here](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)
2. run them through the html downloader
3. convert the 'boxer single' HTML files -> JSON objects (so we can populate gh repos or other properties with data)
4. from the JSON, get the data needed to populate the fight tables