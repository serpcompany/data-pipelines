# BOXREC DATA PIPELINE OVERVIEW

## Pipeline Order:

1. Scrape Boxer raw HTML files
2. Scrape Wiki Pages →
3. Validate HTML
4. Upload All HTML to DB
5. Extract Additional URLs
6. Scrape & Upload Additional Pages
7. Validate HTML (remove login pages failures)
8. Extract fields from HTML (currenlty into JSON)
