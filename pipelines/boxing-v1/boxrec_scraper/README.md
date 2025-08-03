# BoxRec Scraper & Parser

A comprehensive Python pipeline for scraping BoxRec data and converting HTML to structured JSON with schema versioning and data validation.

- [boxrec.com urls for scraping spreadsheet](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)


## Pipeline Flow

1. Scrape Boxer raw HTML files, file: `scrape_raw_html/scrape_boxers_html.py`

```py
python scrape_raw_html/scrape_boxers_html.py 5000boxers.csv --workers 10
```

2. Scrape Wiki Pages, file: `scrape_raw_html/scrape_wiki_html.py`
3. Validate HTML, file: `validate_scrapes.py`
4. Upload All HTML to DB, file: `upload_boxer_html_to_db.py`
5. Extract Additional URLs, file: `extract_urls_from_raw_html/extract_opponent_urls.py` / `extract_urls_from_raw_html/extract_bout_urls.py`
6. Extract fields from HTML (currently into JSON), file: `extract_field_data_from_raw_html/batch_extract_all.py`
7. Move the JSON files into the boxingundefeated.com project and use the seed scripts in `servers/tasks/seed-*.ts` to load it into the DB
