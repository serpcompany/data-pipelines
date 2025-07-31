#!/bin/bash
# Test wiki scraper with a few boxers

echo "BoxRec Wiki Scraper Test"
echo "========================"
echo ""
echo "This will test downloading wiki pages for 5 famous boxers:"
echo "- Floyd Mayweather Jr (352)"
echo "- Mike Tyson (474)"
echo "- Naoya Inoue (628407)"
echo "- Canelo Alvarez (348759)"
echo "- Muhammad Ali (000180)"
echo ""

# Create test JSON file with just these boxers
cat > test_boxers.json << 'EOF'
[
  {"boxrec_id": "352", "name": "Floyd Mayweather Jr"},
  {"boxrec_id": "474", "name": "Mike Tyson"},
  {"boxrec_id": "628407", "name": "Naoya Inoue"},
  {"boxrec_id": "348759", "name": "Canelo Alvarez"},
  {"boxrec_id": "000180", "name": "Muhammad Ali"}
]
EOF

echo "Running wiki scraper..."
echo ""

# Run the scraper on test file
python scripts/scrape_wiki_zyte.py test_boxers.json data/raw/boxrec_wiki_test/

# Clean up
rm test_boxers.json

echo ""
echo "Test complete! Check data/raw/boxrec_wiki_test/ for results."