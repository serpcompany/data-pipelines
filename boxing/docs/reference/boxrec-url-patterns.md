
# Boxrec URL Patterns

## boxer single

**Old boxrec urls were on /proboxer/, but they changed to /box-pro/:**
- `https://boxrec.com/en/box-pro/3192`
- `https://boxrec.com/en/proboxer/3192`
- `boxrec_id` = `3192` 

**Pro vs. Am:**
- Professional URL pattern: https://boxrec.com/en/box-am/497268
- Amateur URL pattern: https://boxrec.com/en/box-am/497268

### Event URL pattern
- syntax: `https://boxrec.com/en/event/{boxrec_event_id}`
- example (`boxrec_event_id` = `10101`):  `https://boxrec.com/en/event/10101/`

### Bout URL pattern
- syntax: `https://boxrec.com/en/event/{boxrec_event_id}/{boxrec_bout_id}`
- example (`boxrec_bout_id` = `15745`):  `https://boxrec.com/en/event/10101/15745`

> notice how a bout is tied to an event, and an event will have multiple bouts (probably)

### Scoring URL pattern
- `https://boxrec.com/en/scoring/15745/`
- `boxrec_scoring_id` = `15745`

**Note:** The scoring URLs only show on the boxer single page when LOGGED IN.
