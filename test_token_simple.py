#!/usr/bin/env python3
"""
Test API with token (handles URL-encoded tokens)
"""

import requests
import json
import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Your token (URL-encoded is fine, we'll decode it)
TOKEN = "W%2FT%2FKaL70Rj8h9Lt7WZn4hTdj2%2F259fCZ2%2FU0BZk%2F1nzshfdWxbRU9r0znBxGzNBJku3u%2FithtixDrAQs4H75DDB0IcxUT3E1%2FVf6HM83M3IwYGpz8%2B3NMBlcE6xgFYrlhhYE1FRtOIuy9Odlo2juB%2FaHQv38VFz6opdM0HyXdAewW3HZPaOQh3%2Bhusi5Wd6Dvi%2BkOnR83ebhGPIM5CT9IPxvjfBfC%2BGTUlj2RuQlN%2BcECxc1kbU5KX9kGrqezhi9T1Zucg%2BYHhn8CpVnRuFs7JbCc9Ab0vaD3a1ymd7S42Xgp0nNMjpZep6ZlLBoIqCCkITWzQJDck7gwiKZYlmIlusYOAg3T61Lpo1XfYtTsanq8MJ1ymhshnJJNILjsefolyTWXkwNQfKYlZxg%2FUI0%2BTQ4u5%2Bn87pqMystrotekeM%2B7GKIDZ4t7oh6FMHgEzVmFQXfOpZv1v5i%2FFeGLjyXaiwnDObgcOtQtMZ%2BKjozjAza%2F4AZ4X%2FgArcISk%2BoxXR4XTv21O0IfsS6lR54s8bns947xXL1mBTvZ1kBH0Rqdk6aVpmHYPIk14A7b%2BHU9GeruZqK4O4foxTCq8sOhmlixVCgE%2FDBqpOdE4VTwGHkscNDe4Zueb5WEDJia2U5Lbg00EG3Z91DzTXOC%2BFS7LYcsy5tVUnYbcx9TsRc7aa%2FaOnL1Sce01XRS7f7otxv2ohfBQVex2RN8ASWbvFjCHRj9pEtm1Ldw8Sf6Tm%2FHrLCsiMW5h7Uqf%2FnCdYu587sP1lu%2FiMFDHLfu2X0yTCeZNngRhGJZJb7eA6k18M%2Bz9TUMMMnFUcbQ1ZZ4tzZfKP3Z1EQvYpU2Gvzpdim3a0fUOLm%2FTnllNM2jj%2B%2B5TaoPQ0dJfm8CFEt1JjnmaSUf%2FETeoD1MOsI%2BX5REjatumGKU4lQ8kBrP%2BpqOQyaOYuGTSI23927HbMCDxZg8%2BY9LTK8C8XFJi%2F5M8WRXkk5lRHQ1hC9WiQ%2BWfLH6%2Fky7iRnKCbG9RNM7F3Ie8lfQ36ud4MU539cJ%2FxBpNRD%2BYeX9CX7Z%2F6E6oCJRweWL7XMrRGU%2B%2F4rrZf3HH%2Brl8YBIgWcpfMbsW9ocB%2F5uFQlAEr275k5phzjkDAU5M06CMhrn4Qnp7qDPkRg0I%2FfQQNWxlPR8AD44ArjvxfbXxQPKH0EADuqlypB9ClVAX6cKzg1nEAUDYlF3jOw2eC6lq2DnKxYNaybRtVF0OvR3T08pkB4Kh6srIpnvknrLt9ziC9Yzv71lROs2FUzWDzSCiqi3f5oYavXqH2KqvcfPl60Ky%2BU0pCgZTdFnum%2Bargt59x3zpJAsEpSNA%3D"

# Decode if URL-encoded
token = urllib.parse.unquote(TOKEN)
print(f"Decoded token (first 50 chars): {token[:50]}...")

session = requests.Session()
session.verify = False

api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

print("\n" + "=" * 60)
print("Testing SmartSchool Homework API")
print("=" * 60)

# Method 1: Query parameter
print("\n1. Testing with webToken as query parameter...")
try:
    response = session.get(api_url, params={'webToken': token}, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ SUCCESS!")
        print(f"   Response type: {type(data)}")

        if isinstance(data, dict):
            print(f"   Response keys: {list(data.keys())}")
            print(f"\n   Full response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif isinstance(data, list):
            print(f"   Number of items: {len(data)}")
            if len(data) > 0:
                print(f"\n   First item:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
    else:
        print(f"   ✗ Failed")
        print(f"   Response: {response.text[:200]}")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Method 2: Cookie
print("\n2. Testing with webToken as cookie...")
try:
    session.cookies.set('webToken', token)
    response = session.get(api_url, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ SUCCESS!")
        print(f"   Response type: {type(data)}")
    else:
        print(f"   ✗ Failed")

except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
