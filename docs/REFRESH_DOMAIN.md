# 🔄 Refresh Domain Configuration

This document outlines the refresh domain functionality that allows users to update virtual host configuration when project types change.

## 🆕 New Feature

### **Refresh Domain Configuration** ✅ IMPLEMENTED

**Function:** `refresh_domain()`

**Purpose:**
- Allows users to refresh domain configuration when project type changes
- Provides helpful information based on detected project type
- Useful when converting projects (e.g., from WordPress to Laravel)
- No actual virtual host configuration changes needed - mainly informational

**Use Cases:**
- **Project Migration**: When converting from WordPress to Laravel
- **Project Type Change**: When adding/removing framework files
- **Configuration Verification**: To verify current project type detection
- **Troubleshooting**: To get project-specific guidance

## 🔧 Technical Implementation

### Function Overview

```python
def refresh_domain():
    """Refresh domain configuration to detect new project type."""
    console.print("[blue]🔄 Refresh Domain Configuration[/blue]")
    console.print("[cyan]This will update the virtual host configuration to reflect any changes in your project type.[/cyan]")
    
    # List current domains for user to choose from
    # Display available domains with current project types
    # Get user selection
    # Detect current project type
    # Provide helpful information based on project type
```

### Key Features

**1. Domain Selection:**
- Lists all available `.yen` domains
- Shows current project type and port for each domain
- Numbered selection for easy choice

**2. Project Type Detection:**
- Uses existing `detect_project_type()` function
- Supports WordPress, Laravel, PHP, HTML, and Unknown types
- Real-time detection based on current file structure

**3. Helpful Guidance:**
- Provides project-specific recommendations
- Includes setup and configuration tips
- Covers common troubleshooting steps

## 🎯 User Experience

### Workflow

1. **Access**: Menu option 7 - "Refresh domain configuration"
2. **Domain List**: View all available domains with current types
3. **Selection**: Choose domain to refresh (numbered list)
4. **Confirmation**: Confirm refresh operation
5. **Information**: Receive project-specific guidance

### Example Session

```
🔄 Refresh Domain Configuration
This will update the virtual host configuration to reflect any changes in your project type.

Available domains:
1) test.yen :8888 🟢 HTML
    📁 /Users/lequang/Documents/Woks/test

2) mysite.yen :8888 🔵 WordPress
    📁 /Users/lequang/Documents/Woks/mysite

Select domain to refresh (1-2): 1

Current project type: HTML
Refresh configuration for test.yen? [y/N]: y

🔄 Refreshing configuration for test.yen...
✅ Configuration refreshed for test.yen :8888
📁 Project path: /Users/lequang/Documents/Woks/test
🔍 Detected type: HTML

💡 Static HTML detected:
   • Ensure index.html or index.php exists
   • Check file permissions
```

## 📋 Project-Specific Guidance

### WordPress Projects 🔵

**When WordPress is detected:**
```
💡 WordPress detected:
   • Ensure wp-config.php is properly configured
   • Check database connection settings
   • Verify file permissions (755 for directories, 644 for files)
```

**Use Cases:**
- After WordPress installation
- When troubleshooting WordPress issues
- When verifying WordPress configuration

### Laravel Projects 🔴

**When Laravel is detected:**
```
💡 Laravel detected:
   • Run 'composer install' if dependencies are missing
   • Check .env file configuration
   • Ensure storage and bootstrap/cache directories are writable
```

**Use Cases:**
- After Laravel installation
- When converting from other frameworks
- When troubleshooting Laravel issues

### PHP Projects 🟡

**When PHP is detected:**
```
💡 PHP project detected:
   • Check PHP version compatibility
   • Verify file permissions
```

**Use Cases:**
- Custom PHP applications
- Simple PHP scripts
- PHP-based APIs

### HTML Projects 🟢

**When HTML is detected:**
```
💡 Static HTML detected:
   • Ensure index.html or index.php exists
   • Check file permissions
```

**Use Cases:**
- Static websites
- HTML prototypes
- Simple landing pages

### Unknown Projects ⚪

**When project type is unknown:**
```
💡 Unknown project type:
   • Check if project files are properly organized
   • Verify the project structure
```

**Use Cases:**
- New projects
- Unusual project structures
- Troubleshooting detection issues

## 🚀 Benefits

### For Users:
- ✅ **Project Type Awareness**: Always know what type of project you're working with
- ✅ **Migration Support**: Easy verification when converting between frameworks
- ✅ **Troubleshooting**: Get project-specific guidance and tips
- ✅ **Configuration Verification**: Ensure project type detection is accurate

### For Developers:
- ✅ **Framework Transitions**: Smooth migration between different frameworks
- ✅ **Project Management**: Better understanding of project structure
- ✅ **Debugging**: Quick identification of project-specific issues
- ✅ **Best Practices**: Receive framework-specific recommendations

## 🔍 Advanced Features

### Error Handling
- **No Domains**: Graceful handling when no `.yen` sites exist
- **Invalid Selection**: Clear error messages for invalid choices
- **Missing Paths**: Proper handling of inaccessible directories
- **Cancellation**: Easy cancellation with Ctrl+C

### Integration
- **Existing Functions**: Leverages `get_domain_path()`, `get_domain_port()`, and `detect_project_type()`
- **Consistent UI**: Uses same styling and patterns as other functions
- **Menu Integration**: Seamlessly integrated into main menu system

## 🎉 Ready for Production

The refresh domain functionality provides:
- ✅ **Project Type Verification** for accurate detection
- ✅ **Helpful Guidance** based on detected project types
- ✅ **Easy Migration Support** for framework transitions
- ✅ **Troubleshooting Assistance** with project-specific tips
- ✅ **Professional User Experience** with clear feedback

This feature makes the FE Local CLI tool much more helpful for managing different types of web projects! 🚀
