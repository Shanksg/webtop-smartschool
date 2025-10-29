#!/usr/bin/env python3
"""
Test if we can login with curl/requests without captcha
"""

import requests
import json
import yaml
from pathlib import Path

def test_curl_login():
    """Test login with requests (like curl)"""

    print("=" * 60)
    print("Testing Login with curl/requests (no browser)")
    print("=" * 60)

    # Load credentials
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    student = config['students'][0]
    username = student['username']
    password = student['password']

    print(f"\nUsername: {username}")
    print("=" * 60)

    session = requests.Session()
    session.verify = False

    login_url = "https://webtopserver.smartschool.co.il/server/api/user/LoginByUserNameAndPassword"

    # Test 1: Try without captcha
    print("\nTest 1: Trying login WITHOUT captcha token...")
    print("-" * 60)

    payload = {
        "UserName": username,
        "Password": password,
        "RememberMe": False
    }

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://webtop.smartschool.co.il',
        'Referer': 'https://webtop.smartschool.co.il/'
    }

    try:
        response = session.post(login_url, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == True:
                print("\n✓ SUCCESS! Login worked WITHOUT captcha!")
                print("   We can use curl for automation!")

                # Extract token
                token = data.get('data', {}).get('token')
                if token:
                    print(f"\n✓ Got token: {token[:50]}...")
                    return True
            else:
                print(f"\n✗ Login failed: {data.get('message') or data.get('errorDescription')}")
        else:
            print(f"\n✗ HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"\n✗ Request failed: {e}")

    # Test 2: Try with empty captcha
    print("\n\nTest 2: Trying with EMPTY captcha field...")
    print("-" * 60)

    payload = {
        "UserName": username,
        "Password": password,
        "RememberMe": False,
        "captcha": "",
        "Data": "",
        "UniqueId": "",
        "BiometricLogin": ""
    }

    try:
        response = session.post(login_url, json=payload, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == True:
                print("\n✓ SUCCESS! Login worked with empty captcha!")
                token = data.get('data', {}).get('token')
                if token:
                    print(f"\n✓ Got token: {token[:50]}...")
                    return True
            else:
                error = data.get('message') or data.get('errorDescription')
                print(f"\n✗ Login failed: {error}")

                if 'captcha' in str(error).lower() or 'recaptcha' in str(error).lower():
                    print("\n❌ CAPTCHA IS REQUIRED - Cannot use curl for automation")
                    print("   Must use browser automation or manual token extraction")
                    return False

    except Exception as e:
        print(f"\n✗ Request failed: {e}")

    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("❌ Cannot login with curl - reCAPTCHA is mandatory")
    print("✅ Use: python auto_login_token.py (browser automation)")
    print("   OR")
    print("✅ Use: python extract_token_from_browser.py (read from Chrome)")
    print("=" * 60)

    return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    test_curl_login()
