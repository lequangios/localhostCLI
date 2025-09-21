#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Global Installation Script for FE Local
# ==============================
# Installs the fe_local binary globally so it can be run as 'fe_local' from anywhere
# ==============================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Defaults (overridable via flags)
BINARY_NAME="fe_local"

# Args: --name <binary_name>
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      BINARY_NAME="$2"; shift 2 ;;
    *)
      shift ;;
  esac
done

BINARY_PATH="$PROJECT_ROOT/bin/$BINARY_NAME"
INSTALL_PATH="/usr/local/bin/$BINARY_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing $BINARY_NAME globally...${NC}"

# Check if binary exists
if [ ! -f "$BINARY_PATH" ]; then
  echo -e "${RED}❌ Binary not found at $BINARY_PATH${NC}"
  echo -e "${YELLOW}💡 Run ./build.sh --name $BINARY_NAME --script <script.py> first to build the binary${NC}"
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
echo -e "${YELLOW}⚠️ This requires sudo privileges. Please enter your password when prompted.${NC}"
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
  echo -e "${GREEN}🎉 You can now run '$BINARY_NAME' from anywhere${NC}"
  echo ""
  echo -e "${BLUE}📋 Usage examples:${NC}"
  echo "   $BINARY_NAME               # Run the CLI tool"
  echo "   which $BINARY_NAME         # Show installation path"
  echo "   $BINARY_NAME --help        # Show help (if implemented)"
  echo ""
  echo -e "${YELLOW}🔄 To update:${NC}"
  echo "   1. Run ./build.sh --name $BINARY_NAME --script <script.py> to rebuild"
  echo "   2. Run ./install.sh --name $BINARY_NAME to reinstall"
  echo ""
  echo -e "${YELLOW}🗑️ To uninstall:${NC}"
  echo "   sudo rm $INSTALL_PATH"
else
  echo -e "${RED}❌ Installation failed${NC}"
  echo -e "${YELLOW}💡 Make sure /usr/local/bin is in your PATH${NC}"
  exit 1
fi
