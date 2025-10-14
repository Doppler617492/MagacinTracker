# Installation Scripts Guide

This directory contains automated scripts to help you set up the Magacin Track project.

## 📁 Available Scripts

### 1. `check-prerequisites.sh` - System Checker
**Purpose:** Check what software is installed on your system

**When to use:** 
- Before starting installation
- To verify prerequisites are installed
- To diagnose installation issues

**What it checks:**
- ✅ Xcode Command Line Tools
- ✅ Homebrew
- ✅ Python 3 and pip
- ✅ Node.js and npm
- ✅ Docker and Docker Compose
- ✅ Git
- ✅ Python virtual environment
- ✅ Frontend dependencies

**Usage:**
```bash
./check-prerequisites.sh
```

**Output:** Color-coded report showing what's installed (green ✓) and what's missing (red ✗)

---

### 2. `install-prerequisites.sh` - System Setup
**Purpose:** Install system-level dependencies (Homebrew, Node.js, Docker)

**When to use:**
- After installing Xcode Command Line Tools
- To install missing prerequisites

**What it installs:**
- ✅ Homebrew (if not installed)
- ✅ Node.js 18 (via Homebrew)
- ✅ Docker Desktop (optional, asks first)
- ✅ PostgreSQL client (optional, asks first)
- ✅ Redis (optional, asks first)

**Requirements:**
- Xcode Command Line Tools must be installed first

**Usage:**
```bash
./install-prerequisites.sh
```

**Interactive:** Will ask for confirmation before installing optional components

---

### 3. `setup.sh` - Project Setup
**Purpose:** Install all project-specific dependencies

**When to use:**
- After all prerequisites are installed
- When dependencies need to be reinstalled

**What it does:**
1. Creates Python virtual environment (if not exists)
2. Installs Python backend dependencies
3. Installs AI Engine Python dependencies
4. Installs all frontend dependencies (Admin, PWA, TV)
5. Verifies Docker setup

**Requirements:**
- All prerequisites must be installed
- Run `./check-prerequisites.sh` first to verify

**Usage:**
```bash
./setup.sh
```

**Time:** Takes 10-15 minutes depending on internet speed

---

## 🚀 Typical Installation Flow

### First Time Setup

```bash
# 1. Check current status
./check-prerequisites.sh

# 2. Install Xcode Command Line Tools (if needed)
xcode-select --install
# Wait for installation dialog to complete

# 3. Install system prerequisites
./install-prerequisites.sh
# Answer prompts for optional components

# 4. Verify prerequisites are installed
./check-prerequisites.sh
# Should show all green checkmarks

# 5. Install project dependencies
./setup.sh
# Wait for completion (10-15 minutes)

# 6. Start the application
docker-compose up -d
```

---

## 🔍 Script Details

### check-prerequisites.sh

**Exit Codes:**
- `0` - Success (may still have missing items, check output)

**Output Sections:**
1. System Prerequisites
2. Project Dependencies
3. Summary with next steps

**Does NOT install anything** - only checks and reports

---

### install-prerequisites.sh

**Exit Codes:**
- `0` - Success
- `1` - Xcode Command Line Tools not found

**Prompts:**
- Docker Desktop installation (y/N)
- PostgreSQL client installation (y/N)
- Redis installation (y/N)

**Requires:**
- Internet connection
- Administrator password (for Homebrew first-time install)

**Safe to re-run:** Yes, skips already installed items

---

### setup.sh

**Exit Codes:**
- `0` - Success
- `1` - Prerequisites not met

**Environment:**
- Creates `backend/venv/` directory
- Installs to `frontend/node_modules/` (workspace style)

**Safe to re-run:** Yes, but will reinstall dependencies

**Speed up re-runs:**
- Python: Reuses existing venv if present
- Node.js: Uses npm cache

---

## 🛠️ Troubleshooting

### Script Won't Run - Permission Denied

```bash
chmod +x *.sh
```

### Xcode Check Fails

```bash
# Reset Xcode Command Line Tools
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```

### Homebrew Not Found After Install

```bash
# Add to PATH (Apple Silicon)
eval "$(/opt/homebrew/bin/brew shellenv)"

# Add to PATH (Intel)
eval "$(/usr/local/bin/brew shellenv)"

# Make permanent
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
```

### Node.js Not Found After Install

```bash
# Link Node.js
brew link node@18

# Or use specific version
brew install node@18 && brew link --overwrite node@18
```

### Python Dependencies Fail

```bash
# Delete and recreate virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
./setup.sh
```

### Frontend Dependencies Fail

```bash
# Clear npm cache
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Docker Check Fails

```bash
# Make sure Docker Desktop is running
open -a Docker

# Wait 30 seconds, then verify
docker ps
```

---

## 📊 What Gets Installed

### System Level (install-prerequisites.sh)
```
Homebrew
├── Node.js 18
├── npm (comes with Node.js)
└── Optional:
    ├── Docker Desktop
    ├── PostgreSQL client
    └── Redis
```

### Project Level (setup.sh)

**Python (backend/venv/):**
```
Backend Dependencies:
├── FastAPI 0.111.0
├── SQLAlchemy 2.0.29
├── Pydantic 2.7.0
├── Redis 5.0.4
├── Asyncpg 0.29.0
├── Alembic 1.13.1
└── [20+ more packages]

AI Engine Dependencies:
├── NumPy 1.24.3
├── Scikit-learn 1.3.0
└── [10+ more packages]
```

**Node.js (frontend/node_modules/):**
```
Frontend Dependencies:
├── React 18.2.0
├── Ant Design 5.16.0
├── TypeScript 5.4.5
├── Vite 5.2.11
└── [100+ more packages across 3 apps]
```

---

## ⏱️ Time Estimates

| Script | Duration | Notes |
|--------|----------|-------|
| check-prerequisites.sh | < 10 seconds | Just checking |
| install-prerequisites.sh | 10-15 min | Depends on internet |
| setup.sh | 10-15 min | Downloads packages |
| **Total First Install** | **20-30 min** | Excluding Xcode |

**Xcode Command Line Tools:** Additional 5-10 minutes (one-time)

---

## 🔄 Maintenance

### Update Dependencies

```bash
# Update Python dependencies
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Update Node.js dependencies
cd frontend
npm update
```

### Clean Reinstall

```bash
# Python
cd backend
rm -rf venv
./setup.sh

# Node.js
cd frontend
rm -rf node_modules package-lock.json
./setup.sh
```

### Update System Packages

```bash
brew update
brew upgrade
```

---

## 📝 Files Created

After running all scripts, you'll have:

```
backend/
├── venv/                    # Python virtual environment
│   ├── bin/
│   ├── lib/
│   └── ...

frontend/
├── node_modules/            # Node.js packages (shared)
├── admin/node_modules/      # Admin-specific packages
├── pwa/node_modules/        # PWA-specific packages
└── tv/node_modules/         # TV-specific packages
```

**Size estimates:**
- Python venv: ~500 MB
- Node modules: ~800 MB - 1 GB
- Total: ~1.3 - 1.5 GB

---

## 🔐 Security Notes

- Scripts use official sources (Homebrew, npm, PyPI)
- No sensitive data is stored
- Passwords may be requested for:
  - Xcode installation (system password)
  - Homebrew first install (system password)
- All scripts can be reviewed before running

---

## 🎯 Quick Reference

```bash
# Check what's installed
./check-prerequisites.sh

# Install system software
./install-prerequisites.sh

# Install project dependencies
./setup.sh

# Full clean install
rm -rf backend/venv frontend/node_modules
./setup.sh
```

---

## 📚 Related Documentation

- **QUICKSTART.md** - Quick start guide
- **SETUP.md** - Detailed setup instructions  
- **INSTALLATION-SUMMARY.md** - Complete installation overview
- **README.md** - Project overview
- **docs/deployment-guide.md** - Production deployment

---

**Last Updated:** October 11, 2025

