#!/bin/bash

# Install Prerequisites for Magacin Track
# Run this after installing Xcode Command Line Tools

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Installing Prerequisites${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Xcode Command Line Tools are installed
echo -e "${BLUE}Checking Xcode Command Line Tools...${NC}"
if ! xcode-select -p &> /dev/null; then
    echo -e "${RED}ERROR: Xcode Command Line Tools not installed${NC}"
    echo ""
    echo "Please install Xcode Command Line Tools first:"
    echo "  $ xcode-select --install"
    echo ""
    echo "Then run this script again."
    exit 1
fi
echo -e "${GREEN}✓ Xcode Command Line Tools installed${NC}"
echo ""

# Install Homebrew
echo -e "${BLUE}Checking Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [ -f "/opt/homebrew/bin/brew" ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    echo -e "${GREEN}✓ Homebrew installed${NC}"
else
    echo -e "${GREEN}✓ Homebrew already installed${NC}"
    brew --version
fi
echo ""

# Update Homebrew
echo -e "${BLUE}Updating Homebrew...${NC}"
brew update
echo ""

# Install Node.js
echo -e "${BLUE}Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 18..."
    brew install node@18
    
    # Link Node.js
    brew link node@18
    
    echo -e "${GREEN}✓ Node.js installed${NC}"
else
    echo -e "${GREEN}✓ Node.js already installed${NC}"
    node --version
    npm --version
fi
echo ""

# Ask about Docker
echo -e "${BLUE}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed${NC}"
    echo ""
    read -p "Do you want to install Docker Desktop? (recommended) [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Docker Desktop..."
        brew install --cask docker
        echo -e "${GREEN}✓ Docker Desktop installed${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Please open Docker Desktop from Applications folder${NC}"
        echo "and wait for it to start before running the project."
    else
        echo -e "${YELLOW}Skipping Docker installation${NC}"
        echo "You can install it later with: brew install --cask docker"
    fi
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
    docker --version
    
    # Check if Docker is running
    if docker ps &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker is running${NC}"
    else
        echo -e "${YELLOW}⚠ Docker is installed but not running${NC}"
        echo "Please start Docker Desktop from Applications folder"
    fi
fi
echo ""

# Install PostgreSQL client (optional)
echo -e "${BLUE}Checking PostgreSQL client...${NC}"
if ! command -v psql &> /dev/null; then
    read -p "Install PostgreSQL client? (optional, for database access) [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing PostgreSQL client..."
        brew install postgresql@15
        echo -e "${GREEN}✓ PostgreSQL client installed${NC}"
    else
        echo "Skipping PostgreSQL client"
    fi
else
    echo -e "${GREEN}✓ PostgreSQL client already installed${NC}"
fi
echo ""

# Install Redis (optional)
echo -e "${BLUE}Checking Redis...${NC}"
if ! command -v redis-cli &> /dev/null; then
    read -p "Install Redis? (optional, for local development) [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Redis..."
        brew install redis
        echo -e "${GREEN}✓ Redis installed${NC}"
    else
        echo "Skipping Redis"
    fi
else
    echo -e "${GREEN}✓ Redis already installed${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Prerequisites Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "Installed:"
command -v brew &> /dev/null && echo "  ✓ Homebrew $(brew --version | head -n1)"
command -v node &> /dev/null && echo "  ✓ Node.js $(node --version)"
command -v npm &> /dev/null && echo "  ✓ npm v$(npm --version)"
command -v docker &> /dev/null && echo "  ✓ Docker $(docker --version)"
command -v psql &> /dev/null && echo "  ✓ PostgreSQL client"
command -v redis-cli &> /dev/null && echo "  ✓ Redis"
echo ""

echo "Next steps:"
echo ""
echo "1. Verify all prerequisites:"
echo "   $ ./check-prerequisites.sh"
echo ""
echo "2. Install project dependencies:"
echo "   $ ./setup.sh"
echo ""
echo "3. Start the application:"
echo "   $ docker-compose up -d"
echo ""
echo "For detailed instructions, see QUICKSTART.md"
echo ""

