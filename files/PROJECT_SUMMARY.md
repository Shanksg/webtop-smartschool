# SmartSchool Homework Monitor - Project Summary

## What I Created For You

I've built a complete Docker-based service that monitors SmartSchool for new homework and sends notifications. This is based on the `ofek-bot` pattern you referenced.

## Files Created

### Core Application Files
1. **smartschool_monitor.py** - Main Python application that:
   - Logs into SmartSchool with username/password
   - Fetches homework via the SmartSchool API
   - Detects new homework by comparing with stored state
   - Sends notifications via Apprise

2. **Dockerfile** - Docker image definition with all dependencies

3. **docker-compose.yml** - Docker Compose configuration to run the service
   - Configurable check times (default: 12:00, 16:00, 20:00)
   - Configurable notification services
   - Volume mounts for config and logs

4. **requirements.txt** - Python dependencies:
   - requests (HTTP requests)
   - schedule (scheduled tasks)
   - pyyaml (YAML config files)
   - loguru (logging)
   - apprise (multi-service notifications)

### Configuration Files
5. **config.yaml** - Template for storing student credentials (you fill this in)

6. **.gitignore** - Protects sensitive data from version control

### Documentation
7. **README.md** - Comprehensive documentation covering:
   - Setup instructions
   - Configuration options
   - Notification service examples
   - Troubleshooting guide
   - Security recommendations

8. **QUICKSTART.md** - 5-minute setup guide for quick deployment

### Optional
9. **smartschool-monitor.service** - Systemd service file (for Linux host deployment without Docker)

## How It Works

```
┌──────────────────────────────────────┐
│   Scheduled Times (12:00, 16:00)    │
└──────────────┬───────────────────────┘
               │
        ┌──────▼───────┐
        │  Login to    │
        │ SmartSchool  │
        └──────┬───────┘
               │
        ┌──────▼─────────────────┐
        │ Fetch Homework from API│
        └──────┬─────────────────┘
               │
        ┌──────▼──────────────────┐
        │ Compare with Previous   │
        │ (detect new homework)   │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────────────┐
        │ Send Notification       │
        │ (Home Assistant, etc.)  │
        └─────────────────────────┘
```

## Key Features

✅ **Authentication** - Logs in with username/password (like the screenshot showed)
✅ **Scheduled Checks** - Runs at specific times (12:00, 16:00, 20:00)
✅ **Smart Detection** - Only notifies on NEW homework (no duplicates)
✅ **Multi-Notification** - Supports Home Assistant, Discord, Telegram, Email, etc.
✅ **Persistent Storage** - Remembers what homework you've seen
✅ **Comprehensive Logging** - Full audit trail of all activity
✅ **Docker Containerized** - Easy deployment anywhere
✅ **Multiple Students** - Monitor multiple children

## Setup Summary

1. **Download all files** to a directory
2. **Create `config/config.yaml`** with SmartSchool credentials
3. **Edit `docker-compose.yml`**:
   - Set `NOTIFIERS` with Home Assistant token (or other service)
   - Optionally adjust `SCHEDULES` times
4. **Run**: `docker-compose up -d`
5. **Check logs**: `docker-compose logs -f smartschool-monitor`

That's it! The service will check at your configured times.

## API Endpoint Used

The service uses the SmartSchool API endpoint you discovered:
```
https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework
```

This endpoint is called with your login credentials to fetch homework data.

## Notification Services Supported

Via Apprise, you can notify via:
- **Home Assistant** - Native integration
- **Telegram** - Instant messages to your phone
- **Discord** - Send to Discord channel or DM
- **Email** - Gmail, Outlook, etc.
- **Slack** - Send to Slack channel
- **Webhooks** - Custom integrations
- And 50+ other services!

See README.md for specific configuration examples.

## Security

- Credentials stored locally in `config/config.yaml` (not in Docker image)
- `.gitignore` prevents accidental credential leaks
- Runs in isolated Docker container
- Logs contain no sensitive data (passwords stripped)
- Use `.gitignore` to prevent committing credentials to git

## Next Steps

1. **Read QUICKSTART.md** for 5-minute setup
2. **Read README.md** for detailed documentation
3. **Create `config/config.yaml`** with your credentials
4. **Update `docker-compose.yml`** with your notification service
5. **Run `docker-compose up -d`**
6. **Monitor logs** to see it working

## Support & Customization

The code is well-commented and follows the `ofek-bot` pattern you requested. You can:
- Add more students to `config.yaml`
- Change check times in `docker-compose.yml`
- Add different notification services
- Modify the homework detection logic in `smartschool_monitor.py`
- Deploy on any Docker-compatible system

## Questions?

Check the README.md troubleshooting section or examine the logs:
```bash
docker-compose logs -f smartschool-monitor
```

## One Important Note

⚠️ **After testing the API** with your previous token, that token is now compromised. You should:
1. Log out of SmartSchool in your browser
2. Log back in to get a fresh session
3. Use your SmartSchool username/password in `config.yaml` instead of manually extracting tokens

The service will handle token generation automatically during login.

---

All files are ready to use. Good luck! 🚀
