import os
import json
import requests
import schedule
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
import apprise
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import unquote

# Configure logging
log_dir = Path("/app/logs") if Path("/app").exists() else Path("./logs")
log_dir.mkdir(exist_ok=True)
logger.add(f"{log_dir}/smartschool-monitor.log", rotation="500 MB", retention="7 days")

class SmartSchoolMonitor:
    def __init__(self):
        self.config_path = Path("/app/config/config.yaml") if Path("/app/config").exists() else Path("./config/config.yaml")
        self.state_file = Path("/app/config/homework_state.json") if Path("/app/config").exists() else Path("./config/homework_state.json")
        self.token_file = Path("/app/config/token_cache.json") if Path("/app/config").exists() else Path("./config/token_cache.json")
        self.students = []
        self.notifiers = []
        self.load_config()
        self.setup_notifiers()
        self.load_state()

    def load_config(self):
        """Load configuration from YAML file"""
        try:
            import yaml
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self.students = config.get('students', [])
            logger.info(f"Loaded {len(self.students)} students from config")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def setup_notifiers(self):
        """Setup Apprise notifiers from environment variable"""
        notifiers_str = os.getenv('NOTIFIERS', '')
        if not notifiers_str:
            logger.warning("No NOTIFIERS environment variable set")
            return

        self.apobj = apprise.Apprise()
        for notifier in notifiers_str.split(','):
            notifier = notifier.strip()
            if notifier:
                if self.apobj.add(notifier):
                    logger.info(f"Added notifier: {notifier}")
                else:
                    logger.error(f"Failed to add notifier: {notifier}")

    def load_state(self):
        """Load previous homework state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.homework_state = json.load(f)
                logger.info("Loaded previous homework state")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.homework_state = {}
        else:
            self.homework_state = {}

    def save_state(self):
        """Save homework state to file"""
        try:
            self.state_file.parent.mkdir(exist_ok=True, parents=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.homework_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_token_cache(self, username):
        """Load cached token for a user"""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, 'r') as f:
                cache = json.load(f)

            user_cache = cache.get(username)
            if not user_cache:
                return None

            # Check if token is expired (tokens usually last 24 hours)
            cached_time = datetime.fromisoformat(user_cache['timestamp'])
            if (datetime.now() - cached_time).total_seconds() > 23 * 3600:  # 23 hours
                logger.info(f"Cached token for {username} is expired (time-based)")
                return None

            # URL-decode the token if it's encoded
            token = user_cache.get('token', '')
            if token and '%' in token:
                user_cache['token'] = unquote(token)
                logger.debug("Decoded URL-encoded token from cache")

            logger.info(f"Using cached token for {username}")
            return user_cache

        except Exception as e:
            logger.error(f"Failed to load token cache: {e}")
            return None

    def validate_token(self, token, student_params):
        """Test if token is still valid by making API call"""
        try:
            logger.info("Validating token...")
            homework_data = self.get_homework(token, student_params)

            if homework_data is not None:
                logger.info("✓ Token is valid")
                return True
            else:
                logger.warning("✗ Token is invalid or expired")
                return False

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    def save_token_cache(self, username, token, student_params):
        """Save token to cache"""
        try:
            cache = {}
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    cache = json.load(f)

            cache[username] = {
                'token': token,
                'student_params': student_params,
                'timestamp': datetime.now().isoformat()
            }

            self.token_file.parent.mkdir(exist_ok=True, parents=True)
            with open(self.token_file, 'w') as f:
                json.dump(cache, f, indent=2)

            logger.info(f"Saved token cache for {username}")

        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")

    def login_with_selenium(self, username, password):
        """Fully automated login using undetected-chromedriver"""
        logger.info(f"Starting automated login for {username}")

        # Check if we're running in Docker (headless)
        is_docker = os.path.exists('/.dockerenv')
        headless = is_docker or os.getenv('HEADLESS', 'false').lower() == 'true'  # Changed default to false

        # Setup undetected Chrome
        options = uc.ChromeOptions()

        if headless:
            logger.info("Running in headless mode")
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
        else:
            logger.info("Running in non-headless mode (better for reCAPTCHA)")

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')

        # Additional options to help with reCAPTCHA
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')

        driver = None

        try:
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
            logger.info("Browser initialized")

            # Navigate to login
            login_url = "https://webtop.smartschool.co.il/account/login"
            driver.get(login_url)
            logger.info("Loaded login page")

            # Wait for page
            time.sleep(10)

            # Remove overlays with JavaScript
            js_cleanup = """
            document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="cookie"]').forEach(el => el.remove());
            document.body.style.overflow = 'auto';
            return 'cleaned';
            """
            driver.execute_script(js_cleanup)
            logger.info("Cleaned page overlays")

            # Find and fill username
            wait = WebDriverWait(driver, 20)
            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
            username_field.click()
            time.sleep(0.5)
            username_field.send_keys(username)
            logger.info("Entered username")
            time.sleep(1)

            # Find and fill password
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.click()
            time.sleep(0.5)
            password_field.send_keys(password)
            logger.info("Entered password")
            time.sleep(2)

            # Handle reCAPTCHA checkbox
            logger.info("Looking for reCAPTCHA checkbox...")
            try:
                # Wait for reCAPTCHA iframe to load
                time.sleep(3)

                # Switch to reCAPTCHA iframe
                recaptcha_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha']")))
                driver.switch_to.frame(recaptcha_iframe)
                logger.info("Switched to reCAPTCHA iframe")

                # Click the checkbox
                time.sleep(2)
                recaptcha_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".recaptcha-checkbox-border")))
                recaptcha_checkbox.click()
                logger.info("Clicked reCAPTCHA checkbox")

                # Switch back to main content
                driver.switch_to.default_content()
                logger.info("Switched back to main content")

                # Wait for reCAPTCHA to validate
                time.sleep(5)

            except Exception as e:
                logger.warning(f"Could not handle reCAPTCHA: {e}")
                # Switch back to main content in case we're stuck in iframe
                try:
                    driver.switch_to.default_content()
                except:
                    pass

            # Submit
            logger.info("Submitting form...")
            try:
                # Try to find and click the login button
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                logger.info("Clicked login button")
            except:
                # Fallback to pressing Enter
                password_field.send_keys(Keys.RETURN)
                logger.info("Submitted form via Enter key")

            # Wait for login (max 90 seconds - increased for reCAPTCHA)
            logger.info("Waiting for login to complete (this may take longer with reCAPTCHA)...")
            start_time = time.time()
            web_token = None
            login_successful = False

            while time.time() - start_time < 90:
                current_url = driver.current_url.lower()

                # Check if we've left the login page
                if 'login' not in current_url and 'webtop.smartschool.co.il' in current_url:
                    logger.info(f"Login successful - URL changed to: {driver.current_url}")
                    login_successful = True
                    break

                # Check for token in cookies during wait
                cookies = driver.get_cookies()
                for cookie in cookies:
                    if cookie['name'] == 'webToken' and cookie['value']:
                        web_token = cookie['value']
                        logger.info("Token found in cookies during wait")
                        login_successful = True
                        break

                if login_successful:
                    break

                time.sleep(2)

            if not login_successful:
                logger.error("Login did not complete within timeout period")
                logger.info(f"Final URL: {driver.current_url}")
                driver.save_screenshot("login_timeout.png")
                return None, None

            # Give the app time to set all cookies and tokens
            logger.info("Login successful, waiting for tokens to be set...")
            time.sleep(5)

            # Navigate to API server domain to get the token cookie
            try:
                logger.info("Navigating to API server to get token cookie...")
                driver.get("https://webtopserver.smartschool.co.il/")
                time.sleep(3)
            except Exception as e:
                logger.warning(f"Failed to navigate to API server: {e}")

            # Extract final token from API server domain
            time.sleep(2)

            # Debug: Print all cookies from API server
            cookies = driver.get_cookies()
            logger.info(f"All cookies found on API server: {[c['name'] for c in cookies]}")

            for cookie in cookies:
                logger.debug(f"Cookie: {cookie['name']} = {cookie['value'][:50] if len(cookie['value']) > 50 else cookie['value']}")
                if cookie['name'] == 'webToken':
                    web_token = cookie['value']
                    # URL-decode if needed
                    if web_token and '%' in web_token:
                        web_token = unquote(web_token)
                        logger.debug("Decoded URL-encoded token")
                    logger.info("✓ Found webToken on API server!")
                    break

            # If not in cookies, try localStorage and sessionStorage
            if not web_token:
                logger.info("Token not in cookies, checking localStorage...")
                try:
                    # Check all localStorage keys for tokens
                    all_storage = driver.execute_script("""
                        let items = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            let key = localStorage.key(i);
                            items[key] = localStorage.getItem(key);
                        }
                        return items;
                    """)
                    logger.info(f"localStorage keys: {list(all_storage.keys()) if all_storage else 'empty'}")

                    if all_storage:
                        for key, value in all_storage.items():
                            if 'token' in key.lower() or 'webtoken' in key.lower():
                                logger.info(f"Found potential token in localStorage[{key}]")
                                web_token = value
                                break
                except Exception as e:
                    logger.debug(f"localStorage check failed: {e}")

            if not web_token:
                logger.info("Token not in localStorage, checking sessionStorage...")
                try:
                    # Check all sessionStorage keys for tokens
                    all_session = driver.execute_script("""
                        let items = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            let key = sessionStorage.key(i);
                            items[key] = sessionStorage.getItem(key);
                        }
                        return items;
                    """)
                    logger.info(f"sessionStorage keys: {list(all_session.keys()) if all_session else 'empty'}")

                    if all_session:
                        for key, value in all_session.items():
                            if 'token' in key.lower() or 'webtoken' in key.lower():
                                logger.info(f"Found potential token in sessionStorage[{key}]")
                                web_token = value
                                break
                except Exception as e:
                    logger.debug(f"sessionStorage check failed: {e}")

            # Also check for other possible token names
            if not web_token:
                logger.info("Checking for alternative token names...")
                for alt_name in ['token', 'authToken', 'accessToken', 'jwt']:
                    for cookie in cookies:
                        if alt_name.lower() in cookie['name'].lower():
                            logger.info(f"Found potential token in cookie: {cookie['name']}")
                            web_token = cookie['value']
                            break
                    if web_token:
                        break

            if not web_token:
                logger.error("Failed to extract token from cookies, localStorage, or sessionStorage")
                logger.info("Saving screenshot and page source for debugging...")
                driver.save_screenshot("login_failed.png")
                with open("page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logger.info("Current URL: " + driver.current_url)
                return None, None

            logger.info(f"✓ Token extracted successfully")
            return web_token, None

        except Exception as e:
            logger.error(f"Login failed: {e}")
            import traceback
            traceback.print_exc()

            if driver:
                try:
                    driver.save_screenshot("error.png")
                except:
                    pass

            return None, None

        finally:
            if driver:
                driver.quit()
                logger.info("Browser closed")

    def get_homework(self, token, student_params):
        """
        Fetch homework from SmartSchool API

        Args:
            token: webToken from login
            student_params: dict with studentID, classCode, etc.
        """
        try:
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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            # POST with student parameters
            response = session.post(api_url, json=student_params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == True:
                logger.info(f"Successfully retrieved homework data")
                return data.get('data', [])
            else:
                error_desc = data.get('errorDescription', 'Unknown error')
                logger.error(f"API returned error: {error_desc}")
                return None

        except Exception as e:
            logger.error(f"Failed to get homework: {e}")
            return None

    def extract_homework_items(self, homework_data):
        """Extract actual homework from the schedule data"""
        homework_items = []

        if not homework_data:
            return homework_items

        for day in homework_data:
            date = day.get('date', '')
            hours_data = day.get('hoursData', [])

            for hour in hours_data:
                schedule = hour.get('scheduale', [])

                for item in schedule:
                    homework_text = item.get('homeWork') or ''
                    if homework_text:
                        homework_text = homework_text.strip()

                    if homework_text:  # Only include if there's actual homework
                        homework_items.append({
                            'date': date,
                            'subject': item.get('subject_name') or 'Unknown',
                            'teacher': item.get('teacher') or 'Unknown',
                            'homework': homework_text,
                            'description': item.get('descClass') or ''
                        })

        return homework_items

    def hash_homework(self, homework_item):
        """Create a hash of homework item to detect changes"""
        try:
            hw_str = json.dumps(homework_item, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(hw_str.encode()).hexdigest()
        except:
            return None

    def check_homework(self, student_name, username, password, student_params):
        """Check for new homework for a student"""
        try:
            token = None
            need_new_token = False

            # Try to use cached token first
            cached = self.load_token_cache(username)

            if cached:
                token = cached['token']
                if not student_params:
                    student_params = cached.get('student_params')

                # Validate token before using
                logger.info(f"Found cached token for {student_name}, validating...")
                if not self.validate_token(token, student_params):
                    logger.warning(f"Cached token for {student_name} is invalid, need new login")
                    need_new_token = True
                    token = None
            else:
                logger.info(f"No cached token for {student_name}")
                need_new_token = True

            # Get new token if needed
            if need_new_token:
                logger.info(f"Getting new token for {student_name}...")
                token, params_from_login = self.login_with_selenium(username, password)

                if not token:
                    logger.error(f"Failed to get token for {student_name}")
                    return

                if params_from_login:
                    student_params = params_from_login

                # Cache the new token
                self.save_token_cache(username, token, student_params)
                logger.info(f"✓ New token cached for {student_name}")

            if not student_params:
                logger.error(f"No student parameters available for {student_name}")
                logger.error("Please set student_params in config or login manually")
                return

            # Get homework
            homework_data = self.get_homework(token, student_params)

            if not homework_data:
                logger.warning(f"No homework data for {student_name}")
                return

            # Extract actual homework items
            homework_items = self.extract_homework_items(homework_data)
            logger.info(f"Found {len(homework_items)} homework items for {student_name}")

            # Initialize state for this student if needed
            if student_name not in self.homework_state:
                self.homework_state[student_name] = {}

            # Check for new homework
            new_homework = []
            current_hashes = {}

            for item in homework_items:
                item_hash = self.hash_homework(item)
                if not item_hash:
                    continue

                current_hashes[item_hash] = item

                # Check if this is new homework
                if item_hash not in self.homework_state[student_name]:
                    new_homework.append(item)
                    self.homework_state[student_name][item_hash] = {
                        'detected_at': datetime.now().isoformat(),
                        'item': item
                    }
                    logger.info(f"New homework detected: {item['subject']}")

            # Remove old homework from state
            self.homework_state[student_name] = {
                k: v for k, v in self.homework_state[student_name].items()
                if k in current_hashes
            }

            # Send notifications if new homework found
            if new_homework:
                self.send_notification(student_name, new_homework)

            # Save state
            self.save_state()

        except Exception as e:
            logger.error(f"Error checking homework for {student_name}: {e}")
            import traceback
            traceback.print_exc()

    def send_notification(self, student_name, homework_list):
        """Send notification via webhook or Apprise"""
        try:
            if not hasattr(self, 'apobj') or len(self.apobj) == 0:
                logger.warning("No notifiers configured")
                return

            # Filter to only today's homework
            today = datetime.now().strftime('%Y-%m-%d')
            today_homework = [hw for hw in homework_list if hw.get('date', '')[:10] == today]

            if not today_homework:
                logger.info(f"No homework for today ({today}), skipping notification")
                return

            # Format homework message
            message = f"📚 New homework for {student_name} (Today: {today}):\n\n"

            for idx, hw in enumerate(today_homework, 1):
                date_str = hw.get('date', '')[:10]  # Just the date part
                subject = hw.get('subject', 'Unknown')
                homework = hw.get('homework', '')
                teacher = hw.get('teacher', '')

                message += f"{idx}. {subject} ({date_str})\n"
                message += f"   👨‍🏫 {teacher}\n"
                message += f"   📝 {homework[:200]}\n"  # Limit length
                if len(homework) > 200:
                    message += f"   ...\n"
                message += "\n"

            title = f"SmartSchool Homework - {student_name}"

            logger.info(f"Sending notification: {title}")

            # Check if using webhook (json:// or jsons://)
            notifiers_str = os.getenv('NOTIFIERS', '')
            if 'json://' in notifiers_str or 'jsons://' in notifiers_str:
                # Send directly via requests for webhooks
                self._send_webhook_notification(notifiers_str, title, message)
            else:
                # Use Apprise for other notification types
                self.apobj.notify(
                    body=message,
                    title=title
                )

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def _send_webhook_notification(self, notifier_url, title, message):
        """Send notification directly to webhook"""
        try:
            # Parse the webhook URL
            # Format: json://host:port/path or jsons://host:port/path
            if notifier_url.startswith('jsons://'):
                url = 'https://' + notifier_url[8:]
                verify_ssl = True
            elif notifier_url.startswith('json://'):
                url = 'http://' + notifier_url[7:]
                verify_ssl = True
            else:
                logger.error(f"Unknown notifier format: {notifier_url}")
                return

            # Check for verify=no parameter
            if '?verify=no' in url:
                url = url.replace('?verify=no', '')
                verify_ssl = False

            # Prepare the exact format that works with curl
            payload = {
                "title": title,
                "message": message
            }

            logger.info(f"Sending webhook to: {url}")
            logger.debug(f"Payload: {payload}")

            # Send the request
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                verify=verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✓ Webhook notification sent successfully")
            else:
                logger.error(f"Webhook returned status {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            import traceback
            traceback.print_exc()

    def schedule_checks(self):
        """Schedule homework checks at specific times"""
        schedules_str = os.getenv('SCHEDULES', '12:00,16:00,20:00')
        schedules = [s.strip() for s in schedules_str.split(',')]

        logger.info(f"Scheduling checks at: {schedules}")

        for schedule_time in schedules:
            schedule.every().day.at(schedule_time).do(self.run_all_checks)
            logger.info(f"Scheduled check at {schedule_time}")

    def run_all_checks(self):
        """Run homework checks for all students"""
        logger.info(f"Starting scheduled check at {datetime.now()}")

        for student in self.students:
            try:
                name = student.get('name', 'Unknown')
                username = student.get('username')
                password = student.get('password')
                student_params = student.get('student_params')  # Optional in config

                if not username or not password:
                    logger.warning(f"Missing credentials for {name}")
                    continue

                self.check_homework(name, username, password, student_params)

            except Exception as e:
                logger.error(f"Error checking homework for student: {e}")

            # Small delay between checks
            time.sleep(2)

    def start(self):
        """Start the monitor"""
        logger.info("Starting SmartSchool Homework Monitor v2 (with Selenium)")

        self.schedule_checks()

        # Run first check immediately
        self.run_all_checks()

        # Keep scheduler running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    try:
        monitor = SmartSchoolMonitor()
        monitor.start()
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}")
        raise
