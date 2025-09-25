# Quick Start Guide

This guide covers everything you need to know to set up, build, install, and use the LAMP CLI tools.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Building the Tools](#building-the-tools)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Uninstallation](#uninstallation)
7. [Troubleshooting](#troubleshooting)
8. [Development Setup](#development-setup)

## Prerequisites

### System Requirements

- **Operating System**: macOS (tested on macOS 10.15+)
- **Python**: Python 3.7 or higher
- **Homebrew**: Required for LAMP stack management
- **Sudo Access**: Required for system-level operations

### Required Software

```bash
# Check Python version
python3 --version

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python3
```

## Environment Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd localhostCLI

# Make scripts executable
chmod +x *.sh
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Prerequisites

```bash
# Check Python installation
python3 --version

# Check Homebrew installation
brew --version

# Check sudo access
sudo -v

# Verify virtual environment
which python
# Should show: /path/to/localhostCLI/venv/bin/python
```

### 4. Environment Management

```bash
# Activate virtual environment (when needed)
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Check installed packages
pip list

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Building the Tools

The LAMP CLI tools are built using PyInstaller to create standalone binaries.

### Quick Build (All Tools)

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Build all tools at once
./setup.sh
```

### Individual Tool Building

#### 1. LAMP CLI (Main Tool)

```bash
# Activate virtual environment
source venv/bin/activate

# Build the main LAMP CLI tool
./build.sh --script lamp_cli.py --name fe_lamp

# Build with force rebuild
./build.sh --script lamp_cli.py --name fe_lamp --force
```

#### 2. LAMP Site CLI (Virtual Host Management)

```bash
# Activate virtual environment
source venv/bin/activate

# Build the site management tool
./build.sh --script lamp_site_cli.py --name fe_lamp_site

# Build with force rebuild
./build.sh --script lamp_site_cli.py --name fe_lamp_site --force
```

#### 3. MPHM CLI (Legacy Tool)

```bash
# Activate virtual environment
source venv/bin/activate

# Build the legacy MAMP tool
./build.sh --script mphm_cli.py --name mphm

# Build with force rebuild
./build.sh --script mphm_cli.py --name mphm --force
```

### Build Process Details

The build process:

1. **Creates Virtual Environment**: Isolated build environment
2. **Installs Dependencies**: PyInstaller and required packages
3. **Optimizes Binary**: Excludes unnecessary modules for smaller size
4. **Creates Standalone Binary**: Single executable file
5. **Cleans Up**: Removes temporary build files

### Build Output

```bash
# Binaries are created in ./bin/ directory
./bin/fe_lamp          # Main LAMP CLI tool
./bin/fe_lamp_site      # Site management tool
./bin/mphm              # Legacy MAMP tool
```

### Build Options

```bash
# Available build options
./build.sh --script <script.py> --name <binary_name> [--force]

# Examples
./build.sh --script lamp_cli.py --name my_lamp_tool
./build.sh --script lamp_site_cli.py --name my_site_tool --force
```

### Virtual Environment Best Practices

```bash
# Always activate virtual environment before building
source venv/bin/activate

# Verify you're in the right environment
which python
# Should show: /path/to/localhostCLI/venv/bin/python

# Check installed packages
pip list

# Update dependencies regularly
pip install --upgrade -r requirements.txt

# Deactivate when done
deactivate
```

### Environment Isolation

```bash
# Create isolated environment for testing
python3 -m venv test_env
source test_env/bin/activate

# Install only required packages
pip install rich pyinstaller

# Test build in isolated environment
./build.sh --script lamp_cli.py --name fe_lamp

# Clean up test environment
deactivate
rm -rf test_env
```

## Running in Virtual Environment

### Development Mode (Recommended for Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Run tools directly from source
python3 lamp_cli.py --help
python3 lamp_site_cli.py --help
python3 mphm_cli.py --help

# Run with specific commands
python3 lamp_cli.py status
python3 lamp_cli.py install
python3 lamp_site_cli.py  # Interactive mode
```

### Using Built Binaries in Virtual Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Run built binaries locally
./bin/fe_lamp --help
./bin/fe_lamp_site --help
./bin/mphm --help

# Test functionality
./bin/fe_lamp status
./bin/fe_lamp install
```

### Environment Variables

```bash
# Set environment variables for virtual environment
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export FE_LAMP_NAME="fe_lamp"
export FE_LAMP_SITE_NAME="fe_lamp_site"

# Run with environment variables
python3 lamp_cli.py status
python3 lamp_site_cli.py --help
```

## Installation

### Global Installation (For Production Use)

```bash
# Activate virtual environment first
source venv/bin/activate

# Install all tools globally
./setup.sh

# Or install individually
./install.sh --name fe_lamp
./install.sh --name fe_lamp_site
./install.sh --name mphm
```

### Manual Installation

```bash
# Copy binaries to /usr/local/bin
sudo cp ./bin/fe_lamp /usr/local/bin/fe_lamp
sudo cp ./bin/fe_lamp_site /usr/local/bin/fe_lamp_site
sudo cp ./bin/mphm /usr/local/bin/mphm

# Make executable
sudo chmod +x /usr/local/bin/fe_lamp
sudo chmod +x /usr/local/bin/fe_lamp_site
sudo chmod +x /usr/local/bin/mphm

# Handle macOS Gatekeeper
sudo xattr -dr com.apple.quarantine /usr/local/bin/fe_lamp
sudo xattr -dr com.apple.quarantine /usr/local/bin/fe_lamp_site
sudo xattr -dr com.apple.quarantine /usr/local/bin/mphm
```

### Installation Verification

```bash
# Check if tools are installed
which fe_lamp
which fe_lamp_site
which mphm

# Test the tools
fe_lamp --version
fe_lamp_site --version
mphm --version
```

## Usage

### LAMP CLI (Main Tool)

```bash
# Check installation status
fe_lamp status

# Install LAMP stack
fe_lamp install

# Start LAMP services
fe_lamp start

# Stop LAMP services
fe_lamp stop

# Restart LAMP services
fe_lamp restart

# Configure Apache
fe_lamp configure-apache --port 80

# Enable mod_rewrite
fe_lamp enable-mod-rewrite

# Check mod_rewrite status
fe_lamp check-rewrite-status

# Export databases
fe_lamp export-databases

# Show help
fe_lamp --help
```

### LAMP Site CLI (Virtual Host Management)

```bash
# Start interactive CLI
fe_lamp_site

# Show help
fe_lamp_site --help

# Show version
fe_lamp_site --version
```

### MPHM CLI (Legacy Tool)

```bash
# Start interactive CLI
mphm

# Show help
mphm --help

# Show version
mphm --version
```

## Uninstallation

### Global Uninstallation

```bash
# Uninstall all tools
./uninstall.sh

# Or uninstall individually
./uninstall.sh --name fe_lamp
./uninstall.sh --name fe_lamp_site
./uninstall.sh --name mphm
```

### Manual Uninstallation

```bash
# Remove binaries
sudo rm /usr/local/bin/fe_lamp
sudo rm /usr/local/bin/fe_lamp_site
sudo rm /usr/local/bin/mphm

# Remove LAMP configuration (optional)
sudo rm -rf /opt/fe_lamp
```

### Uninstall LAMP Stack

```bash
# Uninstall LAMP components
fe_lamp uninstall

# With database export
fe_lamp uninstall --export-db --export-path ./backups
```

## Troubleshooting

### Common Issues

#### 1. Build Issues

```bash
# Error: Python not found
# Solution: Install Python 3
brew install python3

# Error: PyInstaller not found
# Solution: Install PyInstaller in virtual environment
source venv/bin/activate
pip install pyinstaller

# Error: Permission denied
# Solution: Check file permissions
chmod +x *.sh

# Error: Virtual environment not activated
# Solution: Activate virtual environment
source venv/bin/activate

# Error: Dependencies not found
# Solution: Install dependencies in virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Installation Issues

```bash
# Error: Binary not found
# Solution: Build first
./build.sh --script lamp_cli.py --name fe_lamp

# Error: Sudo required
# Solution: Ensure sudo access
sudo -v

# Error: Gatekeeper blocks binary
# Solution: Remove quarantine
sudo xattr -dr com.apple.quarantine /usr/local/bin/fe_lamp
```

#### 3. Runtime Issues

```bash
# Error: Homebrew not found
# Solution: Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Error: Apache not running
# Solution: Start Apache
brew services start httpd

# Error: MySQL not running
# Solution: Start MySQL
brew services start mysql
```

#### 4. Virtual Environment Issues

```bash
# Error: Virtual environment not found
# Solution: Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Error: Wrong Python interpreter
# Solution: Check which Python is being used
which python
# Should show: /path/to/localhostCLI/venv/bin/python

# Error: Dependencies not found in virtual environment
# Solution: Install dependencies in virtual environment
source venv/bin/activate
pip install -r requirements.txt

# Error: PYTHONPATH not set
# Solution: Set PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Error: Virtual environment deactivated
# Solution: Reactivate virtual environment
source venv/bin/activate

# Error: Package conflicts
# Solution: Create fresh virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

```bash
# Run with verbose output
fe_lamp --verbose

# Check system status
fe_lamp status

# Check Apache configuration
fe_lamp show-apache-config
```

### Log Files

```bash
# Apache error logs
tail -f /opt/homebrew/var/log/httpd/error_log

# Apache access logs
tail -f /opt/homebrew/var/log/httpd/access_log

# MySQL error logs
tail -f /opt/homebrew/var/log/mysql/error.log
```

## Development Setup

### For Developers (Virtual Environment Recommended)

```bash
# Clone repository
git clone <repository-url>
cd localhostCLI

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export FE_LAMP_NAME="fe_lamp"
export FE_LAMP_SITE_NAME="fe_lamp_site"

# Run from source (recommended for development)
python3 lamp_cli.py --help
python3 lamp_site_cli.py --help
python3 mphm_cli.py --help
```

### Development Workflow

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Make changes to source code
# Edit files in src/ directory

# 3. Test changes directly from source
python3 lamp_cli.py status
python3 lamp_site_cli.py --help

# 4. Build binary (optional for testing)
./build.sh --script lamp_cli.py --name fe_lamp --force

# 5. Test built binary
./bin/fe_lamp status

# 6. Install globally (for production testing)
./install.sh --name fe_lamp

# 7. Test global installation
fe_lamp status

# 8. Deactivate when done
deactivate
```

### Virtual Environment Management

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Check virtual environment
which python
# Should show: /path/to/localhostCLI/venv/bin/python

# Install/update dependencies
pip install --upgrade -r requirements.txt

# Check installed packages
pip list

# Deactivate virtual environment
deactivate

# Remove virtual environment (if needed)
rm -rf venv
```

### Environment Configuration

```bash
# Create .env file for environment variables
cat > .env << EOF
PYTHONPATH=${PWD}/src:${PYTHONPATH}
FE_LAMP_NAME=fe_lamp
FE_LAMP_SITE_NAME=fe_lamp_site
EOF

# Source environment variables
source .env

# Run tools
python3 lamp_cli.py status
```

### Code Structure

```
localhostCLI/
├── lamp_cli.py              # Main LAMP CLI tool
├── lamp_site_cli.py         # Site management tool
├── mphm_cli.py              # Legacy MAMP tool
├── src/                     # Source modules
│   ├── lamp_manager.py      # Core LAMP management
│   ├── lamp_apache_manager.py
│   ├── lamp_vhost_manager.py
│   ├── lamp_site_manager.py
│   └── ...
├── bin/                     # Built binaries
├── template/                # Template files
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── setup.sh                 # All-in-one setup
├── build.sh                 # Build script
├── install.sh               # Installation script
└── uninstall.sh             # Uninstallation script
```

### Testing

```bash
# Test LAMP CLI
./bin/fe_lamp status
./bin/fe_lamp install
./bin/fe_lamp start

# Test Site CLI
./bin/fe_lamp_site --help

# Test MPHM CLI
./bin/mphm --help
```

## Advanced Usage

### Custom Binary Names

```bash
# Build with custom names
./build.sh --script lamp_cli.py --name my_lamp_tool
./install.sh --name my_lamp_tool

# Use custom binary
my_lamp_tool status
```

### Multiple Installations

```bash
# Install different versions
./build.sh --script lamp_cli.py --name fe_lamp_v1
./build.sh --script lamp_cli.py --name fe_lamp_v2

./install.sh --name fe_lamp_v1
./install.sh --name fe_lamp_v2
```

### System Integration

```bash
# Add to PATH (if not already)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Create aliases
echo 'alias lamp="fe_lamp"' >> ~/.zshrc
echo 'alias site="fe_lamp_site"' >> ~/.zshrc
source ~/.zshrc
```

## Best Practices

### 1. Regular Updates

```bash
# Update tools
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Rebuild tools
./setup.sh

# Check for updates
fe_lamp --version
```

### 2. Virtual Environment Automation

```bash
# Create activation script
cat > activate_env.sh << 'EOF'
#!/bin/bash
# Activate virtual environment and set environment variables
source venv/bin/activate
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export FE_LAMP_NAME="fe_lamp"
export FE_LAMP_SITE_NAME="fe_lamp_site"
echo "Virtual environment activated!"
echo "Python path: $(which python)"
echo "PYTHONPATH: $PYTHONPATH"
EOF

chmod +x activate_env.sh

# Use activation script
./activate_env.sh

# Create deactivation script
cat > deactivate_env.sh << 'EOF'
#!/bin/bash
# Deactivate virtual environment
deactivate
echo "Virtual environment deactivated!"
EOF

chmod +x deactivate_env.sh
```

### 3. Backup Configuration

```bash
# Backup LAMP configuration
cp -r /opt/fe_lamp ./backup/

# Export databases before major changes
fe_lamp export-databases --output-dir ./backups
```

### 4. System Maintenance

```bash
# Regular status checks
fe_lamp status

# Clean up old backups
find ./backups -name "*.sql.gz" -mtime +30 -delete
```

### 5. Security

```bash
# Keep tools updated
git pull origin main
./setup.sh

# Monitor system logs
tail -f /opt/homebrew/var/log/httpd/error_log
```

## Support

### Getting Help

```bash
# Show help for any tool
fe_lamp --help
fe_lamp_site --help
mphm --help

# Check status
fe_lamp status
fe_lamp_site --version
```

### Documentation

- **Main Documentation**: `docs/LAMP_CLI_FEATURES.md`
- **Site CLI Documentation**: `docs/LAMP_SITE_CLI_FEATURES.md`
- **Quick Start**: `docs/QUICK_START.md` (this file)

### Issues and Support

For issues and feature requests, please contact the development team.

## Notes

- All tools require sudo privileges for system-level operations
- macOS Gatekeeper may block binaries on first run
- Virtual environments are used for isolated builds
- Build artifacts are cleaned up automatically
- Configuration is stored in `/opt/fe_lamp/`
- All operations include automatic backup creation
- Tools work with both bundled and source environments
