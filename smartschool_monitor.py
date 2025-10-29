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

# Configure logging
log_dir = Path("/app/logs")
log_dir.mkdir(exist_ok=True)
logger.add(f"{log_dir}/smartschool-monitor.log", rotation="500 MB", retention="7 days")

class SmartSchoolMonitor:
    def __init__(self):
        self.config_path = Path("/app/config/config.yaml")
        self.state_file = Path("/app/config/homework_state.json")
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
        return session

    def login(self, session, username, password):
        """Login to SmartSchool and get webToken"""
        try:
            login_url = "https://webtop.smartschool.co.il/account/login"
            
            # Get login page to extract any CSRF tokens if needed
            response = session.get(login_url)
            response.raise_for_status()
            
            # Attempt login
            login_data = {
                'username': username,
                'password': password
            }
            
            response = session.post(login_url, data=login_data)
            response.raise_for_status()
            
            # Extract webToken from cookies
            cookies = session.cookies.get_dict()
            if 'webToken' in cookies:
                logger.info(f"Successfully logged in as {username}")
                return session, cookies['webToken']
            else:
                # Try to get token from response or other sources
                logger.warning(f"webToken not found in cookies for {username}")
                # The token might be set in a redirect or in local storage
                # For now, we'll return the session as-is
                return session, None
                
        except Exception as e:
            logger.error(f"Login failed for {username}: {e}")
            return None, None

    def get_homework(self, session, web_token):
        """Fetch homework from SmartSchool API"""
        try:
            api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"
            
            params = {
                'webToken': web_token
            }
            
            response = session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            homework_data = response.json()
            logger.debug(f"Retrieved homework data: {type(homework_data)}")
            
            return homework_data
            
        except Exception as e:
            logger.error(f"Failed to get homework: {e}")
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
            
            # Login
            session, web_token = self.login(session, username, password)
            if not session or not web_token:
                logger.error(f"Failed to get valid session for {student_name}")
                return
            
            # Get homework
            homework_data = self.get_homework(session, web_token)
            if not homework_data:
                logger.warning(f"No homework data for {student_name}")
                return
            
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
