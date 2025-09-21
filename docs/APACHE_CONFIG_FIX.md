# Apache Configuration Fix

## 🚨 **Problem Identified**

When deleting virtual hosts, users encountered the following error:

```
httpd: Syntax error on line 694 of /Applications/MAMP/conf/apache/httpd.conf: 
Could not open configuration file /Applications/MAMP/Library/conf/extra/httpd-vhosts.conf: 
No such file or directory
```

## 🔍 **Root Cause Analysis**

### **Issue**
The Apache configuration file (`/Applications/MAMP/conf/apache/httpd.conf`) can have several problematic states:

1. **Commented Out (Disabled)**:
```apache
#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
```

2. **Incorrect Relative Path**:
```apache
Include conf/extra/httpd-vhosts.conf
```

3. **Commented Relative Path**:
```apache
#Include conf/extra/httpd-vhosts.conf
```

### **Problems**
- **Commented Out**: Virtual host functionality is disabled
- **Relative Path**: `conf/extra/httpd-vhosts.conf` resolves to wrong location
- **Wrong Base Directory**: Apache resolves relative paths to `/Applications/MAMP/Library/conf/`
- **File Location**: The actual file is at `/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf`
- **Result**: Apache cannot find the file or virtual hosts are disabled

### **Correct Configuration**
The include statement should be active and use an absolute path:

```apache
Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
```

## 🛠️ **Solution Implemented**

### **1. Fix Script Created**
- **File**: `fix_apache_config.sh`
- **Purpose**: Automatically fix the Apache configuration path
- **Features**:
  - Backup original configuration
  - Fix include path
  - Validate Apache configuration
  - Provide clear feedback

### **2. Enhanced Error Handling**
Updated both `create_virtualhost()` and `delete_virtualhost()` functions to:

- **Detect Specific Error**: Check for Apache configuration errors
- **Provide Clear Guidance**: Show exact fix command
- **User-Friendly Messages**: Explain the problem and solution

### **3. Comprehensive Module Enablement**
Updated `enable_vhost_module()` function that:

- **Handles All States**: Covers commented, incorrect, and missing configurations
- **Smart Detection**: Identifies specific configuration issues
- **Automatic Fixes**: Enables commented configs, fixes paths, adds missing includes
- **Backup Safety**: Creates timestamped backups before changes
- **Validation**: Tests Apache configuration after changes

### **4. Configuration Check Function**
Added `check_apache_config()` function that:

- **Detects Commented Out Config**: Checks for `#Include` statements (disabled)
- **Validates Include Path**: Checks for correct/incorrect paths
- **Handles Multiple States**: Covers all possible configuration states
- **Provides Fix Instructions**: Shows how to resolve issues
- **Integrated with Status Check**: Part of virtual host status monitoring

### **5. Enhanced Module Detection**
Updated `check_vhost_module_enabled()` function that:

- **Line-by-Line Analysis**: Parses Apache config line by line
- **Comment Detection**: Distinguishes between active and commented statements
- **Accurate Status**: Returns true only when both module and include are active
- **Consistent Logic**: Matches the detection logic in `check_apache_config()`

## 📋 **How to Fix**

### **Automatic Fix (Recommended)**
```bash
# Run the fix script
./fix_apache_config.sh
```

### **Manual Fix**
```bash
# Create backup
sudo cp /Applications/MAMP/conf/apache/httpd.conf /Applications/MAMP/conf/apache/httpd.conf.backup

# Fix the include path
sudo sed -i '' 's|Include conf/extra/httpd-vhosts.conf|Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf|' /Applications/MAMP/conf/apache/httpd.conf

# Test Apache configuration
sudo /Applications/MAMP/bin/apache2/bin/apachectl configtest

# Restart MAMP
```

## 🔧 **Fix Script Details**

### **Script Features**
```bash
#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Fix Apache Configuration Script
# ==============================
# Fixes the incorrect path to httpd-vhosts.conf in Apache configuration
# ==============================
```

### **What the Script Does**
1. **Check Files**: Verifies Apache config and vhost config exist
2. **Detect Issues**: Looks for all possible configuration problems:
   - Commented out absolute path (disabled)
   - Commented out relative path (disabled)
   - Incorrect relative path (enabled but wrong)
   - Missing include statement
3. **Create Backup**: Backs up original configuration with timestamp
4. **Fix Configuration**: 
   - Enables commented out configurations
   - Fixes incorrect paths
   - Adds missing include statements
5. **Validate**: Tests Apache configuration
6. **Provide Feedback**: Clear success/error messages

### **Script Output Examples**

**Example 1: Commented Out Configuration**
```
🔧 Fixing Apache Configuration...

📋 Current configuration:
  Apache Config: /Applications/MAMP/conf/apache/httpd.conf
  VHost Config: /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf

🔍 Checking current include statement...
⚠️ Found commented out virtual host configuration
Found: #Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
💾 Creating backup...
🔧 Enabling virtual host configuration...
✅ Virtual host configuration enabled
🔍 Verifying final configuration...
✅ Virtual host configuration is now correct
🧪 Testing Apache configuration...
✅ Apache configuration is valid

🎉 Apache configuration fixed successfully!
```

**Example 2: Incorrect Relative Path**
```
🔧 Fixing Apache Configuration...

📋 Current configuration:
  Apache Config: /Applications/MAMP/conf/apache/httpd.conf
  VHost Config: /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf

🔍 Checking current include statement...
⚠️ Found incorrect relative path: Include conf/extra/httpd-vhosts.conf
💾 Creating backup...
🔧 Fixing include path...
✅ Fixed include path to absolute path
🔍 Verifying final configuration...
✅ Virtual host configuration is now correct
🧪 Testing Apache configuration...
✅ Apache configuration is valid

🎉 Apache configuration fixed successfully!
```

## 🚀 **Enhanced Error Messages**

### **Before Fix**
```
❌ Failed to update hosts file or restart Apache: Command '['sudo', 'sh', '-c', "sed -i '' '/127.0.0.1 test\\.yen/d' /etc/hosts && /Applications/MAMP/bin/apache2/bin/apachectl -k restart"]' returned non-zero exit status 1.
Please ensure you have sudo privileges
```

### **After Fix**
```
❌ Failed to update hosts file or restart Apache: Command '['sudo', 'sh', '-c', "sed -i '' '/127.0.0.1 test\\.yen/d' /etc/hosts && /Applications/MAMP/bin/apache2/bin/apachectl -k restart"]' returned non-zero exit status 1.

⚠️ Apache configuration error detected!
The Apache config is looking for httpd-vhosts.conf in the wrong location.
💡 To fix this issue, run:
   ./fix_apache_config.sh
This will fix the Apache configuration path.
```

## 🔍 **Configuration Check Integration**

### **Virtual Host Status Check**
The `check_vhost_status()` function now includes Apache configuration validation:

**Example 1: Commented Out Configuration**
```
🔍 Virtual Host Status Check

Apache Config: /Applications/MAMP/conf/apache/httpd.conf
  Status: ✅ Exists

🔍 Checking Apache Configuration...
⚠️ Virtual host configuration is commented out (disabled)
Found: #Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
💡 To enable virtual hosts, run:
   ./fix_apache_config.sh

Virtual Host Config: /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
  Status: ✅ Exists
```

**Example 2: Incorrect Relative Path**
```
🔍 Virtual Host Status Check

Apache Config: /Applications/MAMP/conf/apache/httpd.conf
  Status: ✅ Exists

🔍 Checking Apache Configuration...
⚠️ Found incorrect relative path in Apache config
Current: Include conf/extra/httpd-vhosts.conf
Should be: Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
💡 To fix this, run:
   ./fix_apache_config.sh

Virtual Host Config: /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
  Status: ✅ Exists
```

## 📊 **Technical Details**

### **File Locations**
- **Apache Config**: `/Applications/MAMP/conf/apache/httpd.conf`
- **VHost Config**: `/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf`
- **Apache Binary**: `/Applications/MAMP/bin/apache2/bin/apachectl`

### **Include Statement Fix**
```bash
# Before (incorrect)
Include conf/extra/httpd-vhosts.conf

# After (correct)
Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf
```

### **Backup Strategy**
```bash
# Backup with timestamp
sudo cp /Applications/MAMP/conf/apache/httpd.conf /Applications/MAMP/conf/apache/httpd.conf.backup.$(date +%Y%m%d_%H%M%S)
```

## 🎯 **Prevention**

### **Configuration Validation**
- **Startup Check**: Validate Apache config on tool startup
- **Status Monitoring**: Regular configuration checks
- **Error Detection**: Specific error message handling

### **User Education**
- **Clear Messages**: Explain what went wrong
- **Fix Instructions**: Provide exact commands to resolve
- **Documentation**: Comprehensive troubleshooting guide

## 🔮 **Future Improvements**

### **Planned Enhancements**
- **Auto-Fix**: Automatically fix common configuration issues
- **Config Validation**: More comprehensive Apache config checking
- **MAMP Detection**: Better MAMP installation detection
- **Path Resolution**: Automatic path resolution for different MAMP versions

### **Potential Features**
- **Config Backup**: Automatic configuration backup before changes
- **Rollback**: Easy rollback to previous configurations
- **Multiple MAMP**: Support for multiple MAMP installations
- **Version Detection**: Automatic MAMP version detection and path adjustment

## 📝 **Troubleshooting**

### **Common Issues**
1. **Permission Denied**: Ensure sudo privileges
2. **File Not Found**: Verify MAMP installation path
3. **Config Test Fails**: Check for other Apache configuration errors
4. **Backup Failed**: Ensure write permissions to config directory

### **Recovery Steps**
```bash
# If fix fails, restore from backup
sudo cp /Applications/MAMP/conf/apache/httpd.conf.backup.* /Applications/MAMP/conf/apache/httpd.conf

# Test configuration
sudo /Applications/MAMP/bin/apache2/bin/apachectl configtest

# Restart MAMP
```

## ✅ **Verification**

### **Test Steps**
1. **Run Fix Script**: `./fix_apache_config.sh`
2. **Check Status**: Use option 5 in FE Local CLI
3. **Test Operations**: Create/delete virtual hosts
4. **Verify Apache**: Check Apache error logs

### **Success Indicators**
- ✅ Apache configuration test passes
- ✅ Virtual host operations work without errors
- ✅ No "Could not open configuration file" errors
- ✅ MAMP starts without configuration warnings
