# 🐛 Bug Fixes

This document outlines the bugs that were identified and fixed in the MPHM CLI tool.

## 🔧 Fixed Issues

### 1. **MAMP Detection Bug** ✅ FIXED

**Problem:**
- The `check_mamp_installed()` function was incorrectly checking `APACHE_RESTART` as a file path
- `APACHE_RESTART` was a command string (`/Applications/MAMP/bin/apache2/bin/apachectl -k restart`), not a file path
- This caused `Path(APACHE_RESTART).exists()` to always return `False`

**Root Cause:**
```python
# BEFORE (Buggy)
VHOST_CONF = "/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
APACHE_RESTART = "/Applications/MAMP/bin/apache2/bin/apachectl -k restart"

def check_mamp_installed():
    if not Path(VHOST_CONF).exists() or not Path(APACHE_RESTART).exists():  # ❌ BUG!
        # APACHE_RESTART is a command, not a file path
```

**Solution:**
```python
# AFTER (Fixed)
VHOST_CONF = "/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
APACHE_BINARY = "/Applications/MAMP/bin/apache2/bin/apachectl"  # ✅ File path
APACHE_RESTART = f"{APACHE_BINARY} -k restart"  # ✅ Command string

def check_mamp_installed():
    vhost_exists = Path(VHOST_CONF).exists()
    apache_exists = Path(APACHE_BINARY).exists()  # ✅ Check actual binary
    
    if not vhost_exists or not apache_exists:
        # Proper error handling with detailed messages
```

**Additional Improvements:**
- Added executable permission check for Apache binary
- Better error messages showing which components are missing
- More robust file existence validation

### 2. **Build Path Issues** ✅ FIXED

**Problem:**
- Hardcoded paths in PyInstaller builds could cause issues
- Binary was not being rebuilt when source code changed

**Solution:**
- Fixed path handling in the build process
- Added `--force` flag to build script for forced rebuilds
- Improved build caching to avoid unnecessary rebuilds

## 🧪 Testing

### Before Fix:
```bash
$ ./bin/mphm
❌ MAMP not found! Please ensure MAMP is installed in /Applications/MAMP
```

### After Fix:
```bash
$ ./bin/mphm
╭───────────────────────╮
│ MAMP HOST TOOL (.yen) │
╰───────────────────────╯
1) Create new site
2) Delete site
3) List existing sites
4) Create sample WordPress/Laravel project
0) Exit
Choose an option [0/1/2/3/4]:
```

## 🔍 Debug Process

1. **Identified the Issue:**
   - Binary was failing MAMP detection even though MAMP was installed
   - Debug output showed paths were correct but detection was failing

2. **Root Cause Analysis:**
   - Traced the issue to `check_mamp_installed()` function
   - Found that `APACHE_RESTART` was being treated as a file path instead of a command

3. **Solution Implementation:**
   - Separated file path (`APACHE_BINARY`) from command string (`APACHE_RESTART`)
   - Added proper file existence checks
   - Enhanced error reporting

4. **Verification:**
   - Rebuilt binary with `--force` flag
   - Tested MAMP detection successfully
   - Verified all functionality works correctly

## 📋 Prevention Measures

1. **Code Review:**
   - Always verify that file paths are actual file paths, not command strings
   - Use descriptive variable names that clearly indicate their purpose

2. **Testing:**
   - Test binary builds after any path-related changes
   - Verify functionality on clean systems

3. **Documentation:**
   - Document the purpose of each path variable
   - Include examples of expected values

### 2. **Permission Issues in Virtual Host Operations** ✅ FIXED

**Problem:**
- The `create_virtualhost()` and `delete_virtualhost()` functions were getting stuck
- Functions were trying to write directly to protected system files without proper permissions
- No error handling for permission failures

**Root Cause:**
```python
# BEFORE (Buggy)
def create_virtualhost(domain: str, path: Path):
    # Direct file write without sudo
    with open(VHOST_CONF, 'a') as f:  # ❌ Permission denied!
        f.write(vhost_block)
```

**Solution:**
```python
# AFTER (Fixed)
def create_virtualhost(domain: str, path: Path):
    # Use sudo for file operations
    try:
        subprocess.run([
            "sudo", "sh", "-c", 
            f"echo '{vhost_block}' >> {VHOST_CONF}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red bold]❌ Failed to write to vhost config:[/red bold] {e}")
        console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
        sys.exit(1)
```

**Additional Improvements:**
- Added `check_sudo_permissions()` function to warn users about sudo requirements
- Proper error handling with try-catch blocks
- Clear error messages when permission failures occur
- Progress indicators show what's happening during operations

### 3. **File Write Operations** ✅ FIXED

**Problem:**
- Both create and delete operations were failing due to permission issues
- No proper error handling for system operations

**Solution:**
- All file write operations now use `sudo`
- Proper error handling with descriptive messages
- Users are warned about sudo requirements upfront

---

*These fixes ensure that MPHM correctly detects MAMP installations, handles permissions properly, and provides a smooth user experience.*
