# LAMP Site CLI Features Documentation

This comprehensive document covers all the features and capabilities of the LAMP Site CLI tool for managing virtual hosts and local development sites.

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [Virtual Host Management](#virtual-host-management)
4. [Project Type Detection](#project-type-detection)
5. [Domain Suffix Management](#domain-suffix-management)
6. [Project Template Creation](#project-template-creation)
7. [Status Monitoring](#status-monitoring)
8. [Configuration Management](#configuration-management)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Overview

The LAMP Site CLI is an interactive tool for managing LAMP virtual hosts and local development environments. It provides:

- **Virtual Host Management**: Create, delete, and list virtual hosts
- **Project Type Detection**: Automatic detection of WordPress, Laravel, Symfony, Drupal, etc.
- **Domain Suffix Management**: Custom domain suffixes (.local, .dev, .test, etc.)
- **Project Template Creation**: Quick setup of WordPress, Laravel, PHP, and HTML projects
- **Status Monitoring**: Check virtual host configuration status
- **Rich CLI Interface**: Beautiful, interactive command-line interface

## Core Features

### Interactive Menu System

The tool provides an interactive menu with the following options:

```
LAMP SITE TOOL (.test)
1) Create new site
2) List existing sites
3) Delete site
4) Create sample WordPress/Laravel/PHP/HTML project
5) Check virtual host status
6) Manage domain suffix
0) Exit
```

### Command Line Options

```bash
# Show help
lamp_site_cli --help

# Show version
lamp_site_cli --version

# Start interactive CLI
lamp_site_cli
```

## Virtual Host Management

### Create New Site

The create site functionality allows you to set up a new virtual host with:

- **Site Name**: Custom name for your site
- **Project Path**: Full path to your project folder
- **Description**: Optional description
- **Website Type**: Manual selection or auto-detection

#### Website Type Options

- **P** - PHP
- **L** - Laravel
- **S** - Symfony
- **W** - WordPress
- **D** - Drupal
- **M** - Magento
- **J** - JavaScript
- **H** - HTML
- **A** - Auto-detect

#### Laravel Special Handling

The tool includes special handling for Laravel projects:

- **Auto-detection**: Detects Laravel by presence of `artisan` file
- **Public Directory**: Automatically uses `public` directory as document root
- **Path Resolution**: Handles both project root and public directory paths

#### Example Usage

```bash
# Interactive creation
lamp_site_cli
# Choose option 1 (Create new site)
# Enter site name: mysite
# Enter project path: /Users/username/Sites/mysite
# Enter description: My WordPress site
# Choose website type: W (WordPress)
```

### List Existing Sites

The list functionality shows comprehensive information about all registered sites:

- **Site Name**: Display name
- **Project Type**: With emoji indicators
- **Status**: PATH, VHOST, HOSTS status
- **URL**: Full URL with port
- **Path**: Project directory path
- **Description**: Site description

#### Status Indicators

- **PATH**: Green if project directory exists, red if missing
- **VHOST**: Green if virtual host configuration exists, red if missing
- **HOSTS**: Green if hosts file entry exists, red if missing

#### Project Type Emojis

- 🔵 WordPress
- 🔴 Laravel
- 🟡 PHP
- 🟢 HTML
- 🟣 Symfony
- 🟠 Drupal
- 🟤 Magento
- 🟦 JavaScript
- ⚪ Unknown

### Delete Site

Safe deletion of virtual hosts that:

- Removes virtual host configuration
- Removes hosts file entry
- Restarts Apache
- Preserves project files
- Updates site configuration

## Project Type Detection

The tool includes intelligent project type detection using the `LampSiteDetector` class.

### Supported Project Types

1. **WordPress**
   - Detects `wp-config.php`, `wp-content/`, `wp-admin/`
   - Handles WordPress multisite configurations

2. **Laravel**
   - Detects `artisan` file
   - Identifies `app/`, `config/`, `routes/` directories
   - Handles Laravel project structure

3. **Symfony**
   - Detects `composer.json` with Symfony dependencies
   - Identifies Symfony-specific directories

4. **Drupal**
   - Detects Drupal core files and structure
   - Identifies Drupal-specific directories

5. **Magento**
   - Detects Magento-specific files and structure
   - Identifies e-commerce platform indicators

6. **PHP**
   - Generic PHP project detection
   - Looks for `.php` files and PHP structure

7. **HTML**
   - Static HTML/CSS/JS projects
   - Detects HTML files and static assets

8. **JavaScript**
   - Node.js and JavaScript projects
   - Detects `package.json`, `node_modules/`

### Auto-Detection Process

1. **File System Analysis**: Scans project directory for framework indicators
2. **Composer Analysis**: Checks `composer.json` for framework dependencies
3. **Directory Structure**: Analyzes typical framework directory patterns
4. **File Patterns**: Looks for framework-specific files
5. **Fallback**: Defaults to "Unknown" if no pattern matches

## Domain Suffix Management

### Custom Domain Suffixes

The tool supports custom domain suffixes for local development:

- **Default**: `.test`
- **Common Options**: `.local`, `.dev`, `.test`, `.app`
- **Custom**: Any valid domain suffix

### Domain Suffix Features

1. **Validation**: Ensures proper domain format
2. **Persistence**: Saves configuration to `fe_lamp_site.json`
3. **Backward Compatibility**: Existing sites keep their current domains
4. **New Sites**: Use updated domain suffix

### Configuration Management

```bash
# Access domain suffix management
lamp_site_cli
# Choose option 6 (Manage domain suffix)

# Options available:
# 1) Change domain suffix
# 2) Reset to default (.local)
# 3) Show current configuration
# 0) Back to main menu
```

## Project Template Creation

### Supported Templates

1. **WordPress**
   - Downloads latest WordPress
   - Extracts to project directory
   - Sets up proper directory structure
   - Creates virtual host automatically

2. **Laravel**
   - Uses Composer to create Laravel project
   - Installs dependencies
   - Sets up proper directory structure
   - Creates virtual host automatically

3. **PHP**
   - Creates simple PHP project structure
   - Includes basic `index.php` with `phpinfo()`
   - Sets up document root

4. **HTML**
   - Creates static HTML project
   - Includes basic HTML structure
   - Sets up document root

### Template Creation Process

1. **Project Type Selection**: Choose from available templates
2. **Project Name**: Enter project name
3. **Directory Creation**: Creates project in `~/Sites/` directory
4. **Template Setup**: Downloads and configures template
5. **Virtual Host Creation**: Automatically creates virtual host
6. **Browser Launch**: Opens project in default browser

### Progress Indicators

The tool includes rich progress indicators for long-running operations:

- **Spinner**: Visual feedback during operations
- **Status Updates**: Clear descriptions of current operations
- **Error Handling**: Graceful handling of failures

## Status Monitoring

### Virtual Host Status Check

The status check provides comprehensive information about:

1. **Apache Configuration**
   - Config file existence and location
   - Virtual host module status
   - VHosts include status

2. **Configuration Files**
   - Apache config file status
   - Virtual host config file status
   - File permissions and accessibility

3. **Current Settings**
   - Apache port configuration
   - Document root location
   - Domain suffix settings

4. **Virtual Hosts Summary**
   - List of all configured virtual hosts
   - Status of each virtual host
   - Configuration health

### Status Indicators

- **✅ Green**: Component is properly configured
- **❌ Red**: Component is missing or misconfigured
- **⚠️ Yellow**: Component needs attention

## Configuration Management

### Configuration Files

1. **LAMP Configuration**: `/opt/fe_lamp/fe_lamp.json`
   - Apache port and document root
   - System configuration
   - Component information

2. **Site Configuration**: `/opt/fe_lamp/fe_lamp_site.json`
   - Site registry
   - Domain suffix settings
   - Site metadata

### Site Metadata

Each site stores comprehensive metadata:

```json
{
  "sites": {
    "mysite.test": {
      "name": "mysite",
      "domain": "mysite.test",
      "path": "/Users/username/Sites/mysite/public",
      "project_type": "Laravel",
      "description": "My Laravel project",
      "port": 8080,
      "created_at": "2024-01-15T10:30:00"
    }
  },
  "settings": {
    "domain_suffix": ".test",
    "port": 8080
  }
}
```

### Automatic Configuration

The tool automatically:

- Creates configuration files if missing
- Sets up virtual host functionality
- Enables Apache modules
- Configures hosts file entries
- Manages Apache restarts

## Troubleshooting

### Common Issues

#### 1. Sudo Permission Issues

```bash
# Error: Sudo access denied
# Solution: Ensure you have sudo privileges
sudo -v  # Test sudo access
```

#### 2. Apache Configuration Issues

```bash
# Error: Virtual host module not enabled
# Solution: Run status check and fix configuration
lamp_site_cli
# Choose option 5 (Check virtual host status)
```

#### 3. Project Path Issues

```bash
# Error: Path not found
# Solution: Ensure project directory exists
ls -la /path/to/project
```

#### 4. Domain Already Exists

```bash
# Error: Site already exists
# Solution: Choose different name or delete existing site
lamp_site_cli
# Choose option 3 (Delete site)
```

### Verification Commands

```bash
# Check Apache status
brew services list | grep httpd

# Check virtual host configuration
cat /opt/homebrew/etc/httpd/extra/httpd-vhosts.conf

# Check hosts file
cat /etc/hosts | grep 127.0.0.1

# Test Apache configuration
brew services info httpd
```

## Best Practices

### 1. Project Organization

```bash
# Recommended project structure
~/Sites/
├── my-wordpress-site/
│   └── public/          # WordPress files
├── my-laravel-app/
│   ├── app/
│   ├── public/          # Laravel public directory
│   └── artisan
└── my-html-site/
    └── public/          # HTML files
```

### 2. Domain Naming

```bash
# Good domain names
mysite.test
myapp.local
project.dev

# Avoid
mysite          # Missing suffix
my-site.test    # Hyphens can cause issues
my_site.test    # Underscores not recommended
```

### 3. Project Setup Workflow

1. **Create Project Directory**
   ```bash
   mkdir -p ~/Sites/myproject
   cd ~/Sites/myproject
   ```

2. **Set Up Project**
   ```bash
   # For Laravel
   composer create-project laravel/laravel public
   
   # For WordPress
   # Download and extract WordPress to public/
   ```

3. **Create Virtual Host**
   ```bash
   lamp_site_cli
   # Choose option 1 (Create new site)
   ```

### 4. Maintenance

```bash
# Regular status checks
lamp_site_cli
# Choose option 5 (Check virtual host status)

# List all sites
lamp_site_cli
# Choose option 2 (List existing sites)

# Clean up unused sites
lamp_site_cli
# Choose option 3 (Delete site)
```

### 5. Development Workflow

1. **Start LAMP Stack**
   ```bash
   lamp_cli start
   ```

2. **Create Development Site**
   ```bash
   lamp_site_cli
   # Choose option 1 (Create new site)
   ```

3. **Access Site**
   ```bash
   # Site automatically opens in browser
   # Or manually navigate to http://mysite.test:8080
   ```

4. **Development**
   - Edit files in project directory
   - Changes are immediately visible
   - No restart required

## Integration with LAMP CLI

The LAMP Site CLI works seamlessly with the main LAMP CLI:

### Prerequisites

```bash
# Ensure LAMP stack is installed and running
lamp_cli install
lamp_cli start
```

### Configuration Sharing

- Uses same Apache configuration
- Shares virtual host settings
- Integrates with LAMP status system

### Service Management

```bash
# Restart Apache after virtual host changes
lamp_cli restart

# Check overall LAMP status
lamp_cli status
```

## Advanced Features

### 1. Rich CLI Interface

- **Color-coded output**: Green for success, red for errors, yellow for warnings
- **Progress indicators**: Visual feedback during long operations
- **Interactive prompts**: User-friendly input collection
- **Panel displays**: Organized information presentation

### 2. Error Handling

- **Graceful failures**: Clear error messages and recovery suggestions
- **Validation**: Input validation and path checking
- **Rollback**: Automatic cleanup on failures

### 3. Performance Optimizations

- **Caching**: Virtual host content caching to avoid repeated file reads
- **Efficient operations**: Batched file operations
- **Progress feedback**: User-friendly progress indicators

### 4. Security

- **Sudo validation**: Proper permission checking
- **Safe operations**: Backup creation before modifications
- **Input sanitization**: Validation of user inputs

## Notes

- All virtual host changes require Apache restart to take effect
- The tool automatically handles backup creation before making changes
- Project files are never deleted during site deletion
- Configuration is automatically saved and persisted
- The tool works with both bundled and source environments
- Rich CLI interface provides excellent user experience
- Comprehensive error handling and validation
- Seamless integration with LAMP CLI ecosystem
