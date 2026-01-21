import os
import json
import re
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

# Try to use curl_cffi for better browser impersonation (like webtop_client.py)
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    logger.warning("curl_cffi not installed. Using standard requests. Install with: pip install curl_cffi")

# Configure logging
log_dir = Path("/app/logs") if Path("/app").exists() else Path("./logs")
log_dir.mkdir(exist_ok=True)
logger.add(f"{log_dir}/smartschool-monitor.log", rotation="500 MB", retention="7 days")

class SmartSchoolMonitor:
    def __init__(self):
        self.config_path = Path("/app/config/config.yaml") if Path("/app/config").exists() else Path("./config/config.yaml")
        self.state_file = Path("/app/config/homework_state.json") if Path("/app/config").exists() else Path("./config/homework_state.json")
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
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.homework_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def create_session(self):
        """Create a requests session with retry strategy"""
        # Use curl_cffi if available for better browser impersonation
        if CURL_CFFI_AVAILABLE:
            session = curl_requests.Session(impersonate="chrome")
        else:
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            session.verify = False  # Ignore SSL errors for SmartSchool

        # Set desktop browser user agent
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        return session

    def login(self, session, username, password):
        """Login to SmartSchool - tries web portal first, then mobile API fallback"""
        # Try web portal login first
        result = self._login_web_portal(session, username, password)
        if result[0] and result[1]:
            return result

        # Fall back to mobile API login
        logger.info("Web portal login failed, trying mobile API...")
        return self._login_mobile(session, username, password)

    def _login_web_portal(self, session, username, password):
        """Login via webtopserver API (like webtop_client.py)"""
        try:
            base_url = "https://webtop.smartschool.co.il"
            api_url = "https://webtopserver.smartschool.co.il"

            # Step 1: Get the login page to establish session
            session.get(f"{base_url}/account/login")

            # Step 2: Login via webtopserver API
            login_url = f"{api_url}/server/api/user/LoginByUserNameAndPassword"

            # Generate unique ID (device fingerprint)
            unique_id = hashlib.sha1(f"{username}-webtop-python".encode()).hexdigest()

            # Device data JSON
            device_data = {
                "isMobile": False,
                "isTablet": False,
                "isDesktop": True,
                "getDeviceType": "Desktop",
                "os": "Windows",
                "osVersion": "10",
                "browser": "Chrome",
                "browserVersion": "120.0.0.0",
                "browserMajorVersion": 120,
                "screen_resolution": "1920 x 1080",
                "cookies": True,
                "userAgent": session.headers.get("User-Agent", "")
            }

            # Set headers
            session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": base_url,
                "Referer": f"{base_url}/",
                "language": "he",
                "rememberme": "0",
            })

            # Build login payload
            login_payload = {
                "UserName": username,
                "Password": password,
                "Data": "",
                "captcha": "",
                "RememberMe": False,
                "BiometricLogin": "",
                "UniqueId": unique_id,
                "deviceDataJson": json.dumps(device_data)
            }

            response = session.post(login_url, json=login_payload)

            if response.status_code == 200:
                # Check if webToken cookie was set
                cookies = session.cookies.get_dict() if hasattr(session.cookies, 'get_dict') else dict(session.cookies)
                if "webToken" in cookies:
                    try:
                        data = response.json()
                        user_id = (
                            data.get("userId") or
                            data.get("UserId") or
                            data.get("id") or
                            data.get("Id")
                        )

                        # Only consider success if we have user ID or status is true
                        # This handles "half-authenticated" states where user is blocked
                        if user_id or data.get("status") or data.get("success"):
                            logger.info(f"Web portal login successful for {username}")
                            return session, cookies["webToken"], user_id
                    except:
                        pass

                    # Cookie exists but no user ID/success - might be blocked
                    logger.warning("Got webToken cookie but no valid user ID - may be blocked")

                # Check response for success without cookie
                try:
                    data = response.json()
                    if data.get("status") or data.get("success") or data.get("token"):
                        logger.info(f"Web portal login successful for {username}")
                        return session, data.get("token"), data.get("userId")
                except:
                    pass

            logger.warning(f"Web portal login failed for {username}")
            return None, None, None

        except Exception as e:
            logger.error(f"Web portal login error: {e}")
            return None, None, None

    def _login_mobile(self, session, username, password):
        """Login via mobile API (fallback)"""
        try:
            mobile_url = "https://www.webtop.co.il/mobilev2/"
            api_endpoint = "https://www.webtop.co.il/mobilev2/api/"

            # Step 1: Fetch login page to get cookies and security tokens
            response = session.get(f"{mobile_url}default.aspx")
            if response.status_code != 200:
                logger.error(f"Failed to fetch mobile login page: {response.status_code}")
                return None, None, None

            html = response.text

            # Extract platform
            platform = self._extract_platform(html) or "web"

            # Extract security token
            security_id, security_value = self._extract_security_data(html)

            # Step 2: Build and send login request
            login_url = f"{api_endpoint}?platform={platform}"

            login_data = {
                "action": "login",
                "rememberMe": "1",
                "captcha": "",
                "secondsToLogin": "23",
                "username": username,
                "password": password,
            }

            # Add security token if found
            if security_id and security_value:
                login_data[security_id] = security_value

            # Set content type for form data
            session.headers.update({
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://www.webtop.co.il",
                "Referer": "https://www.webtop.co.il/mobilev2/default.aspx",
            })

            response = session.post(login_url, data=login_data)

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data.get("error"):
                        logger.error(f"Mobile login error: {data.get('error')}")
                        return None, None, None

                    if data.get("refresh"):
                        logger.error("Mobile login requires CAPTCHA")
                        return None, None, None

                    token = data.get("token") or data.get("Token")
                    user_id = (
                        data.get("userId") or
                        data.get("UserId") or
                        data.get("id") or
                        data.get("userID")
                    )

                    # Try to extract user ID from token if not in response
                    if not user_id and token and "$" in token:
                        parts = token.split("$")
                        if parts and parts[0].isdigit():
                            user_id = parts[0]

                    if token or user_id:
                        logger.info(f"Mobile API login successful for {username}")
                        # Store platform for later API calls
                        session._platform = platform
                        return session, token, user_id

                except Exception as e:
                    logger.error(f"Failed to parse mobile login response: {e}")

            logger.error(f"Mobile API login failed for {username}")
            return None, None, None

        except Exception as e:
            logger.error(f"Mobile login error: {e}")
            return None, None, None

    def _extract_platform(self, html):
        """Extract platform identifier from login page"""
        match = re.search(r'<input[^>]*id=["\']platform["\'][^>]*value=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r'<input[^>]*value=["\']([^"\']+)["\'][^>]*id=["\']platform["\']', html, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_security_data(self, html):
        """Extract security token from captchaWrapper"""
        captcha_wrapper_match = re.search(
            r'<div[^>]*id=["\']captchaWrapper["\'][^>]*>(.*?)</div>',
            html,
            re.IGNORECASE | re.DOTALL
        )

        if captcha_wrapper_match:
            wrapper_content = captcha_wrapper_match.group(1)
            hidden_match = re.search(
                r'<input[^>]*type=["\']hidden["\'][^>]*id=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
                wrapper_content,
                re.IGNORECASE
            )
            if hidden_match:
                return hidden_match.group(1), hidden_match.group(2)

            hidden_match = re.search(
                r'<input[^>]*id=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
                wrapper_content,
                re.IGNORECASE
            )
            if hidden_match:
                return hidden_match.group(1), hidden_match.group(2)

        return None, None

    def get_homework(self, session, web_token, user_id=None):
        """Fetch homework from SmartSchool API - tries web API first, then mobile fallback"""
        # Try web API first
        result = self._get_homework_web(session, web_token)
        if result is not None:
            return result

        # Fall back to mobile API
        logger.info("Web homework API failed, trying mobile API...")
        return self._get_homework_mobile(session, user_id)

    def _get_homework_web(self, session, web_token):
        """Fetch homework from webtopserver API"""
        try:
            api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

            # Set headers
            web_headers = {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://webtop.smartschool.co.il",
                "Referer": "https://webtop.smartschool.co.il/",
                "language": "he",
                "rememberme": "0",
            }

            # Make request - relies on webToken cookie
            response = session.post(api_url, json={}, headers=web_headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("status") and data.get("data"):
                    logger.info("Successfully retrieved homework from web API")
                    return data

                # Check for "Invalid Request" error in Hebrew (often sent when blocked)
                if "בקשה לא-חוקית" in str(data):
                    logger.warning("Web API returned 'Invalid Request' (בקשה לא-חוקית) - falling back to mobile")
                    return None

                # Check for status: false
                if isinstance(data, dict) and data.get("status") is False:
                    error_desc = data.get("errorDescription", "Unknown error")
                    logger.warning(f"Web API returned error: {error_desc} - falling back to mobile")
                    return None

                return data

            if response.status_code == 401:
                logger.warning("Web API returned 401 - falling back to mobile")
                return None

            logger.warning(f"Web API failed with status {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Web homework API error: {e}")
            return None

    def _get_homework_mobile(self, session, user_id):
        """Fetch homework from mobile API (fallback)"""
        try:
            platform = getattr(session, '_platform', 'web')
            api_endpoint = f"https://www.webtop.co.il/mobilev2/api/?platform={platform}"

            # Set headers for mobile API
            mobile_headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://www.webtop.co.il",
                "Referer": "https://www.webtop.co.il/mobilev2/default.aspx",
            }

            # Try multiple homework-related actions
            actions_to_try = ["loadHomeWork", "getHomeWork", "loadSchedule", "getSchedule", "loadLessons"]

            for action_name in actions_to_try:
                data = {"action": action_name}
                if user_id:
                    data["userId"] = user_id

                logger.debug(f"Trying mobile API action: {action_name}")
                response = session.post(api_endpoint, data=data, headers=mobile_headers, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"Mobile API response for {action_name}: {str(result)[:300]}")

                    # Check if we got actual data (not empty and not error)
                    if result and not result.get("error"):
                        # Check if dict has meaningful content (more than just empty or meta fields)
                        if isinstance(result, dict) and len(result) > 0:
                            logger.info(f"Got data from mobile API action '{action_name}': keys={list(result.keys())}")
                            return result
                        elif isinstance(result, list) and len(result) > 0:
                            logger.info(f"Got {len(result)} items from mobile API action '{action_name}'")
                            return result

            logger.warning("All mobile API actions returned empty or error")
            return None

        except Exception as e:
            logger.error(f"Mobile homework API error: {e}")
            return None

    def hash_homework(self, homework_item):
        """Create a hash of homework item to detect changes"""
        try:
            # Create a string representation of the homework
            hw_str = json.dumps(homework_item, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(hw_str.encode()).hexdigest()
        except:
            return None

    def check_homework(self, student_name, username, password):
        """Check for new homework for a student"""
        try:
            session = self.create_session()

            # Login (returns session, token, user_id)
            session, web_token, user_id = self.login(session, username, password)
            if not session or not web_token:
                logger.error(f"Failed to get valid session for {student_name}")
                return

            # Get homework (pass user_id for mobile API fallback)
            homework_data = self.get_homework(session, web_token, user_id)
            logger.info(f"Homework data received: type={type(homework_data)}, value={str(homework_data)[:500] if homework_data else 'None/Empty'}")
            if not homework_data:
                logger.warning(f"No homework data for {student_name}")
                return

            # Debug: log the structure of homework_data
            logger.info(f"Homework data type: {type(homework_data)}")
            logger.info(f"Homework data keys: {homework_data.keys() if isinstance(homework_data, dict) else 'N/A'}")
            logger.info(f"Homework data sample: {str(homework_data)[:500]}")
            
            # Initialize state for this student if needed
            if student_name not in self.homework_state:
                self.homework_state[student_name] = {}
            
            # Process homework
            new_homework = []
            current_hashes = {}
            
            # Extract homework items (structure may vary, adjust as needed)
            homework_items = []
            if isinstance(homework_data, dict):
                # Try different possible structure formats
                if 'homework' in homework_data:
                    homework_items = homework_data['homework'] if isinstance(homework_data['homework'], list) else [homework_data['homework']]
                elif 'lessons' in homework_data:
                    homework_items = homework_data['lessons'] if isinstance(homework_data['lessons'], list) else [homework_data['lessons']]
                else:
                    homework_items = [homework_data]
            elif isinstance(homework_data, list):
                homework_items = homework_data
            
            logger.info(f"Processing {len(homework_items)} homework items for {student_name}")
            
            for item in homework_items:
                try:
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
                        logger.info(f"New homework detected for {student_name}")
                except Exception as e:
                    logger.error(f"Error processing homework item: {e}")
                    continue
            
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

    def send_notification(self, student_name, homework_list):
        """Send notification via Apprise"""
        try:
            if not hasattr(self, 'apobj') or len(self.apobj) == 0:
                logger.warning("No notifiers configured")
                return
            
            # Format homework message
            message = f"📚 New homework for {student_name}:\n\n"
            
            for idx, hw in enumerate(homework_list, 1):
                if isinstance(hw, dict):
                    # Try to extract relevant information
                    subject = hw.get('subject', 'Unknown Subject')
                    description = hw.get('description', hw.get('content', ''))
                    due_date = hw.get('dueDate', hw.get('date', ''))
                    
                    message += f"{idx}. {subject}\n"
                    if description:
                        message += f"   📝 {description[:100]}\n"
                    if due_date:
                        message += f"   📅 Due: {due_date}\n"
                    message += "\n"
            
            title = f"SmartSchool Homework Alert - {student_name}"
            
            logger.info(f"Sending notification: {title}")
            self.apobj.notify(
                body=message,
                title=title
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

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
                
                if not username or not password:
                    logger.warning(f"Missing credentials for {name}")
                    continue
                
                self.check_homework(name, username, password)
                
            except Exception as e:
                logger.error(f"Error checking homework for student: {e}")
            
            # Small delay between checks to avoid overwhelming the server
            time.sleep(2)

    def start(self):
        """Start the monitor"""
        logger.info("Starting SmartSchool Homework Monitor")
        
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
