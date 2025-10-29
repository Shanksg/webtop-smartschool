#!/usr/bin/env python3
"""
SmartSchool Monitor - Testing Script
Tests individual components to help diagnose issues
"""

import sys
import os
import json
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("=" * 50)
    print("Testing Package Imports...")
    print("=" * 50)
    
    packages = {
        'requests': 'HTTP requests library',
        'schedule': 'Task scheduling',
        'yaml': 'YAML config files',
        'loguru': 'Logging',
        'apprise': 'Notifications',
    }
    
    failed = []
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - {description}")
        except ImportError as e:
            print(f"✗ {package:15} - FAILED: {e}")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages available\n")
    return True


def test_config_file():
    """Test if config file exists and is valid"""
    print("=" * 50)
    print("Testing Configuration File...")
    print("=" * 50)
    
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        print("  Create it with: mkdir -p config && cat > config/config.yaml << EOF")
        print("  students:")
        print("    - name: 'Student Name'")
        print("      username: 'username'")
        print("      password: 'password'")
        print("  EOF")
        return False
    
    print(f"✓ Config file exists: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or 'students' not in config:
            print("✗ Config file is invalid - missing 'students' key")
            return False
        
        students = config['students']
        if not students:
            print("✗ No students configured")
            return False
        
        print(f"✓ Found {len(students)} student(s)")
        for student in students:
            name = student.get('name', 'Unknown')
            username = student.get('username', 'Not set')
            has_password = 'password' in student and student['password']
            status = '✓' if has_password else '✗'
            print(f"  {status} {name}: {username}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return False


def test_smartschool_api():
    """Test SmartSchool API connection"""
    print("\n" + "=" * 50)
    print("Testing SmartSchool API Connection...")
    print("=" * 50)
    
    import yaml
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Load credentials
    try:
        with open("config/config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        students = config.get('students', [])
        
        if not students:
            print("✗ No students in config")
            return False
        
        student = students[0]
        username = student.get('username')
        password = student.get('password')
        name = student.get('name', 'Student')
        
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False
    
    # Create session
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.verify = False
    
    print(f"Testing with student: {name}")
    
    # Test login
    try:
        print("  Attempting login...")
        login_url = "https://webtop.smartschool.co.il/account/login"
        login_data = {'username': username, 'password': password}
        
        response = session.post(login_url, data=login_data, timeout=10)
        response.raise_for_status()
        
        cookies = session.cookies.get_dict()
        if 'webToken' in cookies:
            print("  ✓ Login successful, got webToken")
        else:
            print("  ⚠ Login response received but webToken not in cookies")
            print(f"    Available cookies: {list(cookies.keys())}")
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Login failed: {e}")
        return False
    
    # Test API call
    try:
        print("  Attempting to fetch homework...")
        api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"
        
        # Try with credentials in session
        response = session.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("  ✓ API call successful")
        print(f"    Response type: {type(data).__name__}")
        if isinstance(data, dict):
            print(f"    Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"    Items: {len(data)}")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API call failed: {e}")
        return False


def test_notifiers():
    """Test notification configuration"""
    print("\n" + "=" * 50)
    print("Testing Notification Configuration...")
    print("=" * 50)
    
    notifiers_str = os.getenv('NOTIFIERS', '')
    
    if not notifiers_str:
        print("⚠ No NOTIFIERS environment variable set")
        print("  Set with: export NOTIFIERS='hassio://user@host/token'")
        return False
    
    print(f"Notifiers configured: {len(notifiers_str.split(','))} service(s)")
    
    try:
        import apprise
        apobj = apprise.Apprise()
        
        for notifier in notifiers_str.split(','):
            notifier = notifier.strip()
            if notifier:
                if apobj.add(notifier):
                    print(f"  ✓ {notifier}")
                else:
                    print(f"  ✗ {notifier} - Invalid format")
        
        return len(apobj) > 0
    
    except Exception as e:
        print(f"✗ Error setting up notifiers: {e}")
        return False


def test_storage():
    """Test if storage directories are writable"""
    print("\n" + "=" * 50)
    print("Testing Storage Directories...")
    print("=" * 50)
    
    dirs = {
        'config': 'Configuration files',
        'logs': 'Log files',
    }
    
    all_ok = True
    for dirname, description in dirs.items():
        dirpath = Path(dirname)
        
        # Create if doesn't exist
        dirpath.mkdir(exist_ok=True)
        
        # Test write
        test_file = dirpath / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
            print(f"✓ {dirname:15} - {description} (writable)")
        except Exception as e:
            print(f"✗ {dirname:15} - FAILED: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests"""
    print("\n" + "🔍 SmartSchool Monitor - Test Suite" + "\n")
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration File", test_config_file),
        ("SmartSchool API", test_smartschool_api),
        ("Notifiers", test_notifiers),
        ("Storage", test_storage),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {name}")
    
    print("\n" + "-" * 50)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Ready to run.")
        return 0
    else:
        print("✗ Some tests failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
