#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Uninstall Script for FE Local
# ==============================
# Removes the globally installed fe_local binary
# ==============================

BINARY_NAME="fe_local"
INSTALL_PATH="/usr/local/bin/$BINARY_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️ Uninstalling FE Local...${NC}"

# Check if binary is installed
if [ ! -f "$INSTALL_PATH" ]; then
  echo -e "${YELLOW}⚠️ FE Local is not installed globally${NC}"
  echo -e "${BLUE}💡 Check if it's installed elsewhere:${NC}"
  echo "   which $BINARY_NAME"
  exit 0
fi

# Remove binary
echo -e "${BLUE}📦 Removing $INSTALL_PATH...${NC}"
sudo rm "$INSTALL_PATH"

# Verify removal
if [ ! -f "$INSTALL_PATH" ]; then
  echo -e "${GREEN}✅ Uninstallation successful!${NC}"
  echo -e "${GREEN}🎉 FE Local has been removed from your system${NC}"
  echo ""
  echo -e "${BLUE}💡 To reinstall:${NC}"
  echo "   ./build.sh && ./install.sh"
else
  echo -e "${RED}❌ Uninstallation failed${NC}"
  exit 1
fi
