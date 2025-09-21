#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Optimized Build script for FE Local CLI tool
# ==============================
# - Uses temporary venv for isolation
# - Builds a single-file binary with PyInstaller
# - Places final binary into ./bin/fe_local
# - Cleans up build artifacts
# - Optimized for faster builds
# ==============================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="mphm_cli.py"
VENV_DIR=".build_env"
BINARY_NAME="fe_local"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Building $BINARY_NAME ...${NC}"

# Check python
if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}❌ python3 not found. Please install Python 3.${NC}"
  exit 1
fi

# Check if we can skip build (binary exists and is newer than source)
if [ -f "$PROJECT_ROOT/bin/$BINARY_NAME" ] && [ "$PROJECT_ROOT/bin/$BINARY_NAME" -nt "$PROJECT_ROOT/$SCRIPT_NAME" ]; then
  echo -e "${YELLOW}⚠️ Binary is up to date. Use --force to rebuild.${NC}"
  if [[ "${1:-}" != "--force" ]]; then
    echo -e "${GREEN}✅ Using existing binary: $PROJECT_ROOT/bin/$BINARY_NAME${NC}"
    exit 0
  fi
fi

# Cleanup old builds (only if forced or first time)
if [[ "${1:-}" == "--force" ]] || [ ! -f "$PROJECT_ROOT/bin/$BINARY_NAME" ]; then
  echo -e "${YELLOW}🧹 Cleaning old builds...${NC}"
  rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist" "$PROJECT_ROOT/$BINARY_NAME.spec" "$PROJECT_ROOT/bin/$BINARY_NAME"
fi

# Create temporary venv (reuse if exists and recent)
if [ ! -d "$VENV_DIR" ] || [ "$VENV_DIR" -ot "$PROJECT_ROOT/requirements.txt" ]; then
  echo -e "${BLUE}🐍 Creating virtual environment...${NC}"
  python3 -m venv "$VENV_DIR"
else
  echo -e "${GREEN}♻️ Reusing existing virtual environment...${NC}"
fi

source "$VENV_DIR/bin/activate"

# Install dependencies with optimizations
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install --upgrade pip setuptools wheel --quiet
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
  pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
fi
pip install pyinstaller --quiet

# Build binary with optimizations
echo -e "${BLUE}🔨 Building binary...${NC}"
pyinstaller \
  --onefile \
  --clean \
  --name "$BINARY_NAME" \
  --optimize=2 \
  --strip \
  --noupx \
  --add-data "$PROJECT_ROOT/requirements.txt:." \
  "$PROJECT_ROOT/$SCRIPT_NAME"

# Collect artifact
mkdir -p "$PROJECT_ROOT/bin"
mv "$PROJECT_ROOT/dist/$BINARY_NAME" "$PROJECT_ROOT/bin/$BINARY_NAME"
chmod +x "$PROJECT_ROOT/bin/$BINARY_NAME"

# Deactivate and clean (keep venv for faster rebuilds)
deactivate
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist" "$PROJECT_ROOT/$BINARY_NAME.spec" "$PROJECT_ROOT/__pycache__"

# Show binary info
BINARY_SIZE=$(du -h "$PROJECT_ROOT/bin/$BINARY_NAME" | cut -f1)
echo ""
echo -e "${GREEN}✅ Build complete: $PROJECT_ROOT/bin/$BINARY_NAME${NC}"
echo -e "${GREEN}📊 Binary size: $BINARY_SIZE${NC}"
echo ""
echo -e "${BLUE}👉 Run locally:${NC}"
echo "   ./bin/$BINARY_NAME"
echo ""
echo -e "${BLUE}🌍 Install globally (optional):${NC}"
echo "   sudo cp ./bin/$BINARY_NAME /usr/local/bin/$BINARY_NAME"
echo "   $BINARY_NAME"
echo ""
echo -e "${YELLOW}⚠️ Note: If macOS Gatekeeper blocks the binary, run:${NC}"
echo "   xattr -dr com.apple.quarantine ./bin/$BINARY_NAME"
echo ""
echo -e "${GREEN}💡 Tip: Use --force to rebuild even if binary is up to date${NC}"