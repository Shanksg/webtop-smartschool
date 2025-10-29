#!/usr/bin/env python3
"""
Test API with an existing token from browser
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api_with_token():
    """Test the homework API with a token"""

    print("=" * 60)
    print("Testing SmartSchool API with existing token")
    print("=" * 60)

    # Get token from user
    print("\nTo get your token:")
    print("1. Open SmartSchool in browser and login")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application tab → Cookies")
    print("4. Find 'webToken' cookie and copy its value")
    print("\nOR after login, in Network tab, look at the response")
    print("from 'LoginByUserNameAndPassword' and copy the 'token' field")
    print("=" * 60)

    token = input("\nPaste your token here: ").strip()

    if not token:
        print("No token provided!")
        return

    session = requests.Session()
    session.verify = False

    # Test the homework API
    api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

    print(f"\nTesting API: {api_url}")

    # Try as query parameter
    print("\n1. Trying with token as query parameter...")
    try:
        response = session.get(api_url, params={'webToken': token}, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success!")
            print(f"   Response type: {type(data)}")

            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())}")
                # Pretty print first few items
                print(f"\n   Data preview:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            elif isinstance(data, list):
                print(f"   Items: {len(data)}")
                if len(data) > 0:
                    print(f"\n   First item preview:")
                    print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])

            return True
        else:
            print(f"   ✗ Failed: {response.text[:200]}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Try as header
    print("\n2. Trying with token in Authorization header...")
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = session.get(api_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success!")
            print(f"   Response type: {type(data)}")
            return True
        else:
            print(f"   ✗ Failed")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Try as cookie
    print("\n3. Trying with token as cookie...")
    try:
        session.cookies.set('webToken', token)
        response = session.get(api_url, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Success!")
            print(f"   Response type: {type(data)}")
            return True
        else:
            print(f"   ✗ Failed")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    return False

if __name__ == "__main__":
    test_api_with_token()
