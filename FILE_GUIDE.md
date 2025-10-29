# File Guide - What Each File Does

## 📖 Documentation Files (Read First!)

### START_HERE.md (👈 READ THIS FIRST!)
**Purpose**: Main entry point with quick overview and navigation guide
- Overview of the entire project
- Which document to read based on your needs
- Quick start summary
- Common commands

### PROJECT_SUMMARY.md
**Purpose**: Understand what was created and why
- What files were created and why
- How the system works (with diagram)
- Key features overview
- Architecture explanation

### QUICKSTART.md
**Purpose**: Get running in 5 minutes
- Step-by-step setup guide
- Copy-paste commands
- Common issues and fixes
- Perfect for first-time users

### README.md
**Purpose**: Complete reference documentation
- Comprehensive setup guide
- All configuration options
- Notification service examples
- Detailed troubleshooting
- Advanced features
- Security recommendations

### ENVIRONMENT_VARIABLES.md
**Purpose**: All environment variables explained
- What each variable does
- How to get tokens/IDs for services
- Examples for each service
- How to verify configuration

## 🔧 Application Files (Core Functionality)

### smartschool_monitor.py
**Purpose**: Main application code
**Language**: Python 3
**What it does**:
- Logs into SmartSchool
- Fetches homework data
- Detects new homework
- Sends notifications
**Well-commented**: Yes, easy to understand and modify
**Size**: ~12KB
**Don't need to edit unless**: You want to customize behavior

### Dockerfile
**Purpose**: Defines Docker image for the service
**What it does**:
- Installs Python and dependencies
- Sets up the application container
- Configures startup
**Size**: ~600 bytes
**Edit when**: Almost never (unless customizing container)

### docker-compose.yml
**Purpose**: Docker Compose configuration
**What it does**:
- Defines how to run the container
- Sets environment variables
- Mounts volumes for config and logs
- Configures networking
**IMPORTANT**: You MUST edit this file!
**Edit what**:
- `SCHEDULES`: When to check (12:00,16:00,20:00)
- `NOTIFIERS`: Where to send notifications
**Size**: ~1.3KB

### requirements.txt
**Purpose**: Python package dependencies
**What it contains**:
- requests - HTTP library
- schedule - Task scheduling
- pyyaml - YAML config parsing
- loguru - Logging
- apprise - Multi-service notifications
**Edit when**: Rarely (unless adding new Python packages)
**Size**: ~92 bytes

## ⚙️ Configuration Files (Your Customization)

### config.yaml
**Purpose**: Store student credentials
**Format**: YAML
**What goes here**:
- Student names
- SmartSchool usernames
- SmartSchool passwords
**IMPORTANT**: 
- Create this file yourself!
- Keep it secure - don't share!
- Add to .gitignore (already done)
**Size**: ~292 bytes (template)
**Edit**: Yes! Fill in with real credentials

### .gitignore
**Purpose**: Prevent accidental commits of sensitive files
**What it protects**:
- config/config.yaml (credentials)
- config/homework_state.json (state data)
- logs/ (log files)
- __pycache__/ (Python cache)
**Important**: Don't delete this file!
**Size**: ~379 bytes

## 🧪 Testing & Debugging

### test_setup.py
**Purpose**: Diagnose setup issues
**What it tests**:
- Python package imports
- Configuration file validity
- SmartSchool API connectivity
- Notification configuration
- Storage directory writability
**How to run**:
```bash
python test_setup.py
```
**Output**: Pass/Fail for each test with details
**Use when**: Something isn't working and you need to debug

## 📦 Optional Files

### smartschool-monitor.service
**Purpose**: Systemd service file for Linux
**Use when**: You want to run on Linux without Docker
**Not needed if**: Using Docker Compose (recommended)
**Size**: ~508 bytes

## File Organization

```
smartschool-monitor/              (your project folder)
├── Documentation (Read these)
│   ├── START_HERE.md            👈 Read this first!
│   ├── PROJECT_SUMMARY.md
│   ├── QUICKSTART.md
│   ├── README.md                (comprehensive reference)
│   ├── ENVIRONMENT_VARIABLES.md (env vars reference)
│   └── FILE_GUIDE.md            (this file)
│
├── Application (Core code)
│   ├── smartschool_monitor.py   (main application)
│   ├── Dockerfile               (Docker definition)
│   ├── docker-compose.yml       ⭐ Edit this!
│   └── requirements.txt          (Python dependencies)
│
├── Configuration (Your settings)
│   ├── config.yaml              (credentials - create this)
│   ├── .gitignore               (protect secrets)
│   └── config/                  (folder, create this)
│       ├── config.yaml          (credentials file)
│       └── homework_state.json  (auto-generated)
│
├── Logs (Auto-generated)
│   └── logs/
│       └── smartschool-monitor.log
│
└── Optional
    └── smartschool-monitor.service
```

## Quick Reference: Which File To Edit

| What you want to do | File to edit |
|---|---|
| Change check times | docker-compose.yml (SCHEDULES) |
| Add notification service | docker-compose.yml (NOTIFIERS) |
| Add student to monitor | config/config.yaml |
| Customize app behavior | smartschool_monitor.py |
| Add Python dependency | requirements.txt + Dockerfile |
| Run without Docker | smartschool-monitor.service |
| Debug issues | Run test_setup.py |
| Understand the project | README.md |

## Size Reference

| File | Size | Purpose |
|---|---|---|
| smartschool_monitor.py | 13 KB | Main app (largest) |
| README.md | 7 KB | Documentation |
| PROJECT_SUMMARY.md | 6 KB | Overview |
| START_HERE.md | 5 KB | Entry point |
| ENVIRONMENT_VARIABLES.md | 4 KB | Env vars guide |
| test_setup.py | 8 KB | Testing script |
| Dockerfile | 624 B | Docker image |
| docker-compose.yml | 1.3 KB | Compose config |
| config.yaml | 292 B | Config template |
| requirements.txt | 92 B | Dependencies |

## Getting Started Path

1. **Read**: START_HERE.md (2 min)
2. **Read**: PROJECT_SUMMARY.md (3 min)
3. **Read**: QUICKSTART.md (5 min)
4. **Create**: config/ directory and config.yaml
5. **Edit**: docker-compose.yml
6. **Run**: `docker-compose up -d`
7. **Check**: Logs with `docker-compose logs -f`
8. **Reference**: README.md when you need details

## Files You Don't Need To Edit

- smartschool_monitor.py (unless customizing)
- Dockerfile (unless customizing)
- requirements.txt (unless adding packages)
- .gitignore (unless customizing)
- smartschool-monitor.service (unless not using Docker)

## Files You MUST Create

- **config/config.yaml** - Your student credentials (template provided)

## Files You SHOULD Edit

- **docker-compose.yml** - Set SCHEDULES and NOTIFIERS

## Files You CAN Ignore

- smartschool-monitor.service (optional, for non-Docker)
- test_setup.py (optional, for debugging)

---

All files are in /mnt/user-data/outputs/ ready to download and use!
