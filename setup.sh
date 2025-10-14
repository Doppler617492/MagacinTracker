#!/bin/bash

# Magacin Track - Automated Setup Script
# This script installs all project dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/doppler/Desktop/Magacin Track"

# Function to print colored messages
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Magacin Track - Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

print_step "Checking prerequisites..."

# Check Xcode Command Line Tools
if ! xcode-select -p &> /dev/null; then
    print_error "Xcode Command Line Tools not installed"
    echo "Please run: xcode-select --install"
    exit 1
else
    print_success "Xcode Command Line Tools installed"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not installed"
    echo "Please install Python 3.11+ using: brew install python@3.11"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python ${PYTHON_VERSION} installed"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js not installed"
    echo "Please install Node.js 18+ using: brew install node@18"
    exit 1
else
    NODE_VERSION=$(node --version)
    print_success "Node.js ${NODE_VERSION} installed"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm not installed"
    exit 1
else
    NPM_VERSION=$(npm --version)
    print_success "npm ${NPM_VERSION} installed"
fi

# Check Docker (optional but recommended)
if ! command -v docker &> /dev/null; then
    print_warning "Docker not installed (optional but recommended)"
    echo "Install from: https://www.docker.com/products/docker-desktop"
else
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    print_success "Docker ${DOCKER_VERSION} installed"
fi

echo ""
print_step "All prerequisites satisfied! Starting installation..."
echo ""

# ============================================
# Python Backend Setup
# ============================================
print_step "Setting up Python backend..."

cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_step "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_step "Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet

# Install main backend dependencies
print_step "Installing main backend dependencies..."
pip install -r requirements.txt --quiet
print_success "Main backend dependencies installed"

# Install AI Engine dependencies
print_step "Installing AI Engine dependencies..."
pip install -r services/ai_engine/requirements.txt --quiet
print_success "AI Engine dependencies installed"

print_success "Python backend setup complete!"
echo ""

# ============================================
# Frontend Setup
# ============================================
print_step "Setting up Frontend applications..."

cd "$PROJECT_ROOT/frontend"

# Install frontend dependencies using npm workspaces
print_step "Installing frontend dependencies (this may take a few minutes)..."
npm install

print_success "Frontend dependencies installed for:"
echo "  - Admin Dashboard"
echo "  - PWA (Progressive Web App)"
echo "  - TV Display"

print_success "Frontend setup complete!"
echo ""

# ============================================
# Docker Setup Verification
# ============================================
if command -v docker &> /dev/null; then
    print_step "Verifying Docker setup..."
    
    if docker ps &> /dev/null; then
        print_success "Docker is running"
        
        # Check docker-compose
        if command -v docker-compose &> /dev/null; then
            COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
            print_success "Docker Compose ${COMPOSE_VERSION} available"
        elif docker compose version &> /dev/null; then
            COMPOSE_VERSION=$(docker compose version --short)
            print_success "Docker Compose ${COMPOSE_VERSION} available (plugin)"
        fi
    else
        print_warning "Docker is installed but not running"
        echo "Please start Docker Desktop to use containerized services"
    fi
else
    print_warning "Docker not installed - you'll need it to run the full stack"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ============================================
# Next Steps
# ============================================
echo "Next steps:"
echo ""
echo "1. Review the configuration:"
echo "   - See SETUP.md for detailed instructions"
echo "   - Check docs/ directory for documentation"
echo ""
echo "2. Configure environment variables:"
echo "   - Create .env files based on documentation"
echo ""
echo "3. Run the application:"
echo ""
echo "   Option A - Using Docker (recommended):"
echo "   $ cd \"$PROJECT_ROOT\""
echo "   $ docker-compose up -d"
echo ""
echo "   Option B - Local development:"
echo "   Backend:"
echo "   $ cd \"$PROJECT_ROOT/backend\""
echo "   $ source venv/bin/activate"
echo "   $ cd services/api_gateway && python -m app"
echo ""
echo "   Frontend (in separate terminals):"
echo "   $ cd \"$PROJECT_ROOT/frontend/admin\" && npm run dev"
echo "   $ cd \"$PROJECT_ROOT/frontend/pwa\" && npm run dev"
echo "   $ cd \"$PROJECT_ROOT/frontend/tv\" && npm run dev"
echo ""
echo "4. Access the applications:"
echo "   - Admin Dashboard: http://localhost:5173"
echo "   - PWA: http://localhost:5174"
echo "   - TV Display: http://localhost:5175"
echo "   - API Gateway: http://localhost:8000"
echo ""
echo "For more information, see:"
echo "   - SETUP.md - Complete setup guide"
echo "   - README.md - Project overview"
echo "   - docs/user-guide.md - User documentation"
echo "   - docs/deployment-guide.md - Deployment instructions"
echo ""

# Deactivate virtual environment
deactivate 2>/dev/null || true

print_success "Happy coding! 🚀"

