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
VENV_DIR=".build_env"

# Defaults (can be overridden by flags)
SCRIPT_NAME="mphm_cli.py"
BINARY_NAME="fe_local"

# Args: --script <script.py> --name <binary_name> [--force]
FORCE_FLAG="${1:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --script)
      SCRIPT_NAME="$2"; shift 2 ;;
    --name)
      BINARY_NAME="$2"; shift 2 ;;
    --force)
      FORCE_FLAG="--force"; shift ;;
    *)
      # ignore unknown
      shift ;;
  esac
done

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
  if [[ "$FORCE_FLAG" != "--force" ]]; then
    echo -e "${GREEN}✅ Using existing binary: $PROJECT_ROOT/bin/$BINARY_NAME${NC}"
    exit 0
  fi
fi

# Cleanup old builds (only if forced or first time)
if [[ "$FORCE_FLAG" == "--force" ]] || [ ! -f "$PROJECT_ROOT/bin/$BINARY_NAME" ]; then
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

# Build binary with optimizations for faster startup
echo -e "${BLUE}🔨 Building binary...${NC}"
pyinstaller \
  --onefile \
  --clean \
  --name "$BINARY_NAME" \
  --optimize=2 \
  --strip \
  --noupx \
  --exclude-module tkinter \
  --exclude-module matplotlib \
  --exclude-module numpy \
  --exclude-module pandas \
  --exclude-module PIL \
  --exclude-module cv2 \
  --exclude-module tensorflow \
  --exclude-module torch \
  --exclude-module sklearn \
  --exclude-module scipy \
  --exclude-module jupyter \
  --exclude-module notebook \
  --exclude-module IPython \
  --exclude-module sphinx \
  --exclude-module pytest \
  --exclude-module unittest \
  --exclude-module doctest \
  --exclude-module pdb \
  --exclude-module profile \
  --exclude-module pstats \
  --exclude-module cProfile \
  --exclude-module hotshot \
  --exclude-module timeit \
  --exclude-module trace \
  --exclude-module tracemalloc \
  --exclude-module faulthandler \
  --exclude-module gc \
  --exclude-module sysconfig \
  --exclude-module distutils \
  --exclude-module setuptools \
  --exclude-module pip \
  --exclude-module wheel \
  --exclude-module packaging \
  --exclude-module pkg_resources \
  --exclude-module importlib_metadata \
  --exclude-module zipp \
  --exclude-module tomli \
  --exclude-module backports \
  --exclude-module jaraco \
  --exclude-module more_itertools \
  --exclude-module importlib_resources \
  --exclude-module pygments \
  --exclude-module markdown_it \
  --exclude-module mdurl \
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