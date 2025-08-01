# BOXREC DATA PIPELINE OVERVIEW

## Pipeline Order:

1. Scrape Boxer raw HTML files, file: scrape_raw_html/scrape_boxers_html.py
2. Scrape Wiki Pages, file: scrape_raw_html/scrape_wiki_html.py
3. Validate HTML, file: validate_scrapes.py
4. Upload All HTML to DB, file: upload_boxer_html_to_db.py
5. Extract Additional URLs, file: extract_urls_from_raw_html/extract_opponent_urls.py / extract_urls_from_raw_html/extract_bout_urls.py
6. Scrape & Upload Additional Pages, file: scrape_raw_html/scrape_boxers_html.py
7. Validate HTML (remove login pages failures), file: simple_validate.py
8. Extract fields from HTML (currently into JSON), file: extract_field_data_from_raw_html/batch_extract_all.py
