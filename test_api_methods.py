#!/usr/bin/env python3
"""
Test different methods to call the homework API
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = """W/T/KaL70Rj8h9Lt7WZn4hTdj2/259fCZ2/U0BZk/1nzshfdWxbRU9r0znBxGzNBJku3u/ithtixDrAQs4H75DDB0IcxUT3E1/Vf6HM83M3IwYGpz8+3NMBlcE6xgFYrlhhYE1FRtOIuy9Odlo2juB/aHQv38VFz6opdM0HyXdAewW3HZPaOQh3+husi5Wd6Dvi+kOnR83ebhGPIM5CT9IPxvjfBfC+GTUlj2RuQlN+cECxc1kbU5KX9kGrqezhi9T1Zucg+YHhn8CpVnRuFs7JbCc9Ab0vaD3a1ymd7S42Xgp0nNMjpZep6ZlLBoIqCCkITWzQJDck7gwiKZYlmIlusYOAg3T61Lpo1XfYtTsanq8MJ1ymhshnJJNILjsefolyTWXkwNQfKYlZxg/UI0+TQ4u5+n87pqMystrotekeM+7GKIDZ4t7oh6FMHgEzVmFQXfOpZv1v5i/FeGLjyXaiwnDObgcOtQtMZ+KjozjAza/4AZ4X/gArcISk+oxXR4XTv21O0IfsS6lR54s8bns947xXL1mBTvZ1kBH0Rqdk6aVpmHYPIk14A7b+HU9GeruZqK4O4foxTCq8sOhmlixVCgE/DBqpOdE4VTwGHkscNDe4Zueb5WEDJia2U5Lbg00EG3Z91DzTXOC+FS7LYcsy5tVUnYbcx9TsRc7aa/aOnL1Sce01XRS7f7otxv2ohfBQVex2RN8ASWbvFjCHRj9pEtm1Ldw8Sf6Tm/HrLCsiMW5h7Uqf/nCdYu587sP1lu/iMFDHLfu2X0yTCeZNngRhGJZJb7eA6k18M+z9TUMMMnFUcbQ1ZZ4tzZfKP3Z1EQvYpU2Gvzpdim3a0fUOLm/TnllNM2jj++5TaoPQ0dJfm8CFEt1JjnmaSUf/ETeoD1MOsI+X5REjatumGKU4lQ8kBrP+pqOQyaOYuGTSI23927HbMCDxZg8+Y9LTK8C8XFJi/5M8WRXkk5lRHQ1hC9WiQ+WfLH6/ky7iRnKCbG9RNM7F3Ie8lfQ36ud4MU539cJ/xBpNRD+YeX9CX7Z/6E6oCJRweWL7XMrRGU+/4rrZf3HH+rl8YBIgWcpfMbsW9ocB/5uFQlAEr275k5phzjkDAU5M06CMhrn4Qnp7qDPkRg0I/fQQNWxlPR8AD44ArjvxfbXxQPKH0EADuqlypB9ClVAX6cKzg1nEAUDYlF3jOw2eC6lq2DnKxYNaybRtVF0OvR3T08pkB4Kh6srIpnvknrLt9ziC9Yzv71lROs2FUzWDzSCiqi3f5oYavXqH2KqvcfPl60Ky+U0pCgZTdFnum+argt59x3zpJAsEpSNA="""

token = TOKEN.strip()
api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

session = requests.Session()
session.verify = False

print("Testing SmartSchool Homework API - Multiple Methods")
print("=" * 60)

methods = [
    {
        "name": "POST with webToken in JSON body",
        "method": "POST",
        "json": {"webToken": token}
    },
    {
        "name": "POST with webToken in form data",
        "method": "POST",
        "data": {"webToken": token}
    },
    {
        "name": "POST with webToken as query param",
        "method": "POST",
        "params": {"webToken": token}
    },
    {
        "name": "GET with Authorization header",
        "method": "GET",
        "headers": {"Authorization": f"Bearer {token}"}
    },
    {
        "name": "POST with Authorization header",
        "method": "POST",
        "headers": {"Authorization": f"Bearer {token}"}
    },
    {
        "name": "GET with webToken cookie",
        "method": "GET",
        "cookies": {"webToken": token}
    },
    {
        "name": "POST with webToken cookie",
        "method": "POST",
        "cookies": {"webToken": token}
    },
    {
        "name": "POST empty body with webToken cookie",
        "method": "POST",
        "cookies": {"webToken": token},
        "json": {}
    },
]

for idx, test in enumerate(methods, 1):
    print(f"\n{idx}. {test['name']}")

    try:
        method = test.pop('method')
        name = test.pop('name')
        kwargs = {**test, 'timeout': 10}

        if method == "GET":
            response = session.get(api_url, **kwargs)
        else:
            response = session.post(api_url, **kwargs)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✓ SUCCESS!")
            try:
                data = response.json()
                print(f"   Response type: {type(data).__name__}")
                if isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())}")
                    print("\n   Full Response:")
                    print("   " + "=" * 56)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                elif isinstance(data, list):
                    print(f"   Items: {len(data)}")
                    if len(data) > 0:
                        print(f"\n   First item:")
                        print(json.dumps(data[0], indent=4, ensure_ascii=False))
                break  # Stop on first success
            except:
                print(f"   Response (not JSON): {response.text[:200]}")
        elif response.status_code in [400, 401, 403]:
            print(f"   ✗ Auth error: {response.text[:100]}")
        else:
            print(f"   ✗ Failed")

    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
