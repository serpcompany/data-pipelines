"""
Scrape HTML files with Zyte
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import requests
import time
import os
import base64

default_args = {
    'owner': 'boxing-pipeline',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

dag = DAG(
    'scrape_html_zyte',
    default_args=default_args,
    description='Scrape HTML from URLs using Zyte API',
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=['scraping', 'zyte'],
    params={
        'csv_filename': '',  # Required: CSV file with URLs
    },
)

def read_csv_files(**context):
    """Read CSV files from input directory using pandas"""
    input_dir = '/opt/airflow/data/input'
    csv_files = []
    
    # Get filename parameter from DAG run configuration
    params = context.get('params', {})
    specific_file = params.get('csv_filename', '')
    
    if not specific_file:
        raise ValueError("csv_filename parameter is required")
    
    # Process only the specified file
    if specific_file.endswith('.csv'):
        filepath = os.path.join(input_dir, specific_file)
        if os.path.exists(filepath):
            print(f"Reading specified file: {filepath}")
            df = pd.read_csv(filepath)
            csv_files.append({
                'filename': specific_file,
                'filepath': filepath,
                'rows': len(df),
                'columns': list(df.columns)
            })
        else:
            raise FileNotFoundError(f"Specified CSV file not found: {filepath}")
    else:
        raise ValueError(f"Invalid filename: {specific_file}. Must end with .csv")
            
    context['task_instance'].xcom_push(key='csv_files', value=csv_files)
    return f"Found {len(csv_files)} CSV files"

def validate_csv_structure(**context):
    """Validate CSV files have required columns"""
    csv_files = context['task_instance'].xcom_pull(task_ids='read_csv_files', key='csv_files')
    valid_files = []
    
    for file_info in csv_files:
        df = pd.read_csv(file_info['filepath'])
        
        # Check for URL column (adjust based on your CSV structure)
        has_url_column = any('url' in col.lower() for col in df.columns)
        
        if has_url_column:
            valid_files.append(file_info['filepath'])
            print(f"✓ Valid: {file_info['filename']}")
        else:
            print(f"✗ Invalid: {file_info['filename']} - missing URL column")
    
    context['task_instance'].xcom_push(key='valid_files', value=valid_files)
    return f"Validated {len(valid_files)} files"

def extract_urls(**context):
    """Extract all URLs from valid CSV files"""
    valid_files = context['task_instance'].xcom_pull(task_ids='validate_csv', key='valid_files')
    all_urls = []
    
    for filepath in valid_files:
        df = pd.read_csv(filepath)
        
        # Find URL column
        url_col = next((col for col in df.columns if 'url' in col.lower()), None)
        
        if url_col:
            urls = df[url_col].dropna().tolist()
            all_urls.extend(urls)
            print(f"Extracted {len(urls)} URLs from {os.path.basename(filepath)}")
    
    # Remove duplicates
    unique_urls = list(set(all_urls))
    
    context['task_instance'].xcom_push(key='urls', value=unique_urls)
    return f"Extracted {len(unique_urls)} unique URLs"

def scrape_and_save_with_zyte(**context):
    """Scrape URLs using Zyte API and save HTML files immediately"""
    urls = context['task_instance'].xcom_pull(task_ids='extract_urls', key='urls')
    
    # Get Zyte API key from environment variable
    api_key = os.environ.get("ZYTE_API_KEY")
    if not api_key:
        raise ValueError("ZYTE_API_KEY not set in environment variables")
    
    # Zyte API endpoint
    api_url = "https://api.zyte.com/v1/extract"
    
    # Setup output directory - maps to /Users/devin/repos/projects/data-pipelines/boxing/data/output/html
    output_dir = '/opt/airflow/data/output/html'
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    failed_urls = []
    
    for url in urls:
        print(f"Scraping: {url}")
        
        # Zyte API request payload
        payload = {
            "url": url,
            "httpResponseBody": True,
            "httpResponseHeaders": True,
            "browserHtml": True,  # Get JavaScript-rendered HTML
        }
        
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                html_content = data.get('browserHtml', data.get('httpResponseBody'))
                
                # Save HTML immediately
                url_parts = url.rstrip('/').split('/')
                filename = f"{url_parts[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                saved_files.append({
                    'url': url,
                    'filepath': filepath,
                    'filename': filename,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✓ Successfully scraped and saved: {url} -> {filename}")
            else:
                failed_urls.append({
                    'url': url,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✗ Failed to scrape: {url} - Status: {response.status_code}")
                
        except Exception as e:
            failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            print(f"✗ Error scraping {url}: {str(e)}")
        
        # Rate limiting - adjust based on your Zyte plan
        time.sleep(1)
    
    # Push only metadata to XCom (not the HTML content)
    context['task_instance'].xcom_push(key='saved_files', value=saved_files)
    context['task_instance'].xcom_push(key='failed_urls', value=failed_urls)
    
    return f"Scraped and saved {len(saved_files)} HTML files, {len(failed_urls)} failed"


def report_results(**context):
    """Generate scraping report"""
    saved_files = context['task_instance'].xcom_pull(task_ids='scrape_and_save', key='saved_files')
    failed_urls = context['task_instance'].xcom_pull(task_ids='scrape_and_save', key='failed_urls')
    
    print("\n" + "="*50)
    print("SCRAPING REPORT")
    print("="*50)
    print(f"Total URLs processed: {len(saved_files) + len(failed_urls)}")
    print(f"Successfully scraped and saved: {len(saved_files)}")
    print(f"Failed: {len(failed_urls)}")
    print(f"HTML files saved: {len(saved_files)}")
    
    if failed_urls:
        print("\nFailed URLs:")
        for fail in failed_urls:
            print(f"  - {fail['url']}: {fail['error']}")
    
    return "Report generated"

# Define tasks
read_csv_task = PythonOperator(
    task_id='read_csv_files',
    python_callable=read_csv_files,
    dag=dag,
)

validate_csv_task = PythonOperator(
    task_id='validate_csv',
    python_callable=validate_csv_structure,
    dag=dag,
)

extract_urls_task = PythonOperator(
    task_id='extract_urls',
    python_callable=extract_urls,
    dag=dag,
)

scrape_and_save_task = PythonOperator(
    task_id='scrape_and_save',
    python_callable=scrape_and_save_with_zyte,
    dag=dag,
)

report_task = PythonOperator(
    task_id='report_results',
    python_callable=report_results,
    dag=dag,
)

# Define dependencies - complete pipeline
read_csv_task >> validate_csv_task >> extract_urls_task >> scrape_and_save_task >> report_task