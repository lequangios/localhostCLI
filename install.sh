#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Global Installation Script for FE Local
# ==============================
# Installs the fe_local binary globally so it can be run as 'fe_local' from anywhere
# ==============================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BINARY_NAME="fe_local"
BINARY_PATH="$PROJECT_ROOT/bin/$BINARY_NAME"
INSTALL_PATH="/usr/local/bin/$BINARY_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing FE Local globally...${NC}"

# Check if binary exists
if [ ! -f "$BINARY_PATH" ]; then
  echo -e "${RED}❌ Binary not found at $BINARY_PATH${NC}"
  echo -e "${YELLOW}💡 Run ./build.sh first to build the binary${NC}"
  exit 1
fi

# Check if binary is executable
if [ ! -x "$BINARY_PATH" ]; then
  echo -e "${YELLOW}🔧 Making binary executable...${NC}"
  chmod +x "$BINARY_PATH"
fi

# Create /usr/local/bin if it doesn't exist
if [ ! -d "/usr/local/bin" ]; then
  echo -e "${YELLOW}📁 Creating /usr/local/bin directory...${NC}"
  sudo mkdir -p /usr/local/bin
fi

# Install binary globally
echo -e "${BLUE}📦 Installing to $INSTALL_PATH...${NC}"
sudo cp "$BINARY_PATH" "$INSTALL_PATH"
sudo chmod +x "$INSTALL_PATH"

# Handle macOS Gatekeeper if needed
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo -e "${YELLOW}🍎 Handling macOS Gatekeeper...${NC}"
  sudo xattr -dr com.apple.quarantine "$INSTALL_PATH" 2>/dev/null || true
fi

# Verify installation
if command -v "$BINARY_NAME" >/dev/null 2>&1; then
  echo ""
  echo -e "${GREEN}✅ Installation successful!${NC}"
  echo -e "${GREEN}🎉 You can now run 'fe_local' from anywhere${NC}"
  echo ""
  echo -e "${BLUE}📋 Usage examples:${NC}"
  echo "   fe_local               # Run the CLI tool"
  echo "   which fe_local         # Show installation path"
  echo "   fe_local --help        # Show help (if implemented)"
  echo ""
  echo -e "${YELLOW}🔄 To update:${NC}"
  echo "   1. Run ./build.sh to rebuild"
  echo "   2. Run ./install.sh to reinstall"
  echo ""
  echo -e "${YELLOW}🗑️ To uninstall:${NC}"
  echo "   sudo rm $INSTALL_PATH"
else
  echo -e "${RED}❌ Installation failed${NC}"
  echo -e "${YELLOW}💡 Make sure /usr/local/bin is in your PATH${NC}"
  exit 1
fi
