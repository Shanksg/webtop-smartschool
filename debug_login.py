#!/usr/bin/env python3
"""
Debug script to test SmartSchool login process
"""

import requests
import yaml
from pathlib import Path
import json

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_login():
    """Debug the login process step by step"""

    # Load credentials
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    student = config['students'][0]
    username = student['username']
    password = student['password']
    name = student['name']

    print(f"Testing login for: {name}")
    print(f"Username: {username}")
    print("=" * 60)

    session = requests.Session()
    session.verify = False

    # Step 1: Try to get the login page
    print("\n1. Fetching login page...")
    login_url = "https://webtop.smartschool.co.il/account/login"

    try:
        response = session.get(login_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies received: {list(session.cookies.keys())}")
        print(f"   Response length: {len(response.text)} bytes")

        # Check for CSRF token in HTML
        if 'csrf' in response.text.lower() or 'token' in response.text.lower():
            print("   ⚠️  Page might contain CSRF token requirement")

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # Step 2: Try POST login
    print("\n2. Attempting login POST...")

    login_data = {
        'username': username,
        'password': password
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': login_url
    }

    try:
        response = session.post(login_url, data=login_data, headers=headers, timeout=10, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies after login: {list(session.cookies.keys())}")

        if response.status_code == 302:
            print(f"   Redirect to: {response.headers.get('Location')}")

        if 'webToken' in session.cookies:
            print(f"   ✓ webToken found: {session.cookies['webToken'][:20]}...")
        else:
            print(f"   ✗ No webToken in cookies")
            print(f"   Response headers: {dict(response.headers)}")
            if len(response.text) < 1000:
                print(f"   Response body: {response.text}")

    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return

    # Step 3: Try API endpoint
    print("\n3. Testing API endpoint...")
    api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

    cookies_dict = session.cookies.get_dict()
    print(f"   Using cookies: {list(cookies_dict.keys())}")

    # Try with webToken in params
    if 'webToken' in cookies_dict:
        params = {'webToken': cookies_dict['webToken']}
        try:
            response = session.get(api_url, params=params, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ API call successful!")
                print(f"   Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"   Items: {len(data)}")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
    else:
        print("   ⚠️  Skipping - no webToken available")

    print("\n" + "=" * 60)
    print("Debug complete!")

if __name__ == "__main__":
    debug_login()
