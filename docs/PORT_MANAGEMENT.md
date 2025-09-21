# 🔧 Port Management & Safe Deletion Features

This document outlines the new port management functionality and improved deletion behavior in the MPHM CLI tool.

## 🆕 New Features

### 1. **Safe Domain Deletion** ✅ IMPLEMENTED

**Problem:**
- Previous deletion function could potentially delete project folders
- Users might accidentally lose their work when deleting virtual hosts

**Solution:**
- **Virtual Host Only**: Deletion now only removes virtual host configuration and hosts file entries
- **Folder Preservation**: Project folders are preserved and clearly indicated to users
- **Clear Messaging**: Users are informed about what was deleted and what was preserved

**Updated Behavior:**
```python
print(f"[red]🗑️ Deleted virtual host:[/red] {domain}")
print(f"[cyan]📁 Project folder preserved:[/cyan] {get_domain_path(domain) or 'Unknown path'}")
```

**User Experience:**
```
🗑️ Deleted virtual host: test.yen
📁 Project folder preserved: /Users/lequang/Documents/Woks/test
```

### 2. **Port Management System** ✅ IMPLEMENTED

**Function:** `update_port()`

**Purpose:**
- Allows users to change the default port for new virtual hosts
- Provides validation and clear feedback
- Maintains existing virtual hosts with their configured ports

**Features:**
- **Current Port Display**: Shows the current default port
- **Input Validation**: Validates port numbers (1-65535)
- **Default Value**: Uses current port as default input
- **Clear Feedback**: Shows old and new port values
- **Existing Host Preservation**: Existing virtual hosts keep their configured ports

**Technical Implementation:**
```python
def update_port():
    """Update the default port for virtual hosts."""
    global PORT
    
    console.print(f"[blue]🔧 Current port:[/blue] {PORT}")
    console.print("[cyan]Enter new port number (e.g., 80, 8080, 8888):[/cyan]")
    
    try:
        new_port = int(Prompt.ask("Port", default=str(PORT)))
        
        if new_port == PORT:
            console.print("[yellow]⚠️ Port is already set to this value[/yellow]")
            return
        
        if new_port < 1 or new_port > 65535:
            console.print("[red]❌ Invalid port number. Please enter a port between 1 and 65535[/red]")
            return
        
        # Update global PORT variable
        old_port = PORT
        PORT = new_port
        
        console.print(f"[green]✅ Port updated from {old_port} to {PORT}[/green]")
        console.print("[yellow]⚠️ Note: Existing virtual hosts will continue to use their configured ports[/yellow]")
        console.print("[cyan]💡 New virtual hosts will use the updated port[/cyan]")
        
    except ValueError:
        console.print("[red]❌ Invalid port number. Please enter a valid integer[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Port update cancelled[/yellow]")
```

### 3. **Enhanced Virtual Host Status** ✅ IMPLEMENTED

**Updated Function:** `check_vhost_status()`

**New Feature:**
- **Current Port Display**: Shows the current default port in status display
- **Port Information**: Users can see what port new virtual hosts will use

**Status Display:**
```
┌─ Virtual Host Status ─┐
│ Apache Config: ✅ Exists
│ Virtual Host Config: ✅ Exists  
│ Virtual Host Module: ✅ Enabled
│ Apache Binary: ✅ Exists
│ Current Port: 8888
│                       │
│ Summary:
│ ✅ Virtual host functionality is fully configured and ready
└───────────────────────┘
```

## 🔧 Technical Implementation

### Port Management

**Global Variable:**
```python
PORT = 8888  # Default port for new virtual hosts
```

**Dynamic Updates:**
- Port changes are applied immediately to the global variable
- New virtual hosts use the updated port
- Existing virtual hosts maintain their configured ports

**Validation:**
- **Range Check**: Ports must be between 1 and 65535
- **Type Check**: Input must be a valid integer
- **Duplicate Check**: Prevents setting the same port

### Safe Deletion

**What Gets Deleted:**
- ✅ Virtual host configuration block from Apache config
- ✅ Domain entry from `/etc/hosts` file
- ✅ Apache restart to apply changes

**What Gets Preserved:**
- ✅ Project folder and all files
- ✅ Database files (if any)
- ✅ Configuration files
- ✅ User data and content

**Error Handling:**
- Graceful handling of missing paths
- Clear error messages for permission issues
- Fallback for inaccessible directories

## 🎯 User Experience

### Port Management Workflow

1. **Access**: Menu option 6 - "Update default port"
2. **Current Display**: Shows current port (e.g., 8888)
3. **Input**: User enters new port number
4. **Validation**: System validates the port number
5. **Update**: Port is updated if valid
6. **Feedback**: Clear confirmation of the change

**Example Session:**
```
🔧 Current port: 8888
Enter new port number (e.g., 80, 8080, 8888):
Port [8888]: 8080
✅ Port updated from 8888 to 8080
⚠️ Note: Existing virtual hosts will continue to use their configured ports
💡 New virtual hosts will use the updated port
```

### Safe Deletion Workflow

1. **Access**: Menu option 2 - "Delete site"
2. **Input**: User enters domain name to delete
3. **Processing**: System removes virtual host configuration
4. **Confirmation**: Clear message about what was deleted
5. **Preservation Notice**: Information about preserved folder

**Example Session:**
```
Enter project name to delete (e.g., mysite): test
🗑️ Deleted virtual host: test.yen
📁 Project folder preserved: /Users/lequang/Documents/Woks/test
```

## 🚀 Benefits

### For Users:
- ✅ **Data Safety**: No accidental loss of project files
- ✅ **Port Flexibility**: Easy port management for different environments
- ✅ **Clear Communication**: Always know what was deleted and what was preserved
- ✅ **Environment Adaptation**: Switch between development ports easily

### For Developers:
- ✅ **Project Preservation**: Safe deletion without data loss
- ✅ **Port Management**: Easy switching between development environments
- ✅ **Configuration Control**: Full control over virtual host ports
- ✅ **Error Prevention**: Validation prevents invalid port configurations

## 🔍 Advanced Features

### Port Validation
- **Range Validation**: Ensures ports are within valid range (1-65535)
- **Type Validation**: Prevents non-integer input
- **Duplicate Prevention**: Avoids setting the same port
- **User Feedback**: Clear error messages for invalid input

### Deletion Safety
- **Selective Deletion**: Only removes virtual host configuration
- **Path Preservation**: Maintains all project files and folders
- **Clear Messaging**: Users always know what happened
- **Error Handling**: Graceful handling of edge cases

## 🎉 Ready for Production

The port management and safe deletion features provide:
- ✅ **Safe Operations** that preserve user data
- ✅ **Flexible Port Management** for different environments
- ✅ **Clear User Communication** about all operations
- ✅ **Robust Validation** to prevent errors
- ✅ **Professional User Experience** with comprehensive feedback

These features make the MPHM CLI tool much safer and more flexible for managing development environments! 🚀
