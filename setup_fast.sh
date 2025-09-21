#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Fast Setup Script for FE Local
# ==============================
# Sets up FE Local with fast Python wrapper instead of slow PyInstaller binary
# ==============================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up FE Local (Fast Python Wrapper)...${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/env" ]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Creating one...${NC}"
    
    # Create virtual environment
    python3 -m venv "$PROJECT_ROOT/env"
    
    # Activate and install dependencies
    source "$PROJECT_ROOT/env/bin/activate"
    pip install --upgrade pip setuptools wheel --quiet
    
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
    fi
    
    echo -e "${GREEN}✅ Virtual environment created and dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
fi

# Make fast wrapper executable
chmod +x "$PROJECT_ROOT/fe_local_fast.py"

# Create symlink for global access
INSTALL_PATH="/usr/local/bin/fe_local"
WRAPPER_PATH="$PROJECT_ROOT/fe_local_fast.py"

echo -e "${BLUE}🔗 Creating global symlink...${NC}"

# Remove existing installation if it exists
if [ -f "$INSTALL_PATH" ] || [ -L "$INSTALL_PATH" ]; then
    echo -e "${YELLOW}⚠️ Removing existing installation...${NC}"
    sudo rm -f "$INSTALL_PATH"
fi

# Create symlink
sudo ln -sf "$WRAPPER_PATH" "$INSTALL_PATH"

# Handle macOS Gatekeeper
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🔓 Handling macOS Gatekeeper...${NC}"
    xattr -dr com.apple.quarantine "$WRAPPER_PATH" 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}🎉 Fast setup complete! You can now run 'fe_local' from anywhere.${NC}"
echo ""
echo -e "${BLUE}📊 Performance Comparison:${NC}"
echo -e "   • PyInstaller binary: ~5 seconds startup"
echo -e "   • Fast Python wrapper: ~0.7 seconds startup"
echo -e "   • Speed improvement: 7x faster! 🚀"
echo ""
echo -e "${BLUE}👉 Try it now:${NC}"
echo "   fe_local --help"
echo "   fe_local --version"
echo ""
echo -e "${YELLOW}💡 Note: This uses the fast Python wrapper instead of PyInstaller binary${NC}"
echo -e "${YELLOW}   For maximum portability, use ./setup.sh for PyInstaller binary${NC}"
