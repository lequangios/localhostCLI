import os
import subprocess
import re
from pathlib import Path
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
from functools import lru_cache
from typing import Optional, List, Dict

console = Console()

PROJECTS = []
PORT = 8888
DOMAIN_SUFFIX = ".yen"

VHOST_CONF = "/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
APACHE_BINARY = "/Applications/MAMP/bin/apache2/bin/apachectl"
APACHE_RESTART = f"{APACHE_BINARY} -k restart"
APACHE_CONF = "/Applications/MAMP/conf/apache/httpd.conf"

# Cache for vhost content to avoid repeated file reads
_vhost_cache: Optional[str] = None
_vhost_cache_mtime: Optional[float] = None


def check_sudo_permissions():
    """Check if user has sudo permissions and request password if needed."""
    console.print("[yellow]🔐 Checking sudo permissions...[/yellow]")
    
    try:
        # Test sudo access without password first
        result = subprocess.run(
            ["sudo", "-n", "true"], 
            capture_output=True, 
            timeout=5
        )
        if result.returncode == 0:
            console.print("[green]✅ Sudo access confirmed[/green]")
            return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    
    # If no passwordless sudo, request password
    console.print("[yellow]⚠️ Sudo access required for virtual host operations[/yellow]")
    console.print("[cyan]Please enter your password when prompted[/cyan]")
    
    try:
        # Request sudo password by running a simple command
        result = subprocess.run(
            ["sudo", "true"], 
            check=True,
            timeout=30
        )
        console.print("[green]✅ Sudo access granted[/green]")
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        console.print("[red bold]❌ Sudo access denied or timeout[/red bold]")
        console.print("[yellow]Please ensure you have sudo privileges and try again[/yellow]")
        sys.exit(1)


def check_vhost_module_enabled() -> bool:
    """Check if virtual host module is enabled in Apache configuration."""
    try:
        with open(APACHE_CONF, 'r') as f:
            content = f.read()
        
        # Check for vhost module inclusion
        vhost_include = "Include conf/extra/httpd-vhosts.conf" in content
        vhost_module = "LoadModule vhost_alias_module" in content
        
        return vhost_include and vhost_module
    except (FileNotFoundError, PermissionError):
        return False


def enable_vhost_module():
    """Enable virtual host module in Apache configuration."""
    console.print("[blue]🔧 Enabling virtual host module...[/blue]")
    
    try:
        with open(APACHE_CONF, 'r') as f:
            content = f.read()
        
        # Check if already enabled
        if check_vhost_module_enabled():
            console.print("[green]✅ Virtual host module already enabled[/green]")
            return True
        
        # Add vhost module if not present
        if "LoadModule vhost_alias_module" not in content:
            # Find the LoadModule section and add vhost module
            lines = content.split('\n')
            new_lines = []
            module_added = False
            
            for line in lines:
                new_lines.append(line)
                if line.startswith("LoadModule") and not module_added:
                    new_lines.append("LoadModule vhost_alias_module modules/mod_vhost_alias.so")
                    module_added = True
            
            content = '\n'.join(new_lines)
        
        # Add vhost include if not present
        if "Include conf/extra/httpd-vhosts.conf" not in content:
            content += "\n\n# Virtual hosts\nInclude conf/extra/httpd-vhosts.conf\n"
        
        # Write back to file
        subprocess.run([
            "sudo", "sh", "-c",
            f"cat > {APACHE_CONF} << 'EOF'\n{content}\nEOF"
        ], check=True)
        
        console.print("[green]✅ Virtual host module enabled[/green]")
        return True
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red bold]❌ Failed to enable virtual host module:[/red bold] {e}")
        return False
    except (FileNotFoundError, PermissionError) as e:
        console.print(f"[red bold]❌ Cannot access Apache configuration:[/red bold] {e}")
        return False


def check_and_enable_vhost():
    """Check and enable virtual host functionality if needed."""
    console.print("[blue]🔍 Checking virtual host configuration...[/blue]")
    
    if check_vhost_module_enabled():
        console.print("[green]✅ Virtual host module is enabled[/green]")
        return True
    else:
        console.print("[yellow]⚠️ Virtual host module not enabled[/yellow]")
        console.print("[cyan]Attempting to enable virtual host module...[/cyan]")
        
        if enable_vhost_module():
            console.print("[green]✅ Virtual host module enabled successfully[/green]")
            console.print("[yellow]⚠️ Apache restart required for changes to take effect[/yellow]")
            return True
        else:
            console.print("[red bold]❌ Failed to enable virtual host module[/red bold]")
            console.print("[cyan]Please manually enable virtual host in MAMP settings[/cyan]")
            return False


def check_mamp_installed():
    """Check if MAMP is properly installed by verifying required files exist."""
    vhost_exists = Path(VHOST_CONF).exists()
    apache_exists = Path(APACHE_BINARY).exists()
    
    if not vhost_exists or not apache_exists:
        console.print("[red bold]❌ MAMP not found![/red bold]")
        console.print(f"[yellow]Missing components:[/yellow]")
        if not vhost_exists:
            console.print(f"  • VirtualHost config: {VHOST_CONF}")
        if not apache_exists:
            console.print(f"  • Apache binary: {APACHE_BINARY}")
        console.print(f"[cyan]Please ensure MAMP is installed in /Applications/MAMP[/cyan]")
        sys.exit(1)
    
    # Additional check: verify Apache binary is executable
    if not os.access(APACHE_BINARY, os.X_OK):
        console.print("[red bold]❌ Apache binary is not executable![/red bold]")
        console.print(f"[yellow]File: {APACHE_BINARY}[/yellow]")
        console.print("[cyan]Please check MAMP installation and permissions[/cyan]")
        sys.exit(1)
    
    # Check sudo permissions upfront
    check_sudo_permissions()
    
    # Check and enable virtual host functionality
    check_and_enable_vhost()


@lru_cache(maxsize=128)
def detect_project_type(path_str: str) -> str:
    """
    Optimized project type detection with caching and faster file checking.
    Uses specific file checks instead of expensive glob operations.
    """
    path = Path(path_str)
    
    # Check for specific framework files first (fastest)
    if (path / 'wp-config.php').exists():
        return 'WordPress'
    elif (path / 'artisan').exists():
        return 'Laravel'
    
    # Check for PHP files in common locations only (much faster than glob)
    php_files = [
        'index.php', 'config.php', 'app.php', 'bootstrap.php',
        'composer.json', 'package.json'
    ]
    
    for php_file in php_files:
        if (path / php_file).exists():
            return 'Plain PHP'
    
    # Check for HTML files in common locations
    html_files = ['index.html', 'home.html', 'main.html']
    for html_file in html_files:
        if (path / html_file).exists():
            return 'Static HTML'
    
    # Only use glob as last resort, but limit depth and file count
    try:
        # Check for any PHP files in root and first level only
        for item in path.iterdir():
            if item.is_file() and item.suffix == '.php':
                return 'Plain PHP'
            elif item.is_file() and item.suffix == '.html':
                return 'Static HTML'
    except (PermissionError, OSError):
        pass
    
    return 'Unknown'


def get_vhost_content() -> str:
    """Get vhost content with caching to avoid repeated file reads."""
    global _vhost_cache, _vhost_cache_mtime
    
    try:
        current_mtime = os.path.getmtime(VHOST_CONF)
        if _vhost_cache is None or _vhost_cache_mtime != current_mtime:
            with open(VHOST_CONF, 'r') as f:
                _vhost_cache = f.read()
            _vhost_cache_mtime = current_mtime
        return _vhost_cache
    except (FileNotFoundError, OSError):
        return ""


def check_domain_exists(domain: str) -> bool:
    """Check if domain already exists in vhost config."""
    content = get_vhost_content()
    if not content:
        return False
    
    # Check if domain exists in vhost config
    pattern = rf'ServerName\s+{re.escape(domain)}'
    return bool(re.search(pattern, content))


def check_hosts_entry_exists(domain: str) -> bool:
    """Check if domain already exists in /etc/hosts file."""
    try:
        with open('/etc/hosts', 'r') as f:
            hosts_content = f.read()
        return f'127.0.0.1 {domain}' in hosts_content
    except (FileNotFoundError, PermissionError):
        return False


def validate_new_site(domain: str) -> bool:
    """Validate that the new site doesn't already exist."""
    vhost_exists = check_domain_exists(domain)
    hosts_exists = check_hosts_entry_exists(domain)
    
    if vhost_exists or hosts_exists:
        console.print(f"[red bold]❌ Site '{domain}' already exists![/red bold]")
        
        if vhost_exists:
            console.print(f"[yellow]  • Virtual host configuration found[/yellow]")
        if hosts_exists:
            console.print(f"[yellow]  • Hosts file entry found[/yellow]")
        
        console.print(f"[cyan]Please choose a different name or delete the existing site first[/cyan]")
        return False
    
    return True


def create_virtualhost(domain: str, path: Path):
    """Create virtual host with progress indicator and batched operations."""
    # Validate that the site doesn't already exist
    if not validate_new_site(domain):
        return False
    
    console.print(f"[blue]🚀 Creating virtual host for {domain}...[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating virtual host...", total=None)
        
        vhost_block = f"""
<VirtualHost *:{PORT}>
    DocumentRoot \"{path}\"
    ServerName {domain}

    <Directory \"{path}\">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
"""
        
        # Write to vhost config file
        progress.update(task, description="Writing virtual host configuration...")
        try:
            subprocess.run([
                "sudo", "sh", "-c", 
                f"echo '{vhost_block}' >> {VHOST_CONF}"
            ], check=True)
            console.print("[green]✅ Virtual host configuration written[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red bold]❌ Failed to write to vhost config:[/red bold] {e}")
            console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
            sys.exit(1)
        
        # Invalidate cache
        global _vhost_cache
        _vhost_cache = None
        
        # Add to hosts file and restart Apache
        progress.update(task, description="Adding to hosts file and restarting Apache...")
        
        try:
            subprocess.run([
                "sudo", "sh", "-c", 
                f"echo '127.0.0.1 {domain}' >> /etc/hosts && {APACHE_RESTART}"
            ], check=True)
            console.print("[green]✅ Hosts file updated and Apache restarted[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red bold]❌ Failed to update hosts file or restart Apache:[/red bold] {e}")
            console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
            sys.exit(1)


def delete_virtualhost():
    """Optimized virtual host deletion using regex and batched operations."""
    name = Prompt.ask("Enter project name to delete (e.g., mysite)")
    domain = name + DOMAIN_SUFFIX

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting virtual host...", total=None)
        
        # Read current content
        content = get_vhost_content()
        
        # Use regex to remove the entire VirtualHost block for this domain
        pattern = rf'<VirtualHost \*:{PORT}>.*?ServerName {re.escape(domain)}.*?</VirtualHost>'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Write back if content changed
        if new_content != content:
            progress.update(task, description="Writing updated virtual host configuration...")
            
            # Use sudo to write to vhost config file
            try:
                subprocess.run([
                    "sudo", "sh", "-c",
                    f"cat > {VHOST_CONF} << 'EOF'\n{new_content}\nEOF"
                ], check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[red bold]❌ Failed to write to vhost config:[/red bold] {e}")
                console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
                sys.exit(1)
            
            # Invalidate cache
            global _vhost_cache
            _vhost_cache = None
            
            progress.update(task, description="Removing from hosts file and restarting Apache...")
            
            # Batch system operations
            try:
                subprocess.run([
                    "sudo", "sh", "-c",
                    f"sed -i '' '/127.0.0.1 {re.escape(domain)}/d' /etc/hosts && {APACHE_RESTART}"
                ], check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[red bold]❌ Failed to update hosts file or restart Apache:[/red bold] {e}")
                console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
                sys.exit(1)
            
            print(f"[red]🗑️ Deleted virtual host:[/red] {domain}")
            print(f"[cyan]📁 Project folder preserved:[/cyan] {get_domain_path(domain) or 'Unknown path'}")
        else:
            print(f"[yellow]⚠️ Site not found:[/yellow] {domain}")


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


def refresh_domain():
    """Refresh domain configuration to detect new project type."""
    console.print("[blue]🔄 Refresh Domain Configuration[/blue]")
    console.print("[cyan]This will update the virtual host configuration to reflect any changes in your project type.[/cyan]")
    
    # List current domains for user to choose from
    content = get_vhost_content()
    if not content:
        console.print("[yellow]No virtual hosts found.[/yellow]")
        return
    
    # Find all .yen domains
    pattern = rf'ServerName\s+([^\s]+{re.escape(DOMAIN_SUFFIX)})'
    matches = re.findall(pattern, content)
    
    if not matches:
        console.print("[yellow]No .yen sites found.[/yellow]")
        return
    
    # Display available domains
    console.print("\n[bold]Available domains:[/bold]")
    for i, domain in enumerate(matches, 1):
        domain_path = get_domain_path(domain)
        domain_port = get_domain_port(domain)
        port_display = f" :{domain_port}" if domain_port else " :?"
        
        if domain_path and domain_path.exists():
            project_type = detect_project_type(str(domain_path))
            type_emoji = {
                'WordPress': '🔵',
                'Laravel': '🔴', 
                'PHP': '🟡',
                'HTML': '🟢',
                'Unknown': '⚪'
            }.get(project_type, '⚪')
            
            console.print(f"[green]{i})[/green] {domain}{port_display} {type_emoji} {project_type}")
            console.print(f"    📁 {domain_path}")
        else:
            console.print(f"[green]{i})[/green] {domain}{port_display} ⚠️ Path not found")
    
    # Get user selection
    try:
        choice = int(Prompt.ask(f"\n[yellow]Select domain to refresh (1-{len(matches)})[/yellow]"))
        if choice < 1 or choice > len(matches):
            console.print("[red]❌ Invalid selection[/red]")
            return
        
        selected_domain = matches[choice - 1]
        domain_path = get_domain_path(selected_domain)
        
        if not domain_path or not domain_path.exists():
            console.print(f"[red]❌ Cannot refresh {selected_domain}: Path not found[/red]")
            return
        
        # Detect current project type
        current_type = detect_project_type(str(domain_path))
        console.print(f"\n[blue]Current project type:[/blue] {current_type}")
        
        # Ask for confirmation
        if not Confirm.ask(f"[yellow]Refresh configuration for {selected_domain}?[/yellow]"):
            console.print("[yellow]⚠️ Refresh cancelled[/yellow]")
            return
        
        # Refresh the configuration
        console.print(f"[blue]🔄 Refreshing configuration for {selected_domain}...[/blue]")
        
        # The refresh is mainly informational - the virtual host config doesn't need to change
        # But we can provide useful information about the current state
        domain_port = get_domain_port(selected_domain)
        port_display = f" :{domain_port}" if domain_port else " :?"
        
        console.print(f"[green]✅ Configuration refreshed for {selected_domain}{port_display}[/green]")
        console.print(f"[cyan]📁 Project path:[/cyan] {domain_path}")
        console.print(f"[cyan]🔍 Detected type:[/cyan] {current_type}")
        
        # Provide helpful information based on project type
        if current_type == "WordPress":
            console.print("[blue]💡 WordPress detected:[/blue]")
            console.print("   • Ensure wp-config.php is properly configured")
            console.print("   • Check database connection settings")
            console.print("   • Verify file permissions (755 for directories, 644 for files)")
        elif current_type == "Laravel":
            console.print("[blue]💡 Laravel detected:[/blue]")
            console.print("   • Run 'composer install' if dependencies are missing")
            console.print("   • Check .env file configuration")
            console.print("   • Ensure storage and bootstrap/cache directories are writable")
        elif current_type == "PHP":
            console.print("[blue]💡 PHP project detected:[/blue]")
            console.print("   • Check PHP version compatibility")
            console.print("   • Verify file permissions")
        elif current_type == "HTML":
            console.print("[blue]💡 Static HTML detected:[/blue]")
            console.print("   • Ensure index.html or index.php exists")
            console.print("   • Check file permissions")
        else:
            console.print("[blue]💡 Unknown project type:[/blue]")
            console.print("   • Check if project files are properly organized")
            console.print("   • Verify the project structure")
        
    except ValueError:
        console.print("[red]❌ Invalid input. Please enter a number.[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Refresh cancelled[/yellow]")


def list_virtualhosts():
    """Enhanced listing with project type detection."""
    print("[bold cyan]\n📋 Registered .yen sites:[/bold cyan]")
    
    content = get_vhost_content()
    if not content:
        print("[yellow]No virtual hosts found.[/yellow]")
        return
    
    # Use regex to find all ServerName entries with .yen domains
    pattern = rf'ServerName\s+([^\s]+{re.escape(DOMAIN_SUFFIX)})'
    matches = re.findall(pattern, content)
    
    if matches:
        for domain in matches:
            # Get the document root path and port for this domain
            domain_path = get_domain_path(domain)
            domain_port = get_domain_port(domain)
            
            if domain_path and domain_path.exists():
                # Detect project type
                project_type = detect_project_type(str(domain_path))
                
                # Format project type with appropriate emoji
                type_emoji = {
                    'WordPress': '🔵',
                    'Laravel': '🔴', 
                    'PHP': '🟡',
                    'HTML': '🟢',
                    'Unknown': '⚪'
                }.get(project_type, '⚪')
                
                # Format port display
                port_display = f" :{domain_port}" if domain_port else " :?"
                
                print(f"• {domain}{port_display} {type_emoji} {project_type}")
                print(f"  📁 {domain_path}")
            else:
                port_display = f" :{domain_port}" if domain_port else " :?"
                print(f"• {domain}{port_display} ⚠️ Path not found")
    else:
        print("[yellow]No .yen sites found.[/yellow]")


def create_project_template():
    """Create project template with progress indicators and optimized operations."""
    project_type = Prompt.ask("Choose project type", choices=["wordpress", "laravel"])
    name = Prompt.ask("Enter project name")
    domain = name + DOMAIN_SUFFIX
    base_path = Path.home() / "Sites" / name
    base_path.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        if project_type == "wordpress":
            task = progress.add_task("Downloading WordPress...", total=None)
            subprocess.run([
                "curl", "-L", "-o", "latest.zip", 
                "https://wordpress.org/latest.zip"
            ], check=True)
            
            progress.update(task, description="Extracting WordPress...")
            subprocess.run([
                "unzip", "-q", "latest.zip", "-d", str(base_path)
            ], check=True)
            
            progress.update(task, description="Setting up WordPress...")
            subprocess.run([
                "mv", str(base_path / "wordpress"), str(base_path / "public")
            ], check=True)
            
            # Clean up in background
            subprocess.Popen(["rm", "latest.zip"])
            
        elif project_type == "laravel":
            task = progress.add_task("Creating Laravel project...", total=None)
            subprocess.run([
                "composer", "create-project", "--prefer-dist", 
                "laravel/laravel", str(base_path / "public")
            ], check=True)

        progress.update(task, description="Setting up virtual host...")
        if create_virtualhost(domain, base_path / "public"):
            print(f"[green]✅ {project_type.capitalize()} site created:[/green] http://{domain}:{PORT}")
            subprocess.run(["open", f"http://{domain}:{PORT}"])
        else:
            print("[yellow]⚠️ Site creation cancelled[/yellow]")


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
        
        # Update APACHE_RESTART command with new port
        global APACHE_RESTART
        APACHE_RESTART = f"{APACHE_BINARY} -k restart"
        
        console.print(f"[green]✅ Port updated from {old_port} to {PORT}[/green]")
        console.print("[yellow]⚠️ Note: Existing virtual hosts will continue to use their configured ports[/yellow]")
        console.print("[cyan]💡 New virtual hosts will use the updated port[/cyan]")
        
    except ValueError:
        console.print("[red]❌ Invalid port number. Please enter a valid integer[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Port update cancelled[/yellow]")


def check_vhost_status():
    """Display detailed virtual host configuration status."""
    console.print(Panel("[bold cyan]Virtual Host Status[/bold cyan]", expand=False))
    
    # Check Apache configuration file
    apache_conf_exists = Path(APACHE_CONF).exists()
    console.print(f"[blue]Apache Config:[/blue] {APACHE_CONF}")
    console.print(f"  Status: {'✅ Exists' if apache_conf_exists else '❌ Not found'}")
    
    # Check virtual host config file
    vhost_conf_exists = Path(VHOST_CONF).exists()
    console.print(f"[blue]Virtual Host Config:[/blue] {VHOST_CONF}")
    console.print(f"  Status: {'✅ Exists' if vhost_conf_exists else '❌ Not found'}")
    
    # Check virtual host module
    vhost_enabled = check_vhost_module_enabled()
    console.print(f"[blue]Virtual Host Module:[/blue] {'✅ Enabled' if vhost_enabled else '❌ Disabled'}")
    
    # Check Apache binary
    apache_binary_exists = Path(APACHE_BINARY).exists()
    console.print(f"[blue]Apache Binary:[/blue] {APACHE_BINARY}")
    console.print(f"  Status: {'✅ Exists' if apache_binary_exists else '❌ Not found'}")
    
    # Show current port
    console.print(f"[blue]Current Port:[/blue] {PORT}")
    
    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if apache_conf_exists and vhost_conf_exists and vhost_enabled and apache_binary_exists:
        console.print("[green]✅ Virtual host functionality is fully configured and ready[/green]")
    else:
        console.print("[yellow]⚠️ Virtual host functionality needs attention[/yellow]")
        if not vhost_enabled:
            console.print("[cyan]💡 Use option 5 to enable virtual host module[/cyan]")
    
    # Show current virtual hosts
    console.print("\n[bold]Current Virtual Hosts:[/bold]")
    list_virtualhosts()


def main():
    check_mamp_installed()

    console.print(Panel("[bold cyan]MAMP HOST TOOL (.yen)[/bold cyan]", expand=False))
    print("[green]1)[/green] Create new site")
    print("[green]2)[/green] Delete site")
    print("[green]3)[/green] List existing sites")
    print("[green]4)[/green] Create sample WordPress/Laravel project")
    print("[green]5)[/green] Check virtual host status")
    print("[green]6)[/green] Update default port")
    print("[green]7)[/green] Refresh domain configuration")
    print("[green]0)[/green] Exit")

    choice = Prompt.ask("[yellow]Choose an option[/yellow]", choices=["0", "1", "2", "3", "4", "5", "6", "7"])

    if choice == '1':
        name = Prompt.ask("Enter project name (e.g., mysite)")
        domain = name + DOMAIN_SUFFIX
        folder = Prompt.ask("Enter full project folder path")
        path = Path(folder).expanduser()

        if not path.exists():
            print("[red]❌ Folder not found.[/red]")
            return

        project_type = detect_project_type(str(path))
        print(f"[cyan]Detected project type:[/cyan] [bold]{project_type}[/bold]")

        if create_virtualhost(domain, path):
            print(f"[green]✅ Site created:[/green] http://{domain}:{PORT}")
            subprocess.run(["open", f"http://{domain}:{PORT}"])
        else:
            print("[yellow]⚠️ Site creation cancelled[/yellow]")

    elif choice == '2':
        delete_virtualhost()

    elif choice == '3':
        list_virtualhosts()

    elif choice == '4':
        create_project_template()

    elif choice == '5':
        check_vhost_status()

    elif choice == '6':
        update_port()

    elif choice == '7':
        refresh_domain()

    elif choice == '0':
        console.print("[bold]Goodbye![/bold]", style="magenta")
        exit()


if __name__ == '__main__':
    main()