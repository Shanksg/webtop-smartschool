#!/usr/bin/env python3
"""
Test API with correct parameters from browser
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = """W/T/KaL70Rj8h9Lt7WZn4hTdj2/259fCZ2/U0BZk/1nzshfdWxbRU9r0znBxGzNBJku3u/ithtixDrAQs4H75DDB0IcxUT3E1/Vf6HM83M3IwYGpz8+3NMBlcE6xgFYrlhhYE1FRtOIuy9Odlo2juB/aHQv38VFz6opdM0HyXdAewW3HZPaOQh3+husi5Wd6Dvi+kOnR83ebhGPIM5CT9IPxvjfBfC+GTUlj2RuQlN+cECxc1kbU5KX9kGrqezhi9T1Zucg+YHhn8CpVnRuFs7JbCc9Ab0vaD3a1ymd7S42Xgp0nNMjpZep6ZlLBoIqCCkITWzQJDck7gwiKZYlmIlusYOAg3T61Lpo1XfYtTsanq8MJ1ymhshnJJNILjsefolyTWXkwNQfKYlZxg/UI0+TQ4u5+n87pqMystrotekeM+7GKIDZ4t7oh6FMHgEzVmFQXfOpZv1v5i/FeGLjyXaiwnDObgcOtQtMZ+KjozjAza/4AZ4X/gArcISk+oxXR4XTv21O0IfsS6lR54s8bns947xXL1mBTvZ1kBH0Rqdk6aVpmHYPIk14A7b+HU9GeruZqK4O4foxTCq8sOhmlixVCgE/DBqpOdE4VTwGHkscNDe4Zueb5WEDJia2U5Lbg00EG3Z91DzTXOC+FS7LYcsy5tVUnYbcx9TsRc7aa/aOnL1Sce01XRS7f7otxv2ohfBQVex2RN8ASWbvFjCHRj9pEtm1Ldw8Sf6Tm/HrLCsiMW5h7Uqf/nCdYu587sP1lu/iMFDHLfu2X0yTCeZNngRhGJZJb7eA6k18M+z9TUMMMnFUcbQ1ZZ4tzZfKP3Z1EQvYpU2Gvzpdim3a0fUOLm/TnllNM2jj++5TaoPQ0dJfm8CFEt1JjnmaSUf/ETeoD1MOsI+X5REjatumGKU4lQ8kBrP+pqOQyaOYuGTSI23927HbMCDxZg8+Y9LTK8C8XFJi/5M8WRXkk5lRHQ1hC9WiQ+WfLH6/ky7iRnKCbG9RNM7F3Ie8lfQ36ud4MU539cJ/xBpNRD+YeX9CX7Z/6E6oCJRweWL7XMrRGU+/4rrZf3HH+rl8YBIgWcpfMbsW9ocB/5uFQlAEr275k5phzjkDAU5M06CMhrn4Qnp7qDPkRg0I/fQQNWxlPR8AD44ArjvxfbXxQPKH0EADuqlypB9ClVAX6cKzg1nEAUDYlF3jOw2eC6lq2DnKxYNaybRtVF0OvR3T08pkB4Kh6srIpnvknrLt9ziC9Yzv71lROs2FUzWDzSCiqi3f5oYavXqH2KqvcfPl60Ky+U0pCgZTdFnum+argt59x3zpJAsEpSNA="""

token = TOKEN.strip()

# Parameters from browser
payload = {
    "classCode": 3,
    "moduleID": 11,
    "periodID": 7949,
    "periodName": "מחצית א`",
    "studentID": "YzWJS87TUHKsZ0cEJ9Ysy1/mXhcJ71TfAVeD2hyt2wg=",
    "studentName": "גופר מעוז יוחנן",
    "studyYear": 2026,
    "studyYearName": "תשפ״ו",
    "viewType": 0,
    "weekIndex": 0
}

api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

session = requests.Session()
session.verify = False

# Set cookies
session.cookies.set('webToken', token)
session.cookies.set('input', '0')

# Set headers like browser
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'language': 'he',
    'rememberme': '0',
    'origin': 'https://webtop.smartschool.co.il',
    'referer': 'https://webtop.smartschool.co.il/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
}

print("Testing SmartSchool Homework API with Browser Parameters")
print("=" * 60)
print(f"Endpoint: {api_url}")
print(f"Method: POST")
print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
print("=" * 60)

try:
    response = session.post(api_url, json=payload, headers=headers, timeout=10)
    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ SUCCESS!\n")
        data = response.json()

        print("Response:")
        print("=" * 60)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 60)

        # Check if successful
        if data.get('status') == True:
            print("\n✓ API returned success!")
            if data.get('data'):
                print(f"✓ Got homework data!")
        else:
            print(f"\n⚠ API returned status=false")
            print(f"   Error: {data.get('errorDescription')}")

    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
