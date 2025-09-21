#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Uninstall Script for FE Local
# ==============================
# Removes the globally installed fe_local binary
# ==============================

# Default, overridable with --name
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
INSTALL_PATH="/usr/local/bin/$BINARY_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️ Uninstalling $BINARY_NAME...${NC}"

# Check if binary is installed
if [ ! -f "$INSTALL_PATH" ]; then
  echo -e "${YELLOW}⚠️ $BINARY_NAME is not installed globally${NC}"
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
  echo -e "${GREEN}🎉 $BINARY_NAME has been removed from your system${NC}"
  echo ""
  echo -e "${BLUE}💡 To reinstall:${NC}"
  echo "   ./build.sh --script <script.py> --name $BINARY_NAME && ./install.sh --name $BINARY_NAME"
else
  echo -e "${RED}❌ Uninstallation failed${NC}"
  exit 1
fi
