# Custom Domain Suffix Management

## 🎯 **Overview**

FE Local CLI v1.1.0 introduces the ability to customize domain suffixes instead of being locked to `.yen`. Users can now use any domain suffix they prefer, such as `.local`, `.dev`, `.test`, or any custom suffix.

## 🔧 **Features**

### **1. Custom Domain Suffix Configuration**
- **Default**: `.yen` (backward compatible)
- **Custom Options**: `.local`, `.dev`, `.test`, `.app`, or any custom suffix
- **Persistent Configuration**: Settings saved to `~/.fe_local_config`
- **Validation**: Ensures proper domain format

### **2. Domain Management Menu**
- **Option 8**: "Manage domain suffix" in main menu
- **Change Suffix**: Set new domain suffix
- **Reset to Default**: Return to `.yen`
- **Show Configuration**: Display current settings
- **Save/Load**: Persistent configuration across sessions

## 📋 **Usage Examples**

### **Setting Custom Domain Suffix**

```bash
# Start FE Local CLI
fe_local

# Choose option 8: Manage domain suffix
8

# Choose option 1: Change domain suffix
1

# Enter new suffix (examples):
.local
.dev
.test
.mycompany
```

### **Domain Suffix Options**

| Suffix | Example Domain | Use Case |
|--------|---------------|----------|
| `.local` | `mysite.local` | Standard local development |
| `.dev` | `mysite.dev` | Development environment |
| `.test` | `mysite.test` | Testing environment |
| `.app` | `mysite.app` | Application development |
| `.yen` | `mysite.yen` | Default (backward compatible) |
| Custom | `mysite.mycompany` | Company-specific |

## 🛠️ **Configuration Management**

### **Configuration File**
- **Location**: `~/.fe_local_config`
- **Format**: Simple key-value pairs
- **Content**:
  ```
  DOMAIN_SUFFIX=.local
  PORT=8888
  ```

### **Configuration Functions**

#### **Load Configuration**
```python
def load_config():
    """Load configuration from file."""
    global DOMAIN_SUFFIX, PORT
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('DOMAIN_SUFFIX='):
                        DOMAIN_SUFFIX = line.split('=', 1)[1]
                    elif line.startswith('PORT='):
                        PORT = int(line.split('=', 1)[1])
        except (ValueError, OSError) as e:
            console.print(f"[yellow]⚠️ Error loading config: {e}[/yellow]")
            console.print("[cyan]Using default values[/cyan]")
```

#### **Save Configuration**
```python
def save_config():
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"DOMAIN_SUFFIX={DOMAIN_SUFFIX}\n")
            f.write(f"PORT={PORT}\n")
        console.print(f"[green]✅ Configuration saved to {CONFIG_FILE}[/green]")
    except OSError as e:
        console.print(f"[red]❌ Error saving config: {e}[/red]")
```

## 🔍 **Domain Validation**

### **Validation Rules**
- Must start with `.` (automatically added if missing)
- Valid characters: `a-z`, `A-Z`, `0-9`, `-`
- Must follow domain format: `.example` or `.sub.example`
- Regex pattern: `^\.([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+$`

### **Validation Examples**

| Input | Valid | Result |
|-------|-------|--------|
| `local` | ✅ | `.local` |
| `.dev` | ✅ | `.dev` |
| `.my-company` | ✅ | `.my-company` |
| `.sub.domain` | ✅ | `.sub.domain` |
| `invalid..domain` | ❌ | Error message |
| `domain with spaces` | ❌ | Error message |

## 🎮 **User Interface**

### **Domain Management Menu**
```
🔧 Domain Suffix Management
Current domain suffix: .local

Options:
1) Change domain suffix
2) Reset to default (.yen)
3) Show current configuration
0) Back to main menu

Choose an option [0/1/2/3]: 
```

### **Change Domain Suffix Flow**
```
Enter new domain suffix (e.g., .local, .dev, .test): .dev
✅ Domain suffix changed from .local to .dev
Save this configuration? [y/N]: y
✅ Configuration saved to /Users/username/.fe_local_config
💡 New sites will use the updated domain suffix
⚠️ Existing sites will keep their current domains
```

### **Configuration Display**
```
Current Configuration:
  Domain Suffix: .dev
  Port: 8888
  Config File: /Users/username/.fe_local_config
  Config Exists: Yes
```

## 🔄 **Backward Compatibility**

### **Existing Sites**
- **No Impact**: Existing `.yen` sites continue to work
- **Mixed Domains**: Can have both `.yen` and custom suffix sites
- **List Display**: Shows all domains regardless of suffix

### **Default Behavior**
- **First Run**: Uses `.yen` as default
- **Config Missing**: Falls back to `.yen`
- **Reset Option**: Always available to return to `.yen`

## 📊 **Integration with Existing Features**

### **Create New Site**
- Uses current `DOMAIN_SUFFIX` setting
- Displays full domain in confirmation
- Example: `mysite.dev` instead of `mysite.yen`

### **List Sites**
- Shows all domains regardless of suffix
- Project type detection works with any suffix
- Port display works with any suffix

### **Delete Site**
- Works with any domain suffix
- No changes to deletion logic

### **Virtual Host Status**
- Shows current domain suffix in status
- Lists all domains regardless of suffix

## 🚀 **Benefits**

### **Flexibility**
- **Team Standards**: Use company-specific suffixes
- **Environment Separation**: Different suffixes for different environments
- **Personal Preference**: Choose what works best for you

### **Professional Development**
- **Industry Standards**: Use `.local` or `.dev` as industry standard
- **Client Projects**: Use client-specific suffixes
- **Testing**: Use `.test` for testing environments

### **Ease of Use**
- **Persistent Settings**: No need to reconfigure each time
- **Simple Interface**: Easy-to-use menu system
- **Validation**: Prevents invalid configurations

## 🔧 **Technical Implementation**

### **Global Variables**
```python
DOMAIN_SUFFIX = ".yen"  # Default domain suffix
CONFIG_FILE = Path.home() / ".fe_local_config"
```

### **Menu Integration**
```python
console.print(Panel(f"[bold cyan]MAMP HOST TOOL ({DOMAIN_SUFFIX})[/bold cyan]", expand=False))
print("[green]8)[/green] Manage domain suffix")
```

### **Domain Generation**
```python
if choice == '1':
    name = Prompt.ask("Enter project name (e.g., mysite)")
    domain = name + DOMAIN_SUFFIX  # Uses current suffix
    # ... rest of create site logic
```

## 📝 **Migration Guide**

### **From v1.0.x to v1.1.0**
1. **No Action Required**: Existing `.yen` sites continue to work
2. **Optional**: Use option 8 to change default suffix
3. **New Sites**: Will use current suffix setting

### **Changing Existing Setup**
1. **Backup**: Existing sites are not affected
2. **New Suffix**: Only applies to new sites
3. **Mixed Environment**: Can have both old and new suffixes

## 🎯 **Best Practices**

### **Suffix Selection**
- **`.local`**: Most common for local development
- **`.dev`**: Good for development environments
- **`.test`**: Ideal for testing environments
- **Custom**: Use for specific projects or teams

### **Configuration Management**
- **Save Changes**: Always save configuration changes
- **Backup Config**: Keep backup of `~/.fe_local_config`
- **Team Sync**: Share configuration with team members

### **Domain Naming**
- **Consistent**: Use consistent naming across team
- **Descriptive**: Choose descriptive project names
- **Short**: Keep domain names reasonably short

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multiple Suffixes**: Support for multiple suffixes simultaneously
- **Suffix Templates**: Predefined suffix configurations
- **Import/Export**: Configuration import/export functionality
- **Team Sync**: Automatic configuration synchronization

### **Potential Improvements**
- **Environment Variables**: Support for environment-based suffixes
- **Project-Specific**: Per-project suffix configuration
- **Auto-Detection**: Automatic suffix detection from project files
