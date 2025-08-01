#!/usr/bin/env python3
"""
Quick debug test for the Zyte API key and basic functionality
"""

import os
from pathlib import Path

# Load environment variables from .env file if it exists
def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# Configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')

print(f"🔑 ZYTE_API_KEY exists: {ZYTE_API_KEY is not None}")
if ZYTE_API_KEY:
    print(f"🔑 API key length: {len(ZYTE_API_KEY)} characters")
    print(f"🔑 API key starts with: {ZYTE_API_KEY[:10]}...")
else:
    print("❌ No ZYTE_API_KEY found!")

# Test a simple request
try:
    import requests
    test_url = "https://boxrec.com/en/box-pro/447121"
    
    print(f"\n🌐 Testing API request to: {test_url}")
    response = requests.post(
        "https://api.zyte.com/v1/extract",
        json={
            "url": test_url,
            "httpResponseBody": True,
            "httpResponseHeaders": True
        },
        auth=(ZYTE_API_KEY, ""),
        timeout=30
    )
    
    print(f"📊 Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API request successful!")
        print(f"📄 Response keys: {list(data.keys())}")
    else:
        print(f"❌ API request failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error testing API: {e}")
