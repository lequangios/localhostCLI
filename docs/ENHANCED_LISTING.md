# 📋 Enhanced Virtual Host Listing

This document outlines the enhanced virtual host listing functionality that displays project type information for each domain.

## 🆕 New Features

### 1. **Project Type Detection** ✅ IMPLEMENTED

**Function:** `get_domain_path(domain: str) -> Optional[Path]`

**Purpose:**
- Extracts the document root path for each virtual host domain
- Uses robust block-by-block parsing to handle complex Apache configurations
- Supports both port 80 and 8888 virtual host configurations

**Technical Implementation:**
```python
def get_domain_path(domain: str) -> Optional[Path]:
    """Get the document root path for a domain from vhost config."""
    content = get_vhost_content()
    if not content:
        return None
    
    # Find all VirtualHost blocks and check each one
    vhost_blocks = re.findall(r'<VirtualHost[^>]*>.*?</VirtualHost>', content, re.DOTALL)
    
    for block in vhost_blocks:
        # Check if this block contains our domain
        if re.search(rf'ServerName\s+{re.escape(domain)}', block):
            # Extract DocumentRoot from this block
            docroot_match = re.search(r'DocumentRoot\s+"([^"]+)"', block)
            if docroot_match:
                return Path(docroot_match.group(1))
    
    return None
```

### 2. **Enhanced Listing Display** ✅ IMPLEMENTED

**Function:** `list_virtualhosts()`

**Features:**
- **Project Type Detection**: Automatically detects WordPress, Laravel, PHP, or HTML projects
- **Visual Indicators**: Uses emojis to represent different project types
- **Path Information**: Shows the document root path for each domain
- **Error Handling**: Gracefully handles missing paths or inaccessible directories

**Display Format:**
```
📋 Registered .yen sites:
• test.yen :8888 🟢 HTML
  📁 /Users/lequang/Documents/Woks/test

• mysite.yen :8888 🔵 WordPress
  📁 /Users/lequang/Documents/Woks/mysite/public

• api.yen :8080 🔴 Laravel
  📁 /Users/lequang/Documents/Woks/api/public
```

### 3. **Port Display** ✅ IMPLEMENTED

**Function:** `get_domain_port(domain: str) -> Optional[int]`

**Purpose:**
- Extracts the port number for each virtual host domain
- Uses the same robust block-by-block parsing approach
- Supports different port configurations (80, 8080, 8888, etc.)

**Technical Implementation:**
```python
def get_domain_port(domain: str) -> Optional[int]:
    """Get the port number for a domain from vhost config."""
    content = get_vhost_content()
    if not content:
        return None
    
    # Find all VirtualHost blocks and check each one
    vhost_blocks = re.findall(r'<VirtualHost[^>]*>.*?</VirtualHost>', content, re.DOTALL)
    
    for block in vhost_blocks:
        # Check if this block contains our domain
        if re.search(rf'ServerName\s+{re.escape(domain)}', block):
            # Extract port from VirtualHost tag
            port_match = re.search(r'<VirtualHost[^>]*:(\d+)', block)
            if port_match:
                return int(port_match.group(1))
    
    return None
```

**Features:**
- **Port Extraction**: Extracts port from `<VirtualHost *:PORT>` tags
- **Error Handling**: Returns `None` if port cannot be determined
- **Display Format**: Shows port as `:PORT` or `:?` if unknown

### 4. **Project Type Classification** ✅ IMPLEMENTED

**Detection Logic:**
- **WordPress** 🔵: Detects `wp-config.php` or `wp-content` directory
- **Laravel** 🔴: Detects `artisan` file or Laravel dependencies in `composer.json`
- **PHP** 🟡: Detects any `.php` files in the directory
- **HTML** 🟢: Detects `.html` or `.htm` files
- **Unknown** ⚪: Fallback for unrecognized project types

**Emoji Mapping:**
```python
type_emoji = {
    'WordPress': '🔵',
    'Laravel': '🔴', 
    'PHP': '🟡',
    'HTML': '🟢',
    'Unknown': '⚪'
}.get(project_type, '⚪')
```

## 🔧 Technical Implementation

### Robust Virtual Host Parsing

**Challenge:**
- Apache virtual host configurations can have complex structures
- Multiple virtual hosts with different port configurations
- DocumentRoot and ServerName can appear in different orders

**Solution:**
- **Block-by-Block Parsing**: Extract all VirtualHost blocks first
- **Domain Matching**: Check each block for the target domain
- **Path Extraction**: Extract DocumentRoot from the matching block

**Benefits:**
- ✅ **Handles Complex Configs**: Works with any Apache virtual host structure
- ✅ **Port Agnostic**: Supports both port 80 and 8888 configurations
- ✅ **Order Independent**: Works regardless of directive order
- ✅ **Error Resilient**: Gracefully handles malformed configurations

### Integration Points

1. **Menu Option 3**: Enhanced listing in main menu
2. **Virtual Host Status**: Also used in option 5 status display
3. **Caching**: Leverages existing vhost content caching for performance

## 🎯 User Experience

### Before Enhancement:
```
📋 Registered .yen sites:
• test.yen
• mysite.yen
• api.yen
```

### After Enhancement:
```
📋 Registered .yen sites:
• test.yen :8888 🟢 HTML
  📁 /Users/lequang/Documents/Woks/test

• mysite.yen :8888 🔵 WordPress
  📁 /Users/lequang/Documents/Woks/mysite/public

• api.yen :8080 🔴 Laravel
  📁 /Users/lequang/Documents/Woks/api/public
```

## 🧪 Testing Results

### Test Case: test.yen
```
✅ Found domain test.yen in block 3
✅ DocumentRoot: /Users/lequang/Documents/Woks/test
Path exists: True
PHP files: 0
HTML files: 1
First HTML file: /Users/lequang/Documents/Woks/test/index.html
```

**Result:** `• test.yen 🟢 HTML`

### Error Handling
- **Missing Path**: `• domain.yen ⚠️ Path not found`
- **Inaccessible Directory**: Graceful fallback to "Unknown" type
- **No Virtual Hosts**: `❌ No .yen sites found.`

## 🚀 Benefits

### For Users:
- ✅ **Quick Identification**: Instantly see what type of project each domain hosts
- ✅ **Path Information**: Know exactly where each project is located
- ✅ **Port Information**: See which port each domain is using
- ✅ **Visual Clarity**: Emoji indicators make scanning easier
- ✅ **Error Awareness**: Clear indication when paths are missing

### For Developers:
- ✅ **Project Management**: Easy overview of all hosted projects
- ✅ **Debugging**: Quickly identify project types and locations
- ✅ **Maintenance**: Know which projects need attention
- ✅ **Organization**: Better understanding of development environment

## 🔍 Advanced Features

### Smart Detection
- **WordPress**: Checks for both `wp-config.php` and `wp-content` directory
- **Laravel**: Validates `composer.json` content for Laravel dependencies
- **PHP**: Counts PHP files for accurate detection
- **HTML**: Supports both `.html` and `.htm` extensions

### Performance Optimization
- **Caching**: Reuses existing vhost content cache
- **Efficient Parsing**: Single-pass block extraction
- **Lazy Evaluation**: Only processes domains that exist

## 🎉 Ready for Production

The enhanced listing feature provides:
- ✅ **Comprehensive Information** about each virtual host
- ✅ **Visual Project Classification** with emoji indicators
- ✅ **Robust Error Handling** for edge cases
- ✅ **Performance Optimized** with caching and efficient parsing
- ✅ **User-Friendly Display** with clear formatting

This enhancement makes the MPHM CLI tool much more informative and useful for managing multiple development projects! 🚀
