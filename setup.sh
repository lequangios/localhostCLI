#!/usr/bin/env bash
set -euo pipefail

# ==============================
# All-in-One Setup Script for FE Local
# ==============================
# Builds and installs FE Local globally in one command
# ==============================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up (Build + Install)...${NC}"
echo ""

# Step 1: Build (forward all args, supports --script and --name)
echo -e "${BLUE}📦 Step 1: Building binary...${NC}"
if [ -f "$PROJECT_ROOT/build.sh" ]; then
  chmod +x "$PROJECT_ROOT/build.sh"
  "$PROJECT_ROOT/build.sh" "$@"
else
  echo -e "${RED}❌ build.sh not found${NC}"
  exit 1
fi

echo ""

# Step 2: Install (forward all args; install.sh supports --name)
echo -e "${BLUE}📦 Step 2: Installing globally...${NC}"
if [ -f "$PROJECT_ROOT/install.sh" ]; then
  chmod +x "$PROJECT_ROOT/install.sh"
  "$PROJECT_ROOT/install.sh" "$@"
else
  echo -e "${RED}❌ install.sh not found${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
