# README



## Entities

- boxer: https://boxrec.com/en/box-pro/659772
- event: https://boxrec.com/en/event/761409


we are setting up a boxing data pipeline. but we    │
│   need source data - from boxrec.com. \               │
│   \                                                   │
│   the bst way i personally know is to crawl using     │
│   zyte and simply download the the html so we can     │
│   extracrt later offline. \                           │
│   \                                                   │
│   /Users/devin/repos/projects/data-pipelines/zyte-re  │
│   ference.md            


Can we use this repo (https://github.com/boxing/boxrec) to:

1. create a schema/list of data points from boxrec? (is it up to date)
2. actually get info


- Boxer URL pattern: `https://boxrec.com/en/box-pro/3192` OR `https://boxrec.com/en/proboxer/3192`
  - `boxrec_id` = `3192` 
- Event URL pattern: `https://boxrec.com/en/event/10101`
  - ``boxrec_event_id` = `10101`
- Bout URL pattern: `https://boxrec.com/en/event/10101/15745`
  - `boxrec_bout_id` = `15745`
- Scoring URL pattern: `https://boxrec.com/en/scoring/15745/`
  - `boxrec_scoring_id` = `15745`


## Note:

- The `boxrec_bout_URL` contains the `boxrec_event_id` and the `boxrec_bout_id`

- The `boxrec_scoring_URL` == `boxrec_bout_id`

- the `scoring` URLs only show on the boxer single page when LOGGED IN.****

## Boxing targets

- https://box.live/ 
- https://www.martialbot.com/
- https://boxrec.com/