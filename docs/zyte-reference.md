

# How we typically use zyte

```

# Load the .env file from the root directory
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
if not ZYTE_API_KEY:
    logging.error("ZYTE_API_KEY environment variable not set.")
    exit(1)

PROXY = {
    "http": f"http://{ZYTE_API_KEY}:@api.zyte.com:8011/",
    "https": f"http://{ZYTE_API_KEY}:@api.zyte.com:8011/",
}
VERIFY = '../zyte-ca.crt'

# Determine the directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, 'input.txt')
OUTPUT_CSV_FILE = os.path.join(BASE_DIR, 'output.csv')
OUTPUT_JSON_FILE = os.path.join(BASE_DIR, 'output.json')

lock = threading.Lock()
results = []

```



# another example

```
import csv
import requests
import concurrent.futures
import os
from urllib.parse import urlparse, unquote
from threading import Lock
import re
from tqdm import tqdm
from base64 import b64decode

# === CONFIG ===
csv_file = 'urls.csv'
txt_dir   = 'txt'
ZYTE_API_KEY = 'f97a308b4e2a432ea695905e697d9738'

# === THREAD LOCKS ===
dir_lock      = Lock()
progress_lock = Lock()

def url_path_to_filepath(url):
    """
    Convert a URL into a local filepath under txt_dir.
    E.g. "https://.../dotnet/ai-samples/llms.txt?foo" -> "txt/dotnet/ai-samples/llms.txt"
    """
    parsed = urlparse(url)
    # decode %-escapes, strip leading slash
    raw_path = unquote(parsed.path.lstrip('/'))
    
    # if there's no filename, default to index.txt
    if not raw_path or raw_path.endswith('/'):
        raw_path = os.path.join(raw_path, 'index.txt')
    
    # ensure .txt extension
    base, ext = os.path.splitext(raw_path)
    if ext.lower() != '.txt':
        raw_path = base + '.txt'
    
    # sanitize each path segment
    segments = []
    for seg in raw_path.split(os.sep):
        clean = re.sub(r'[<>:"/\\|?*]', '_', seg)
        if clean:
            segments.append(clean)
    
    # assemble full local filepath
    return os.path.join(txt_dir, *segments)

def download_to_file(index, row, pbar):
    url = row.get('url', '').strip()
    if not url:
        with progress_lock:
            pbar.update(1)
        return index, False, "Empty URL"

    try:
        local_path = url_path_to_filepath(url)
        local_dir  = os.path.dirname(local_path)
        
        # create subdirectories if needed
        with dir_lock:
            os.makedirs(local_dir, exist_ok=True)
        
        # fetch via Zyte
        resp = requests.post(
            "https://api.zyte.com/v1/extract",
            auth=(ZYTE_API_KEY, ""),
            json={"url": url, "httpResponseBody": True},
            timeout=60
        )
        
        if resp.status_code != 200:
            err = f"HTTP {resp.status_code}"
            with progress_lock:
                pbar.update(1)
                pbar.set_postfix_str(f"Failed: {err}")
            return index, False, err
        
        # decode and write
        body = b64decode(resp.json()["httpResponseBody"])
        with open(local_path, 'wb') as f:
            f.write(body)
        
        # update progress
        with progress_lock:
            pbar.update(1)
            pbar.set_postfix_str(f"Saved: {os.path.relpath(local_path, txt_dir)} ({len(body)} bytes)")
        return index, True, f"{len(body)} bytes"
    
    except Exception as e:
        with progress_lock:
            pbar.update(1)
            pbar.set_postfix_str(f"Error: {str(e)[:30]}...")
        return index, False, str(e)

def process_csv():
    # read URLs
    try:
        with open(csv_file, newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        if not rows or 'url' not in rows[0]:
            print(f"CSV must have a 'url' column")
            return
        print(f"Loaded {len(rows)} URLs")
    except Exception as e:
        print(f"Failed to read CSV: {e}")
        return

    # ensure base txt_dir exists
    os.makedirs(txt_dir, exist_ok=True)
    print(f"Outputs → {os.path.abspath(txt_dir)}\n")

    # concurrent download
    total = len(rows)
    success = fail = 0
    max_workers = 20

    with tqdm(total=total, desc="Downloading", unit="file") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(download_to_file, i, row, pbar)
                for i, row in enumerate(rows)
            ]
            for fut in concurrent.futures.as_completed(futures):
                _, ok, _ = fut.result()
                if ok: success += 1
                else:   fail += 1

    print(f"\nDone: {total} URLs → {success} succeeded, {fail} failed")

if __name__ == "__main__":
    process_csv()

```