# Magacin Track - Complete Setup Guide

This guide will help you install all prerequisites and dependencies needed to run the Magacin Track project on your Mac.

## Prerequisites to Install

### 1. Xcode Command Line Tools
**Status**: A dialog should have appeared requesting installation. Click "Install" to proceed.

If the dialog didn't appear, run:
```bash
xcode-select --install
```

After installation, verify with:
```bash
xcode-select -p
```

### 2. Homebrew (Package Manager for macOS)
If not installed, install Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. Python 3.11+ 
```bash
brew install python@3.11
```

Verify installation:
```bash
python3 --version
```

### 4. Node.js 18+ and npm
```bash
brew install node@18
```

Verify installation:
```bash
node --version
npm --version
```

### 5. Docker Desktop for Mac
Download and install from: https://www.docker.com/products/docker-desktop

Or install via Homebrew:
```bash
brew install --cask docker
```

Then open Docker Desktop from Applications.

Verify installation:
```bash
docker --version
docker-compose --version
```

### 6. PostgreSQL Client (optional, for database access)
```bash
brew install postgresql@15
```

### 7. Redis (optional, for local development)
```bash
brew install redis
```

## Installing Project Dependencies

### Step 1: Install Python Virtual Environment
```bash
cd "/Users/doppler/Desktop/Magacin Track/backend"
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Python Backend Dependencies
```bash
# Main backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# AI Engine specific dependencies
pip install -r services/ai_engine/requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend"

# Install all frontend dependencies (uses npm workspaces)
npm install
```

This will install dependencies for:
- Admin dashboard (React + Ant Design)
- PWA (Progressive Web App for mobile)
- TV display (for warehouse displays)

### Step 4: Verify Docker Setup
```bash
docker --version
docker-compose --version

# Test Docker is running
docker ps
```

## Quick Start Scripts

### Run the entire stack with Docker:
```bash
cd "/Users/doppler/Desktop/Magacin Track"
docker-compose up -d
```

### Run backend services locally (development):
```bash
cd "/Users/doppler/Desktop/Magacin Track/backend"
source venv/bin/activate

# Start individual services
cd services/api_gateway && python -m app
```

### Run frontend applications (development):
```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend"

# Admin Dashboard
cd admin && npm run dev

# PWA
cd pwa && npm run dev

# TV Display
cd tv && npm run dev
```

## Environment Configuration

Create `.env` files for each service based on the examples provided in the documentation.

Key environment variables needed:
- Database connection strings (PostgreSQL)
- Redis connection
- JWT secrets
- API keys

## Troubleshooting

### Python Installation Issues
If `pip install` fails with compiler errors, ensure Xcode Command Line Tools are properly installed:
```bash
sudo xcode-select --reset
xcode-select --install
```

### Node.js Installation Issues
If npm install fails, try clearing the cache:
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Docker Issues
If Docker commands fail:
1. Ensure Docker Desktop is running
2. Check Docker Desktop preferences for resource allocation
3. Restart Docker Desktop

### Port Conflicts
Default ports used:
- API Gateway: 8000
- Task Service: 8001
- Catalog Service: 8002
- Import Service: 8003
- AI Engine: 8004
- Admin Frontend: 5173
- PWA: 5174
- TV Display: 5175
- PostgreSQL: 5432
- Redis: 6379
- Kafka: 9092

If any ports are in use, you can modify them in `docker-compose.yml` or service configuration files.

## Next Steps

1. Review the documentation in the `docs/` directory
2. Check `README.md` for architecture overview
3. See `docs/deployment-guide.md` for production deployment
4. See `docs/user-guide.md` for feature documentation

## Support

For issues or questions, refer to:
- Architecture documentation: `docs/architecture.md`
- Runbook: `docs/runbook.md`
- Test plans: `docs/test-plan.md`

