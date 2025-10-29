#!/usr/bin/env python3
"""
Inspect the login form to see what fields are expected
"""

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def inspect_form():
    """Inspect the login form"""

    login_url = "https://webtop.smartschool.co.il/account/login"

    session = requests.Session()
    session.verify = False

    print("Fetching login page...")
    response = session.get(login_url, timeout=10)

    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        return

    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)} bytes")

    # Parse HTML
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all forms
        forms = soup.find_all('form')
        print(f"\nFound {len(forms)} form(s)\n")

        for idx, form in enumerate(forms):
            print(f"Form {idx + 1}:")
            print(f"  Action: {form.get('action')}")
            print(f"  Method: {form.get('method')}")

            # Find all input fields
            inputs = form.find_all('input')
            print(f"  Input fields ({len(inputs)}):")
            for inp in inputs:
                name = inp.get('name', 'N/A')
                input_type = inp.get('type', 'text')
                value = inp.get('value', '')
                print(f"    - {name} (type={input_type}) value='{value}'")

            print()

    except ImportError:
        print("\nBeautifulSoup not installed. Showing raw HTML snippets instead:\n")

        # Look for form tag
        if '<form' in response.text:
            import re
            forms = re.findall(r'<form[^>]*>.*?</form>', response.text, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(forms)} form(s)")

            for idx, form_html in enumerate(forms[:2]):  # Show first 2 forms
                print(f"\nForm {idx + 1} HTML (truncated):")
                print(form_html[:500])
                print("...")

        # Look for input fields
        inputs = re.findall(r'<input[^>]+>', response.text, re.IGNORECASE)
        print(f"\nFound {len(inputs)} input fields:")
        for inp in inputs[:10]:  # Show first 10
            print(f"  {inp}")

if __name__ == "__main__":
    inspect_form()
