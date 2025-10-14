# Quick Start Guide - Install Everything Needed

This guide will get you up and running quickly. Follow these steps in order.

## Current Status

I've detected what's installed on your system:

✅ **Already Installed:**
- Python 3 (system)
- pip
- Git

❌ **Need to Install:**
- Xcode Command Line Tools (installation dialog should have appeared)
- Homebrew (macOS package manager)
- Node.js and npm
- Docker Desktop (optional but recommended)

## Step-by-Step Installation

### Step 1: Install Xcode Command Line Tools

**A dialog should have appeared on your screen.** Click "Install" and wait for it to complete (5-10 minutes).

If no dialog appeared, run this command:
```bash
xcode-select --install
```

Wait for installation to complete, then verify:
```bash
xcode-select -p
# Should output: /Library/Developer/CommandLineTools
```

### Step 2: Install Homebrew

Run this command in Terminal:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions. After installation, you may need to add Homebrew to your PATH:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify installation:
```bash
brew --version
```

### Step 3: Install Node.js

```bash
brew install node@18
```

Verify installation:
```bash
node --version
npm --version
```

### Step 4: Install Docker Desktop (Recommended)

Download and install Docker Desktop:
https://www.docker.com/products/docker-desktop

Or install via Homebrew:
```bash
brew install --cask docker
```

After installation:
1. Open Docker Desktop from Applications folder
2. Wait for it to start (whale icon in menu bar should be steady)

Verify installation:
```bash
docker --version
docker-compose --version
```

### Step 5: Run the Automated Setup

Once all prerequisites are installed, run:

```bash
cd "/Users/doppler/Desktop/Magacin Track"
./check-prerequisites.sh    # Verify everything is installed
./setup.sh                  # Install all project dependencies
```

## What the setup.sh Script Does

The `setup.sh` script will automatically:

1. ✅ Create a Python virtual environment
2. ✅ Install all Python backend dependencies
3. ✅ Install all Node.js frontend dependencies
4. ✅ Verify Docker setup
5. ✅ Show you next steps to run the application

## After Installation

### Option A: Run with Docker (Easiest)

```bash
cd "/Users/doppler/Desktop/Magacin Track"
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis cache
- Kafka message broker
- All backend microservices
- All frontend applications

Access the apps:
- Admin Dashboard: http://localhost:5173
- API Documentation: http://localhost:8000/docs

### Option B: Run Locally (Development)

**Terminal 1 - Backend API:**
```bash
cd "/Users/doppler/Desktop/Magacin Track/backend"
source venv/bin/activate
cd services/api_gateway
python -m app
```

**Terminal 2 - Admin Frontend:**
```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend/admin"
npm run dev
```

**Terminal 3 - PWA:**
```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend/pwa"
npm run dev
```

## Time Estimates

- Xcode Command Line Tools: 5-10 minutes
- Homebrew: 2-5 minutes
- Node.js: 2-3 minutes
- Docker Desktop: 5-10 minutes
- Python dependencies: 3-5 minutes
- Node.js dependencies: 5-10 minutes

**Total: ~20-45 minutes** (depending on internet speed)

## Troubleshooting

### Xcode Install Fails
```bash
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```

### Homebrew Install Fails
Make sure you have administrator access on your Mac. You may need to enter your password during installation.

### Node Install Fails
```bash
brew update
brew install node@18
```

### Docker Desktop Won't Start
1. Check System Preferences → Security & Privacy
2. Allow Docker in the General tab if prompted
3. Restart Docker Desktop

### Python/pip Issues
If pip fails, try:
```bash
python3 -m pip install --upgrade pip
```

### Port Already in Use
If ports are in use, you can change them in `docker-compose.yml`:
- Frontend ports: 5173, 5174, 5175
- Backend ports: 8000-8004
- Database: 5432
- Redis: 6379

## Need Help?

Run the prerequisite checker anytime:
```bash
./check-prerequisites.sh
```

For detailed documentation:
- Full setup guide: `SETUP.md`
- Project overview: `README.md`
- Architecture: `docs/architecture.md`
- User guide: `docs/user-guide.md`

## Quick Commands Reference

```bash
# Check what's installed
./check-prerequisites.sh

# Install project dependencies
./setup.sh

# Start with Docker
docker-compose up -d

# Stop Docker services
docker-compose down

# View Docker logs
docker-compose logs -f

# Activate Python environment
cd backend && source venv/bin/activate

# Run backend service
cd backend/services/api_gateway && python -m app

# Run frontend
cd frontend/admin && npm run dev
```

## What's Next?

After installation:

1. **Configure Environment** - Set up `.env` files (see `docs/deployment-guide.md`)
2. **Explore the Admin Dashboard** - http://localhost:5173
3. **Read the User Guide** - `docs/user-guide.md`
4. **Try the Demo Scenario** - `docs/demo-scenario-sprint3.md`

Good luck! 🚀

