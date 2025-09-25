# LAMP CLI Features Documentation

This comprehensive document covers all the features and capabilities of the LAMP CLI tool.

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [mod_rewrite Features](#mod_rewrite-features)
4. [VirtualHost mod_rewrite Features](#virtualhost-mod_rewrite-features)
5. [Database Export Features](#database-export-features)
6. [Performance Optimizations](#performance-optimizations)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Overview

The LAMP CLI is a comprehensive tool for managing LAMP stack components on macOS via Homebrew. It provides:

- **Installation & Configuration**: Automated setup of Apache, PHP, MySQL/MariaDB, and phpMyAdmin
- **Service Management**: Start, stop, restart LAMP services
- **Database Management**: Import, export, and manage databases
- **Apache Configuration**: Port management, document root, mod_rewrite support
- **VirtualHost Management**: Create, update, delete virtual hosts
- **Status Monitoring**: Check installation and service status

## Core Features

### Installation & Setup

```bash
# Install LAMP stack
lamp_cli install

# Install with specific database
lamp_cli install --db mariadb

# Check installation status
lamp_cli status
```

### Service Management

```bash
# Start all services
lamp_cli start

# Stop all services
lamp_cli stop

# Restart all services
lamp_cli restart
```

### Apache Configuration

```bash
# Configure Apache port and document root
lamp_cli configure-apache --port 80 --doc-root /var/www

# Show current Apache configuration
lamp_cli show-apache-config
```

### Database Management

```bash
# Import database
lamp_cli import-database backup.sql mydb

# Export databases (see Database Export Features section)
lamp_cli export-databases

# Test MySQL connection
lamp_cli test-mysql
```

## mod_rewrite Features

The LAMP CLI includes comprehensive mod_rewrite support for Apache.

### Automatic Enablement

When you run `lamp_cli install`, mod_rewrite is automatically enabled for Apache:
- The `rewrite_module` is loaded
- `AllowOverride` is set to `All` to allow `.htaccess` files
- Your websites can use URL rewriting rules

### Manual Management

#### Enable mod_rewrite
```bash
lamp_cli enable-mod-rewrite
```

#### Disable mod_rewrite
```bash
lamp_cli disable-mod-rewrite
```

#### Check mod_rewrite Status
```bash
lamp_cli check-rewrite-status
```

### Technical Details

When mod_rewrite is enabled, the following changes are made to Apache configuration:

1. **LoadModule Directive**:
   ```apache
   LoadModule rewrite_module lib/httpd/modules/mod_rewrite.so
   ```

2. **AllowOverride Setting**:
   ```apache
   AllowOverride All
   ```

3. **Directory Block**:
   ```apache
   <Directory "/opt/homebrew/var/www">
       AllowOverride All
   </Directory>
   ```

### Common Use Cases

1. **WordPress**: Requires mod_rewrite for pretty permalinks
2. **Laravel**: Uses mod_rewrite for clean URLs
3. **Custom Applications**: URL rewriting for SEO-friendly URLs
4. **API Endpoints**: RESTful URL structures

## VirtualHost mod_rewrite Features

The LampVHostManager class provides VirtualHost-level mod_rewrite management.

### Features

#### Enable mod_rewrite for all VirtualHost blocks
```python
from lamp_vhost_manager import LampVHostManager

vhost_manager = LampVHostManager("/opt/homebrew/etc/httpd/extra/httpd-vhosts.conf")
vhost_manager.enable_mod_rewrite()
```

#### Disable mod_rewrite for all VirtualHost blocks
```python
vhost_manager.disable_mod_rewrite()
```

#### Check mod_rewrite status
```python
status = vhost_manager.get_rewrite_status()
print(f"mod_rewrite enabled: {status['enabled']}")
print(f"Domains with rewrite: {status['blocks_with_rewrite']}")
```

### Status Tracking

The system automatically tracks mod_rewrite status in JSON format:

```json
{
  "enabled": true,
  "blocks_with_rewrite": ["example.com", "test.local"],
  "total_blocks": 3,
  "status_file": "/opt/fe_lamp/vhost_rewrite_status.json",
  "timestamp": "2024-01-15T10:30:00",
  "last_updated": "2024-01-15T10:30:00"
}
```

### VirtualHost Configuration

When mod_rewrite is enabled for VirtualHost blocks:

```apache
<VirtualHost *:8080>
    DocumentRoot "/var/www/example"
    ServerName example.com
    RewriteEngine On
    
    <Directory "/var/www/example">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

## Database Export Features

The LAMP CLI includes comprehensive database export capabilities.

### Export All Databases

```bash
# Export all databases (compressed by default)
lamp_cli export-databases

# Export all databases to specific directory
lamp_cli export-databases --output-dir /path/to/backups

# Export schema only (no data)
lamp_cli export-databases --schema-only

# Export without compression
lamp_cli export-databases --no-compress
```

### Export Single Database

```bash
# Export specific database
lamp_cli export-databases --database myapp

# Export specific database schema only
lamp_cli export-databases --database myapp --schema-only

# Export to custom directory
lamp_cli export-databases --database myapp --output-dir /backups
```

### Advanced Options

#### Connection Parameters
```bash
# Use custom database credentials
lamp_cli export-databases --user myuser --password mypass

# Use default credentials (root/fe_root)
lamp_cli export-databases
```

#### Output Options
```bash
# Custom output directory
lamp_cli export-databases --output-dir /opt/backups/databases

# Disable compression (output .sql files)
lamp_cli export-databases --no-compress

# Schema only export
lamp_cli export-databases --schema-only
```

### Technical Details

#### File Naming Convention
- **With compression**: `{database_name}_{timestamp}.sql.gz`
- **Without compression**: `{database_name}_{timestamp}.sql`

Example: `myapp_20240115_143022.sql.gz`

#### Compression Benefits
- **File Size**: Typically 70-90% reduction in file size
- **Transfer Speed**: Faster upload/download for remote backups
- **Storage**: Significant disk space savings
- **Network**: Reduced bandwidth usage for remote transfers

#### System Database Exclusion
The export process automatically excludes system databases:
- `information_schema`
- `performance_schema`
- `mysql`
- `sys`

Only user-created databases are exported.

### Usage Examples

#### Basic Workflow
```bash
# 1. Export all databases with default settings
lamp_cli export-databases

# 2. Check exported files
ls -la ./db_exports/

# 3. Export specific database
lamp_cli export-databases --database wordpress_site
```

#### Backup Strategy
```bash
# Full backup with compression
lamp_cli export-databases --output-dir /backups/full

# Schema-only backup for development
lamp_cli export-databases --schema-only --output-dir /backups/schema

# Specific application backup
lamp_cli export-databases --database myapp --output-dir /backups/apps
```

## Performance Optimizations

The LAMP CLI includes several performance optimizations:

### 1. Efficient File Operations
- Cached file content with modification time tracking
- Reduced redundant file reads
- Optimized directory scanning

### 2. Optimized Subprocess Calls
- Batched operations using single shell commands
- Reduced process creation overhead
- Efficient command execution

### 3. Smart VirtualHost Management
- Regex-based removal with optimized file operations
- Efficient string manipulation
- Minimal memory usage

### 4. Progress Indicators
- Rich progress indicators for long-running operations
- Clear feedback on operation status
- Better user experience

## Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Ensure output directory is writable
mkdir -p /path/to/backups
chmod 755 /path/to/backups
```

#### 2. Database Connection Failed
```bash
# Check MySQL service
lamp_cli status

# Start MySQL if needed
lamp_cli start
```

#### 3. No Databases Found
```bash
# Check if databases exist
mysql -u root -p -e "SHOW DATABASES;"
```

#### 4. mod_rewrite Not Working
```bash
# Check mod_rewrite status
lamp_cli check-rewrite-status

# Re-enable if disabled
lamp_cli enable-mod-rewrite

# Restart Apache after changes
lamp_cli restart
```

### Verification Commands

```bash
# Check exported files
ls -la ./db_exports/

# Verify compressed files
file ./db_exports/*.sql.gz

# Test decompression
gunzip -t ./db_exports/myapp_20240115_143022.sql.gz

# Check Apache configuration
lamp_cli show-apache-config

# Check service status
lamp_cli status
```

## Best Practices

### 1. Regular Backups
```bash
# Daily backup script
lamp_cli export-databases --output-dir /backups/daily/$(date +%Y%m%d)
```

### 2. Development Setup
```bash
# Export schema for new developers
lamp_cli export-databases --schema-only --output-dir ./dev_schema
```

### 3. Application Migration
```bash
# Export specific application database
lamp_cli export-databases --database myapp --output-dir /migration/backups
```

### 4. Testing Environment
```bash
# Export test database
lamp_cli export-databases --database test_db --no-compress
```

### 5. Service Management
```bash
# Always restart Apache after configuration changes
lamp_cli restart

# Check status before making changes
lamp_cli status
```

### 6. mod_rewrite Management
```bash
# Enable mod_rewrite for new projects
lamp_cli enable-mod-rewrite

# Check status regularly
lamp_cli check-rewrite-status
```

## Integration Notes

- **Installation**: mod_rewrite is automatically enabled during `lamp_cli install`
- **Apache Configuration**: Works alongside existing Apache port and document root configuration
- **Service Management**: Use `lamp_cli restart` after enabling/disabling mod_rewrite
- **Status Checking**: Integrated with the overall LAMP status system
- **Backup System**: All configuration changes are automatically backed up before modification
- **Error Handling**: Comprehensive error handling with clear feedback messages

## Notes

- All configuration changes are automatically backed up before modification
- Backup files are created with timestamps: `httpd.conf.YYYYMMDD-HHMMSS.bak`
- Original configurations can be restored if needed
- mod_rewrite changes require Apache restart to take effect
- Export process creates output directory if it doesn't exist
- Timestamps are in format: YYYYMMDD_HHMMSS
- All operations use the same MySQL connection parameters as other LAMP CLI commands
- Exported files maintain database integrity and can be safely imported
- Compression is applied after successful export to avoid data loss
