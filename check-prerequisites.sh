#!/bin/bash

# Prerequisite Checker for Magacin Track
# Run this script to check what needs to be installed

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_check() {
    echo -n "  Checking $1... "
}

print_installed() {
    echo -e "${GREEN}✓ Installed${NC} ($2)"
}

print_missing() {
    echo -e "${RED}✗ Missing${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Prerequisite Checker${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ALL_GOOD=true

# Check Xcode Command Line Tools
print_check "Xcode Command Line Tools"
if xcode-select -p &> /dev/null; then
    XCODE_PATH=$(xcode-select -p)
    print_installed "installed" "$XCODE_PATH"
else
    print_missing
    echo "    Install with: xcode-select --install"
    ALL_GOOD=false
fi

# Check Homebrew
print_check "Homebrew"
if command -v brew &> /dev/null; then
    BREW_VERSION=$(brew --version | head -n 1 | cut -d' ' -f2)
    print_installed "installed" "v$BREW_VERSION"
else
    print_missing
    echo "    Install from: https://brew.sh"
    ALL_GOOD=false
fi

# Check Python
print_check "Python 3"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_installed "installed" "v$PYTHON_VERSION"
    
    # Check pip
    print_check "pip"
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
        print_installed "installed" "v$PIP_VERSION"
    else
        print_missing
        ALL_GOOD=false
    fi
else
    print_missing
    echo "    Install with: brew install python@3.11"
    ALL_GOOD=false
fi

# Check Node.js
print_check "Node.js"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_installed "installed" "$NODE_VERSION"
else
    print_missing
    echo "    Install with: brew install node@18"
    ALL_GOOD=false
fi

# Check npm
print_check "npm"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_installed "installed" "v$NPM_VERSION"
else
    print_missing
    echo "    Install with Node.js"
    ALL_GOOD=false
fi

# Check Docker
print_check "Docker"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    print_installed "installed" "v$DOCKER_VERSION"
    
    # Check if Docker is running
    if docker ps &> /dev/null 2>&1; then
        echo -e "    ${GREEN}Docker daemon is running${NC}"
    else
        echo -e "    ${YELLOW}Docker is installed but not running${NC}"
        echo "    Start Docker Desktop from Applications"
    fi
else
    print_missing
    echo "    Install from: https://www.docker.com/products/docker-desktop"
    echo "    Or use: brew install --cask docker"
    print_warning "Optional but recommended for running the full stack"
fi

# Check Docker Compose
print_check "Docker Compose"
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
    print_installed "installed" "v$COMPOSE_VERSION"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version --short)
    print_installed "installed" "v$COMPOSE_VERSION (plugin)"
else
    print_missing
    echo "    Included with Docker Desktop"
fi

# Check Git
print_check "Git"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_installed "installed" "v$GIT_VERSION"
else
    print_missing
    echo "    Included with Xcode Command Line Tools"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

# Check project dependencies
echo ""
echo "Checking project dependencies:"
echo ""

PROJECT_ROOT="/Users/doppler/Desktop/Magacin Track"

# Check Python venv
print_check "Python virtual environment"
if [ -d "$PROJECT_ROOT/backend/venv" ]; then
    print_installed "exists" ""
else
    echo -e "${YELLOW}Not created yet${NC}"
    echo "    Will be created by setup.sh"
fi

# Check Node modules
print_check "Frontend dependencies"
if [ -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    print_installed "installed" ""
else
    echo -e "${YELLOW}Not installed yet${NC}"
    echo "    Will be installed by setup.sh"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All prerequisites are installed!${NC}"
    echo ""
    echo "You can now run the setup script:"
    echo "  $ ./setup.sh"
else
    echo -e "${YELLOW}⚠ Some prerequisites are missing${NC}"
    echo ""
    echo "Please install the missing items above, then run:"
    echo "  $ ./check-prerequisites.sh"
    echo ""
    echo "Once all prerequisites are installed, run:"
    echo "  $ ./setup.sh"
fi

echo ""
echo "For detailed setup instructions, see SETUP.md"

