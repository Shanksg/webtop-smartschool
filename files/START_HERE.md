# 🎓 SmartSchool Homework Monitor - START HERE

Welcome! I've created a complete Docker-based service to monitor SmartSchool for homework and send notifications.

## 📚 Documentation (Read In This Order)

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** ← START HERE
   - Overview of what was created
   - How it works (with diagram)
   - Key features

2. **[QUICKSTART.md](QUICKSTART.md)** ← NEXT (5 min setup)
   - Step-by-step setup instructions
   - Common issues & fixes
   - First-time user guide

3. **[README.md](README.md)** ← DETAILED REFERENCE
   - Complete documentation
   - All configuration options
   - Troubleshooting guide
   - Advanced usage

## 🚀 Quick Start (TL;DR)

```bash
# 1. Create project directory
mkdir smartschool-monitor && cd smartschool-monitor

# 2. Copy all files here
# (You downloaded them from the outputs folder)

# 3. Create config file
mkdir config
cat > config/config.yaml << EOF
students:
  - name: "Your Child"
    username: "smartschool_username"
    password: "smartschool_password"
EOF

# 4. Edit docker-compose.yml
# Change this line:
#   NOTIFIERS: "hassio://user@192.168.1.100/YOUR_TOKEN"
# Get token from Home Assistant → Profile → Long-Lived Tokens

# 5. Start
docker-compose up -d

# 6. Check logs
docker-compose logs -f smartschool-monitor
```

Done! It will check for homework at 12:00, 16:00, and 20:00 (or your custom times).

## 📁 Files You Got

### Application Files (Core)
- **smartschool_monitor.py** - Main application code
- **Dockerfile** - Docker image definition
- **docker-compose.yml** - Docker Compose config (edit this!)
- **requirements.txt** - Python dependencies
- **config.yaml** - Template for credentials (create this!)

### Documentation
- **PROJECT_SUMMARY.md** - What was created & why
- **QUICKSTART.md** - 5-minute setup guide
- **README.md** - Complete reference manual
- **test_setup.py** - Debug script to test setup

### Optional
- **smartschool-monitor.service** - For Linux systemd (without Docker)

## ✅ What This Does

✓ **Logs in** to SmartSchool with your credentials
✓ **Checks for homework** at specific times (12:00, 16:00, 20:00)
✓ **Detects new homework** (no duplicate notifications)
✓ **Sends notifications** to Home Assistant, Discord, Telegram, Email, etc.
✓ **Runs in Docker** (works anywhere)
✓ **Tracks state** (remembers what homework you've seen)
✓ **Full logging** (see everything that happens)

## 🔧 Setup Checklist

- [ ] Read PROJECT_SUMMARY.md
- [ ] Read QUICKSTART.md
- [ ] Create config/ directory
- [ ] Create config/config.yaml with SmartSchool credentials
- [ ] Get Home Assistant access token (if using)
- [ ] Edit docker-compose.yml with notification URL
- [ ] Run `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f smartschool-monitor`

## 🎯 Next Steps

1. **First time?** → Read QUICKSTART.md (5 minutes)
2. **Need details?** → Read README.md (comprehensive guide)
3. **Debugging?** → Run `python test_setup.py`
4. **Having issues?** → Check README.md Troubleshooting section

## ⚡ Quick Commands

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f smartschool-monitor

# View last 50 lines
docker-compose logs --tail 50 smartschool-monitor

# Rebuild after code changes
docker-compose up -d --build

# Test your setup
python test_setup.py
```

## 🏠 Notification Services Supported

Via [Apprise](https://github.com/caronc/apprise/wiki):

- **Home Assistant** - `hassio://user@192.168.1.100/TOKEN`
- **Telegram** - `tgram://bottoken/chatid`
- **Discord** - `discord://webhook_id/webhook_token`
- **Email** - `mailto://user:password@gmail.com/to@example.com`
- **Slack** - `slack://token/channel`
- **50+ other services** - See Apprise wiki

## 🔐 Security Notes

- Store credentials securely (not in git)
- `.gitignore` is included to prevent accidental leaks
- Your SmartSchool password is stored locally, not online
- Log files don't contain passwords
- Docker runs in isolated container

## ❓ Questions?

1. **How do I...?** → Check README.md
2. **It's not working** → Check README.md Troubleshooting
3. **Something broke** → Run `python test_setup.py` to diagnose
4. **I need more features** → Code is in smartschool_monitor.py (well-commented)

## 📖 Reading Guide

**Choose your path:**

### Path A: Quick Setup (5 min)
QUICKSTART.md → Deploy → Done

### Path B: Thorough Setup (15 min)
PROJECT_SUMMARY.md → QUICKSTART.md → README.md → Deploy

### Path C: Full Understanding (30 min)
PROJECT_SUMMARY.md → README.md → QUICKSTART.md → Deploy → test_setup.py

### Path D: Advanced Customization
README.md → smartschool_monitor.py (code comments) → Deploy

## 🎉 You're All Set!

Everything is ready to use. Just:
1. Create your config.yaml
2. Edit docker-compose.yml
3. Run `docker-compose up -d`

Your homework notifications are on the way! 📚

---

**Need help?** Read the documentation files in order. They have everything you need.

**Found an issue?** Check README.md troubleshooting section.

**Want to customize?** The code is yours - smartschool_monitor.py is well-commented.

Good luck! 🚀
