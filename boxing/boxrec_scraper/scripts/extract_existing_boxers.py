#!/usr/bin/env python3
"""
Extract existing boxer data from the live database.
Preserves BoxRec URL to slug mappings for the website.
"""

import os
import csv
import json
import logging
import pymysql
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import re

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)

class BoxerDataExtractor:
    """Extract boxer data from existing database."""
    
    def __init__(self):
        self.connection = None
        self.connect_to_db()
    
    def connect_to_db(self):
        """Connect to the MySQL database."""
        try:
            self.connection = pymysql.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USERNAME'),
                password=os.getenv('DB_PASS'),
                database=os.getenv('DB_NAME'),
                charset='utf8mb4'
            )
            logging.info(f"Connected to database: {os.getenv('DB_NAME')}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
    
    def extract_boxers_with_boxrec_urls(self):
        """Extract boxers that have BoxRec URLs."""
        query = """
        SELECT 
            boxer_name,
            boxrec_url,
            boxer_slug,
            id,
            created_at,
            updated_at
        FROM boxing_boxers 
        WHERE boxrec_url IS NOT NULL 
        ORDER BY boxer_name
        """
        
        try:
            cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            logging.info(f"Found {len(results)} boxers with BoxRec URLs")
            return results
            
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            raise
    
    def extract_boxrec_ids_from_urls(self, boxers):
        """Extract BoxRec IDs from URLs."""
        for boxer in boxers:
            url = boxer.get('boxrec_url', '')
            if url:
                # Extract ID from various BoxRec URL formats
                match = re.search(r'box-pro[/_](\d+)', url)
                if match:
                    boxer['boxrec_id'] = match.group(1)
                else:
                    boxer['boxrec_id'] = None
                    logging.warning(f"Could not extract BoxRec ID from: {url}")
            else:
                boxer['boxrec_id'] = None
        
        return boxers
    
    def get_table_info(self):
        """Get information about the boxing_boxers table structure."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DESCRIBE boxing_boxers")
            columns = cursor.fetchall()
            cursor.close()
            
            logging.info("Table structure:")
            for col in columns:
                logging.info(f"  {col}")
                
            return columns
            
        except Exception as e:
            logging.error(f"Error getting table info: {e}")
            return []
    
    def save_to_csv(self, boxers, filename='existing_boxers.csv'):
        """Save boxer data to CSV."""
        output_file = Path('data') / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not boxers:
            logging.warning("No boxer data to save")
            return
        
        # CSV headers
        headers = boxers[0].keys()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(boxers)
        
        logging.info(f"Saved {len(boxers)} boxers to {output_file}")
        return output_file
    
    def save_to_json(self, boxers, filename='existing_boxers.json'):
        """Save boxer data to JSON."""
        output_file = Path('data') / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'extracted_at': datetime.now().isoformat(),
            'total_boxers': len(boxers),
            'boxers': boxers
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logging.info(f"Saved {len(boxers)} boxers to {output_file}")
        return output_file
    
    def create_url_mapping(self, boxers):
        """Create a mapping of BoxRec URLs to slugs."""
        mapping = {}
        urls_for_scraping = []
        
        for boxer in boxers:
            url = boxer.get('boxrec_url')
            slug = boxer.get('boxer_slug')
            boxrec_id = boxer.get('boxrec_id')
            
            if url and slug:
                mapping[url] = {
                    'slug': slug,
                    'boxer_name': boxer.get('boxer_name'),
                    'boxrec_id': boxrec_id,
                    'db_id': boxer.get('id')
                }
                
                # Add to scraping list if we have a valid BoxRec ID
                if boxrec_id:
                    urls_for_scraping.append(url)
        
        # Save mapping
        mapping_file = Path('data') / 'boxrec_url_slug_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        # Save URLs for scraping
        urls_file = Path('data') / 'existing_boxers_urls.csv'
        with open(urls_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['url'])
            for url in urls_for_scraping:
                writer.writerow([url])
        
        logging.info(f"Created URL mapping: {len(mapping)} entries")
        logging.info(f"URLs for scraping: {len(urls_for_scraping)}")
        logging.info(f"Mapping saved to: {mapping_file}")
        logging.info(f"URLs saved to: {urls_file}")
        
        return mapping, urls_for_scraping
    
    def analyze_data(self, boxers):
        """Analyze the extracted data."""
        total = len(boxers)
        with_boxrec_id = sum(1 for b in boxers if b.get('boxrec_id'))
        unique_boxrec_ids = len(set(b['boxrec_id'] for b in boxers if b.get('boxrec_id')))
        
        logging.info(f"\n📊 Data Analysis:")
        logging.info(f"  Total boxers: {total}")
        logging.info(f"  With BoxRec URLs: {total}")
        logging.info(f"  With extractable BoxRec IDs: {with_boxrec_id}")
        logging.info(f"  Unique BoxRec IDs: {unique_boxrec_ids}")
        
        # Check for duplicates
        if with_boxrec_id != unique_boxrec_ids:
            logging.warning(f"  ⚠️  Found {with_boxrec_id - unique_boxrec_ids} duplicate BoxRec IDs")
        
        return {
            'total': total,
            'with_boxrec_id': with_boxrec_id,
            'unique_boxrec_ids': unique_boxrec_ids
        }
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")


def main():
    """Extract boxer data from existing database."""
    extractor = BoxerDataExtractor()
    
    try:
        # Get table structure
        logging.info("📋 Getting table structure...")
        extractor.get_table_info()
        
        # Extract boxer data
        logging.info("\n🔍 Extracting boxer data...")
        boxers = extractor.extract_boxers_with_boxrec_urls()
        
        # Extract BoxRec IDs from URLs
        logging.info("🔗 Extracting BoxRec IDs from URLs...")
        boxers = extractor.extract_boxrec_ids_from_urls(boxers)
        
        # Analyze data
        stats = extractor.analyze_data(boxers)
        
        # Save data
        logging.info("\n💾 Saving data...")
        csv_file = extractor.save_to_csv(boxers)
        json_file = extractor.save_to_json(boxers)
        
        # Create URL mapping
        logging.info("\n🗺️  Creating URL mappings...")
        mapping, urls = extractor.create_url_mapping(boxers)
        
        # Summary
        logging.info(f"\n✅ Extraction Complete!")
        logging.info(f"  CSV file: {csv_file}")
        logging.info(f"  JSON file: {json_file}")
        logging.info(f"  Ready to scrape: {len(urls)} URLs")
        
        # Show first few entries
        if boxers:
            logging.info(f"\n📝 Sample entries:")
            for i, boxer in enumerate(boxers[:5]):
                logging.info(f"  {i+1}. {boxer['boxer_name']}")
                logging.info(f"     Slug: {boxer['boxer_slug']}")
                logging.info(f"     BoxRec: {boxer['boxrec_url']}")
                logging.info(f"     ID: {boxer['boxrec_id']}")
        
    except Exception as e:
        logging.error(f"Error during extraction: {e}")
        raise
    
    finally:
        extractor.close()


if __name__ == "__main__":
    main()