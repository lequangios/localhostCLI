# 🚀 FE LAMP CLI

A comprehensive LAMP stack management toolkit for macOS developers. Provides powerful command-line tools for managing Apache, PHP, MySQL/MariaDB, and virtual hosts with advanced features like mod_rewrite support, database export, and project type detection.

## 📋 Table of Contents

- [Features](#-features)
- [Tools Overview](#-tools-overview)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Advanced Features](#-advanced-features)
- [Documentation](#-documentation)
- [Requirements](#-requirements)
- [Development](#-development)
- [Support](#-support)

## ✨ Features

### Core LAMP Management
- **Install/Configure**: Apache, PHP, MySQL/MariaDB, phpMyAdmin via Homebrew
- **Service Management**: Start/stop/restart services with status monitoring
- **Apache Configuration**: Auto-configure for PHP, phpMyAdmin aliases, session directories
- **Port Management**: Change Apache port and document root
- **mod_rewrite Support**: Enable/disable mod_rewrite with status tracking
- **Database Export**: Export databases with schema-only or full data options
- **Configuration Persistence**: Store settings in `/opt/fe_lamp/fe_lamp.json`

### Virtual Host Management
- **Site Creation**: Create virtual hosts with automatic Apache configuration
- **Project Detection**: Auto-detect project types (WordPress, Laravel, Symfony, etc.)
- **Domain Management**: Custom domain suffixes and port management
- **Template System**: Project templates with API endpoints
- **Hosts File Management**: Automatic `/etc/hosts` entry management
- **Status Tracking**: JSON-based status tracking for all operations

### Advanced Features
- **Rich CLI Interface**: Enhanced command-line experience with Rich library
- **Interactive Menus**: User-friendly interactive interfaces
- **Error Handling**: Comprehensive error handling and validation
- **Backup System**: Automatic backup creation for all operations
- **Logging**: Detailed logging for troubleshooting
- **Cross-Platform**: Optimized for macOS with Homebrew integration

## 🛠️ Tools Overview

### 1. LAMP CLI (`fe_lamp`)
Main LAMP stack management tool with comprehensive features:

```bash
fe_lamp status                    # Check LAMP stack status
fe_lamp install                   # Install LAMP stack
fe_lamp start|stop|restart        # Service management
fe_lamp configure-apache          # Apache configuration
fe_lamp enable-mod-rewrite        # Enable mod_rewrite
fe_lamp export-databases          # Export all databases
```

### 2. Site CLI (`fe_lamp_site`)
Virtual host and project management:

```bash
fe_lamp_site                      # Interactive site management
fe_lamp_site --help               # Show help
```

### 3. MPHM CLI (`mphm`)
Legacy MAMP management tool:

```bash
mphm                              # Interactive MAMP management
mphm --help                       # Show help
```

## 🚀 Quick Start

### Prerequisites
- macOS 10.15+
- Python 3.7+
- Homebrew
- Sudo access

### One-Command Setup
```bash
# Clone repository
git clone <repository-url>
cd localhostCLI

# Make scripts executable
chmod +x *.sh

# One-command setup (build + install)
./setup.sh
```

### Virtual Environment Setup (Recommended)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build and install
./setup.sh
```

## 📦 Installation

### Global Installation
```bash
# Build all tools
./setup.sh

# Or build individually
./build.sh --script lamp_cli.py --name fe_lamp
./build.sh --script lamp_site_cli.py --name fe_lamp_site
./build.sh --script mphm_cli.py --name mphm

# Install globally
./install.sh --name fe_lamp
./install.sh --name fe_lamp_site
./install.sh --name mphm
```

### Development Installation
```bash
# Activate virtual environment
source venv/bin/activate

# Run from source
python3 lamp_cli.py --help
python3 lamp_site_cli.py --help
python3 mphm_cli.py --help
```

## 🧭 Usage

### LAMP Stack Management
```bash
# Check status
fe_lamp status

# Install LAMP stack
fe_lamp install --db mysql

# Service management
fe_lamp start
fe_lamp stop
fe_lamp restart

# Apache configuration
fe_lamp configure-apache --port 8080 --doc-root /opt/homebrew/var/www

# mod_rewrite management
fe_lamp enable-mod-rewrite
fe_lamp disable-mod-rewrite
fe_lamp check-rewrite-status

# Database export
fe_lamp export-databases --output-dir ./backups
fe_lamp export-databases --schema-only --no-compress
```

### Virtual Host Management
```bash
# Interactive site management
fe_lamp_site

# Create new site
fe_lamp_site create

# List existing sites
fe_lamp_site list

# Delete site
fe_lamp_site delete

# Check site status
fe_lamp_site status
```

### Project Type Detection
The system automatically detects project types:

| Type       | Detection Markers                    |
|------------|--------------------------------------|
| WordPress  | `wp-config.php`                      |
| Laravel    | `artisan` file                       |
| Symfony    | `bin/console` or `symfony.lock`      |
| Drupal     | `core/lib/Drupal.php`               |
| Magento    | `bin/magento` and `app/code`         |
| PHP        | Common PHP files in root             |
| HTML       | `index.html` or `home.html`          |
| JavaScript | `package.json`                       |

## 🔧 Advanced Features

### mod_rewrite Management
```bash
# Enable mod_rewrite for Apache
fe_lamp enable-mod-rewrite

# Disable mod_rewrite
fe_lamp disable-mod-rewrite

# Check mod_rewrite status
fe_lamp check-rewrite-status

# Enable mod_rewrite for VirtualHosts
fe_lamp_site enable-rewrite

# Check VirtualHost rewrite status
fe_lamp_site rewrite-status
```

### Database Export
```bash
# Export all databases
fe_lamp export-databases --output-dir ./backups

# Export with options
fe_lamp export-databases \
  --output-dir ./backups \
  --user root \
  --password fe_root \
  --schema-only \
  --no-compress

# Export single database
fe_lamp export-databases --database mydb --output-dir ./backups
```

### Virtual Host Configuration
```bash
# Create site with custom domain
fe_lamp_site create --domain mysite.local --port 8080

# Enable rewrite for specific site
fe_lamp_site enable-rewrite --site mysite.local

# Check site configuration
fe_lamp_site show-config --site mysite.local
```

## 📚 Documentation

### Comprehensive Guides
- **[Quick Start Guide](docs/QUICK_START.md)**: Complete setup and usage guide
- **[LAMP CLI Features](docs/LAMP_CLI_FEATURES.md)**: Detailed LAMP CLI documentation
- **[Site CLI Features](docs/LAMP_SITE_CLI_FEATURES.md)**: Virtual host management guide

### Key Documentation Topics
- Environment setup and virtual environment usage
- Building and installation processes
- Advanced features and configuration
- Troubleshooting and best practices
- Development workflow and automation

## 🔧 Requirements

### System Requirements
- **Operating System**: macOS 10.15 or higher
- **Python**: Python 3.7 or higher
- **Homebrew**: Required for LAMP stack management
- **Sudo Access**: Required for system-level operations

### Dependencies
- **Rich**: Enhanced CLI output and formatting
- **PyInstaller**: Binary compilation and distribution
- **Homebrew Services**: Apache, PHP, MySQL/MariaDB management

### Installation Requirements
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3
brew install python3

# Install required tools
brew install httpd php mysql
```

## 👨‍💻 Development

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd localhostCLI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Run from source
python3 lamp_cli.py --help
python3 lamp_site_cli.py --help
```

### Development Workflow
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Make changes to source code
# Edit files in src/ directory

# 3. Test changes
python3 lamp_cli.py status
python3 lamp_site_cli.py --help

# 4. Build binary (optional)
./build.sh --script lamp_cli.py --name fe_lamp --force

# 5. Test built binary
./bin/fe_lamp status

# 6. Deactivate when done
deactivate
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
└── requirements.txt         # Python dependencies
```

## 🛠️ Build System

### Build Options
```bash
# Build individual tools
./build.sh --script lamp_cli.py --name fe_lamp
./build.sh --script lamp_site_cli.py --name fe_lamp_site
./build.sh --script mphm_cli.py --name mphm

# Build with force rebuild
./build.sh --script lamp_cli.py --name fe_lamp --force

# Build all tools
./setup.sh
```

### Installation Options
```bash
# Install globally
./install.sh --name fe_lamp
./install.sh --name fe_lamp_site
./install.sh --name mphm

# Uninstall
./uninstall.sh --name fe_lamp
./uninstall.sh --name fe_lamp_site
./uninstall.sh --name mphm
```

## 🔍 Troubleshooting

### Common Issues
- **Virtual Environment**: Ensure virtual environment is activated
- **Dependencies**: Install required packages in virtual environment
- **Permissions**: Check sudo access for system operations
- **Homebrew**: Verify Homebrew installation and services

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

## 📊 Dashboard

After installation, a dynamic dashboard is automatically deployed to the Apache document root. The dashboard provides:

- **Project Overview**: List of all managed projects
- **Project Grouping**: Projects grouped by type (WordPress, Laravel, etc.)
- **Status Information**: Real-time status of LAMP stack
- **Quick Access**: Direct links to projects
- **Configuration**: Current Apache and PHP settings

## 🎯 Best Practices

### Regular Maintenance
```bash
# Update tools
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt
./setup.sh

# Backup configuration
cp -r /opt/fe_lamp ./backup/

# Export databases
fe_lamp export-databases --output-dir ./backups
```

### Virtual Environment Management
```bash
# Create activation script
cat > activate_env.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
echo "Virtual environment activated!"
EOF

chmod +x activate_env.sh
./activate_env.sh
```

## 📞 Support

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
- **Quick Start**: `docs/QUICK_START.md`
- **LAMP CLI Features**: `docs/LAMP_CLI_FEATURES.md`
- **Site CLI Features**: `docs/LAMP_SITE_CLI_FEATURES.md`

### Issues and Support
For issues and feature requests, please contact the development team.

## 👨‍💻 Author

**Author**: levietquangt2@gmail.com  
**Experience**: 10+ years in PHP/WordPress/Laravel development  
**Specialization**: LAMP stack management, virtual host configuration, and developer tooling

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📈 Roadmap

- [ ] Windows support
- [ ] Docker integration
- [ ] Advanced project templates
- [ ] Performance monitoring
- [ ] Automated testing
- [ ] CI/CD integration