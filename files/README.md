# SmartSchool Homework Monitor

A Docker-based service that monitors SmartSchool for new homework and sends notifications to Home Assistant, Discord, Telegram, Email, and more.

## Features

- ✅ Monitors SmartSchool for new homework assignments
- ✅ Checks at specific times each day (customizable)
- ✅ Multiple notification channels via Apprise (Home Assistant, Discord, Telegram, Email, etc.)
- ✅ Stores credentials securely in config file
- ✅ Detects only new homework (no duplicate notifications)
- ✅ Comprehensive logging
- ✅ Docker containerized for easy deployment

## Prerequisites

- Docker and Docker Compose installed
- SmartSchool account with login credentials
- (Optional) Home Assistant instance with API access token

## Setup

### 1. Clone/Download the Project

```bash
mkdir smartschool-monitor
cd smartschool-monitor
# Copy all the files here (Dockerfile, docker-compose.yml, requirements.txt, smartschool_monitor.py)
```

### 2. Create Configuration

Create a `config/config.yaml` file with your student credentials:

```yaml
students:
  - name: "Student Name 1"
    username: "student_username"
    password: "student_password"
  
  - name: "Student Name 2"
    username: "another_username"
    password: "another_password"
```

⚠️ **Security Note**: Keep this file safe! The credentials are stored locally in the config directory.

### 3. Configure Notifications

Edit `docker-compose.yml` and set the `NOTIFIERS` environment variable with your notification service URLs.

#### Home Assistant Example

```yaml
NOTIFIERS: "hassio://user@192.168.1.100/YOUR_LONG_LIVED_ACCESS_TOKEN"
```

To get Home Assistant access token:
1. Go to Home Assistant → Profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Create a new token
4. Use format: `hassio://user@YOUR_HA_IP/TOKEN`

#### Other Notification Services

**Telegram:**
```
tgram://bottoken/ChatID1/ChatID2
```

**Discord:**
```
discord://avatar@webhook_id/webhook_token
```

**Email:**
```
mailto://user:password@gmail.com/recipient@example.com
```

**Multiple Services (comma-separated):**
```
NOTIFIERS: "hassio://user@192.168.1.100/token,tgram://bottoken/chatid"
```

See [Apprise Documentation](https://github.com/caronc/apprise/wiki) for all supported services.

### 4. Configure Check Times

Edit `docker-compose.yml` and customize the `SCHEDULES` variable:

```yaml
SCHEDULES: "12:00,16:00,20:00"
```

This will check for homework at 12:00 PM, 4:00 PM, and 8:00 PM daily.

### 5. Build and Run

```bash
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f smartschool-monitor
```

## File Structure

```
smartschool-monitor/
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
├── smartschool_monitor.py      # Main application
├── config/
│   ├── config.yaml            # Student credentials (create this)
│   └── homework_state.json    # Tracks seen homework (auto-generated)
└── logs/
    └── smartschool-monitor.log # Application logs
```

## Usage

### Starting the Service

```bash
docker-compose up -d
```

### Stopping the Service

```bash
docker-compose down
```

### Viewing Logs

```bash
# Follow logs in real-time
docker-compose logs -f smartschool-monitor

# View last 100 lines
docker-compose logs --tail 100 smartschool-monitor
```

### Rebuilding After Changes

```bash
docker-compose up -d --build
```

### Manual Testing

You can test the notifier configuration by manually running a check:

```bash
docker-compose exec smartschool-monitor python -c "
from smartschool_monitor import SmartSchoolMonitor
monitor = SmartSchoolMonitor()
monitor.run_all_checks()
"
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs smartschool-monitor
```

Common issues:
- `FileNotFoundError: Config file not found` → Create `config/config.yaml`
- `Failed to load config` → Check YAML syntax in `config.yaml`

### No notifications being sent

1. Verify `NOTIFIERS` environment variable is set in `docker-compose.yml`
2. Test the notifier URL format is correct
3. Check logs: `docker-compose logs smartschool-monitor`

### Not detecting new homework

1. Check that SmartSchool credentials are correct in `config.yaml`
2. Verify you're using correct login credentials (not token)
3. Check logs for login errors
4. The homework detection is based on content hash - if homework content doesn't change, no notification is sent

### SSL Certificate Error

If you see SSL certificate errors, they're expected from SmartSchool servers. The service handles these internally. If it's causing issues, check network connectivity.

## How It Works

1. **Initialization**: Loads student credentials from `config.yaml`
2. **Scheduling**: Sets up checks at specified times (default: 12:00, 16:00, 20:00)
3. **Login**: Logs into SmartSchool with student credentials
4. **Fetch**: Retrieves homework from SmartSchool API
5. **Compare**: Compares current homework with previously seen homework
6. **Notify**: If new homework is detected, sends notification via configured services
7. **Save**: Updates the local state file with current homework

## Logs

Logs are stored in the `logs/` directory and rotated automatically when they exceed 500MB. Last 7 days of logs are kept.

Log levels:
- `INFO`: Normal operation information
- `WARNING`: Non-critical issues
- `ERROR`: Issues that need attention

## Advanced Configuration

### Adding More Check Times

In `docker-compose.yml`:
```yaml
SCHEDULES: "08:00,12:00,16:00,20:00,22:00"
```

### Monitoring Multiple Students

In `config/config.yaml`:
```yaml
students:
  - name: "Son"
    username: "son_user"
    password: "son_pass"
  - name: "Daughter"
    username: "daughter_user"
    password: "daughter_pass"
```

Each student will be checked independently and notifications will include the student's name.

### Custom Network Configuration

If Home Assistant is running in a Docker network, update `docker-compose.yml`:

```yaml
networks:
  homeassistant_network:
    external: true

services:
  smartschool-monitor:
    networks:
      - homeassistant_network
```

## Support

For issues related to:
- **SmartSchool API**: Check the SmartSchool documentation
- **Apprise/Notifications**: See [Apprise Wiki](https://github.com/caronc/apprise/wiki)
- **Docker**: See [Docker documentation](https://docs.docker.com/)

## License

This project is provided as-is for personal use.

## Security Recommendations

1. Store `config/config.yaml` securely - don't commit to version control
2. Use `.gitignore` to exclude:
   ```
   config/config.yaml
   config/homework_state.json
   logs/
   ```
3. Don't share your SmartSchool credentials
4. Use strong passwords for any external notification services
5. Keep API tokens secure (Home Assistant, Discord, etc.)

## Contributing

Feel free to submit issues and enhancement requests!
