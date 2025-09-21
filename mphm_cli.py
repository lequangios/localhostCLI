import os
import subprocess
import re
import argparse
from pathlib import Path
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
from functools import lru_cache
from typing import Optional, List, Dict
import shutil
from getpass import getpass
import platform

console = Console()

# Version information
VERSION = "1.2.0"
APP_NAME = "FE Local CLI"

PROJECTS = []
PORT = 8888
DOMAIN_SUFFIX = ".yen"  # Default domain suffix
CONFIG_FILE = Path.home() / ".fe_local_config"

VHOST_CONF = "/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
APACHE_BINARY = "/Applications/MAMP/bin/apache2/bin/apachectl"
APACHE_RESTART = f"{APACHE_BINARY} -k restart"
APACHE_CONF = "/Applications/MAMP/conf/apache/httpd.conf"
MAMP_MYSQL = "/Applications/MAMP/Library/bin/mysql"

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
    
    # Check if we're in an interactive environment
    if not sys.stdin.isatty():
        console.print("[yellow]⚠️ Non-interactive environment detected[/yellow]")
        console.print("[cyan]Sudo will be requested when needed during operations[/cyan]")
        return True
    
    # If no passwordless sudo and we're interactive, request password
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
        
        # Check for vhost module inclusion (must be active, not commented)
        # Look for active include statement (not commented out)
        lines = content.split('\n')
        vhost_include = False
        vhost_module = False
        
        for line in lines:
            line = line.strip()
            # Check for active include (not commented)
            if line == "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf":
                vhost_include = True
            # Check for vhost module
            if "LoadModule vhost_alias_module" in line and not line.startswith('#'):
                vhost_module = True
        
        # Both must be present and active (not commented out)
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
        
        # Create backup
        console.print("[blue]💾 Creating backup...[/blue]")
        subprocess.run([
            "sudo", "cp", APACHE_CONF, f"{APACHE_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
        ], check=True)
        
        # Add vhost module if not present
        if "LoadModule vhost_alias_module" not in content:
            console.print("[blue]🔧 Adding virtual host module...[/blue]")
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
        
        # Handle virtual host include configuration
        console.print("[blue]🔧 Configuring virtual host include...[/blue]")
        
        # Check for commented out absolute path (enable it)
        if "#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" in content:
            content = content.replace(
                "#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf",
                "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
            )
            console.print("[green]✅ Enabled commented virtual host configuration[/green]")
        
        # Check for commented out relative path (enable and fix it)
        elif "#Include conf/extra/httpd-vhosts.conf" in content:
            content = content.replace(
                "#Include conf/extra/httpd-vhosts.conf",
                "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
            )
            console.print("[green]✅ Enabled and fixed virtual host configuration[/green]")
        
        # Check for incorrect relative path (fix it)
        elif "Include conf/extra/httpd-vhosts.conf" in content:
            content = content.replace(
                "Include conf/extra/httpd-vhosts.conf",
                "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"
            )
            console.print("[green]✅ Fixed virtual host configuration path[/green]")
        
        # Check if include is missing (add it)
        elif "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" not in content:
            content += "\n\n# Virtual hosts\nInclude /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf\n"
            console.print("[green]✅ Added virtual host configuration[/green]")
        
        # Write back to file
        console.print("[blue]💾 Writing configuration...[/blue]")
        subprocess.run([
            "sudo", "sh", "-c",
            f"cat > {APACHE_CONF} << 'EOF'\n{content}\nEOF"
        ], check=True)
        
        # Test Apache configuration
        console.print("[blue]🧪 Testing Apache configuration...[/blue]")
        try:
            subprocess.run([APACHE_BINARY, "configtest"], check=True, capture_output=True)
            console.print("[green]✅ Apache configuration is valid[/green]")
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠️ Apache configuration test failed, but changes were applied[/yellow]")
        
        console.print("[green]✅ Virtual host module enabled successfully[/green]")
        return True
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red bold]❌ Failed to enable virtual host module:[/red bold] {e}")
        console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
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
    """Create virtual host with progress indicator and batched operations.
    - Validates input path
    - If Laravel project is detected, point DocumentRoot to path/public
    """
    # Validate that the site doesn't already exist
    if not validate_new_site(domain):
        return False

    # Validate provided path
    if not path or not isinstance(path, Path):
        console.print("[red bold]❌ Invalid path provided[/red bold]")
        return False

    if not path.exists():
        console.print(f"[red bold]❌ Path not found:[/red bold] {path}")
        return False

    # Determine actual document root
    actual_docroot = path

    try:
        project_type = detect_project_type(str(path))
    except Exception:
        project_type = "Unknown"

    # Detect Laravel either by detector or by artisan presence
    is_laravel = project_type == "Laravel" or (path / "artisan").exists() or (
        path.parent.exists() and (path.parent / "artisan").exists() and path.name == "public"
    )

    if is_laravel:
        # If user gave project root, use root/public; if they already passed public, keep as is
        if (path / "artisan").exists():
            laravel_public = path / "public"
            if not laravel_public.exists():
                console.print(
                    f"[red bold]❌ Laravel detected but 'public' directory not found in:[/red bold] {path}"
                )
                return False
            actual_docroot = laravel_public
        else:
            # path might already be the public directory
            actual_docroot = path

    # Final safety: docroot must exist
    if not actual_docroot.exists():
        console.print(f"[red bold]❌ DocumentRoot not found:[/red bold] {actual_docroot}")
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
    DocumentRoot \"{actual_docroot}\"
    ServerName {domain}

    <Directory \"{actual_docroot}\">
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

            # Check for specific Apache configuration error
            if "Could not open configuration file" in str(e) and "httpd-vhosts.conf" in str(e):
                console.print(f"[yellow]⚠️ Apache configuration error detected![/yellow]")
                console.print(f"[cyan]The Apache config is looking for httpd-vhosts.conf in the wrong location.[/cyan]")
                console.print(f"[blue]💡 To fix this issue, run:[/blue]")
                console.print(f"[green]   ./fix_apache_config.sh[/green]")
                console.print(f"[cyan]This will fix the Apache configuration path.[/cyan]")
            else:
                console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")

            sys.exit(1)


def delete_virtualhost():
    """Optimized virtual host deletion using regex and safer hosts update.
    - Accepts project name or full domain
    - Removes only the exact matching VirtualHost block (any port)
    - Removes only the domain token from /etc/hosts lines
    """
    raw_input = Prompt.ask("Enter domain or project name to delete (e.g., mysite or mysite.yen)")
    domain = raw_input if raw_input.endswith(DOMAIN_SUFFIX) else raw_input + DOMAIN_SUFFIX

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting virtual host...", total=None)
        
        # Read current content
        content = get_vhost_content()
        
        # Remove the entire VirtualHost block for this domain (any port)
        block_pattern = rf'<VirtualHost[^>]*>.*?ServerName\s+{re.escape(domain)}\b[\s\S]*?</VirtualHost>'
        new_content = re.sub(block_pattern, '', content, flags=re.DOTALL)
        
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

            # Safely remove only the specific domain token from /etc/hosts (any IP)
            try:
                try:
                    with open('/etc/hosts', 'r') as f:
                        hosts_lines = f.readlines()
                except (FileNotFoundError, PermissionError, OSError):
                    hosts_lines = []

                updated_lines = []
                domain_removed = False
                for line in hosts_lines:
                    # Preserve comments and non 127.0.0.1 lines
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        updated_lines.append(line)
                        continue

                    # Tokenize line; first token is IP, remaining are hostnames
                    tokens = stripped.split()
                    if len(tokens) == 0:
                        updated_lines.append(line)
                        continue

                    ip = tokens[0]
                    hosts = tokens[1:]

                    if domain in hosts:
                        # Remove only the domain token
                        remaining = [h for h in hosts if h != domain]
                        domain_removed = True
                        if remaining:
                            new_line = ip + ' ' + ' '.join(remaining) + '\n'
                            updated_lines.append(new_line)
                        else:
                            # Keep the IP-only line to avoid losing system mappings
                            updated_lines.append(ip + '\n')
                    else:
                        updated_lines.append(line)

                updated_hosts = ''.join(updated_lines)

                subprocess.run([
                    "sudo", "sh", "-c",
                    f"cat > /etc/hosts << 'EOF'\n{updated_hosts}\nEOF && {APACHE_RESTART}"
                ], check=True)
            except subprocess.CalledProcessError as e:
                console.print(f"[red bold]❌ Failed to update hosts file or restart Apache:[/red bold] {e}")

                # Check for specific Apache configuration error
                if "Could not open configuration file" in str(e) and "httpd-vhosts.conf" in str(e):
                    console.print(f"[yellow]⚠️ Apache configuration error detected![/yellow]")
                    console.print(f"[cyan]The Apache config is looking for httpd-vhosts.conf in the wrong location.[/cyan]")
                    console.print(f"[blue]💡 To fix this issue, run:[/blue]")
                    console.print(f"[green]   ./fix_apache_config.sh[/green]")
                    console.print(f"[cyan]This will fix the Apache configuration path.[/cyan]")
                else:
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


def show_help():
    """Display help information for the CLI tool."""
    console.print(Panel(f"[bold cyan]{APP_NAME} v{VERSION}[/bold cyan]", expand=False))
    console.print()
    
    console.print("[bold]DESCRIPTION[/bold]")
    console.print("FE Local CLI is a powerful tool for managing MAMP virtual hosts and local development environments.")
    console.print()
    
    console.print("[bold]USAGE[/bold]")
    console.print("  fe_local [OPTIONS]")
    console.print()
    
    console.print("[bold]OPTIONS[/bold]")
    console.print("  -h, --help     Show this help message and exit")
    console.print("  -v, --version  Show version information and exit")
    console.print()
    
    console.print("[bold]FEATURES[/bold]")
    console.print("  • Create and manage virtual hosts with custom domain suffixes")
    console.print("  • Automatic project type detection (WordPress, Laravel, PHP, HTML)")
    console.print("  • Port management and configuration")
    console.print("  • Custom domain suffix management (.local, .dev, .test, etc.)")
    console.print("  • Safe domain deletion (preserves project files)")
    console.print("  • Refresh domain configuration for project type changes")
    console.print("  • Virtual host status monitoring")
    console.print("  • Sample project template creation")
    console.print()
    
    console.print("[bold]EXAMPLES[/bold]")
    console.print("  fe_local                    # Start interactive CLI")
    console.print("  fe_local --help             # Show this help")
    console.print("  fe_local --version          # Show version")
    console.print()
    
    console.print("[bold]REQUIREMENTS[/bold]")
    console.print("  • MAMP installed and running")
    console.print("  • Sudo privileges for virtual host operations")
    console.print("  • macOS (tested on macOS)")
    console.print()
    
    console.print("[bold]SUPPORT[/bold]")
    console.print("  For issues and feature requests, please cotatct levietquangt2@gmail.com.")
    console.print()


def show_version():
    """Display version information for the CLI tool."""
    console.print(f"[bold cyan]{APP_NAME} v{VERSION}[/bold cyan]")
    console.print()
    console.print("[bold]Build Information[/bold]")
    console.print(f"  Version: {VERSION}")
    console.print(f"  Python: {sys.version.split()[0]}")
    console.print(f"  Platform: {sys.platform}")
    console.print()
    console.print("[bold]Features[/bold]")
    console.print("  • Virtual Host Management")
    console.print("  • Project Type Detection")
    console.print("  • Port Configuration")
    console.print("  • Custom Domain Suffix")
    console.print("  • Safe Operations")
    console.print("  • Rich CLI Interface")


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


def save_config():
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"DOMAIN_SUFFIX={DOMAIN_SUFFIX}\n")
            f.write(f"PORT={PORT}\n")
        console.print(f"[green]✅ Configuration saved to {CONFIG_FILE}[/green]")
    except OSError as e:
        console.print(f"[red]❌ Error saving config: {e}[/red]")


def manage_domain_suffix():
    """Manage domain suffix configuration."""
    global DOMAIN_SUFFIX
    
    console.print("[blue]🔧 Domain Suffix Management[/blue]")
    console.print(f"[cyan]Current domain suffix:[/cyan] [bold]{DOMAIN_SUFFIX}[/bold]")
    console.print()
    
    console.print("[bold]Options:[/bold]")
    console.print("1) Change domain suffix")
    console.print("2) Reset to default (.yen)")
    console.print("3) Show current configuration")
    console.print("0) Back to main menu")
    
    choice = Prompt.ask("[yellow]Choose an option[/yellow]", choices=["0", "1", "2", "3"])
    
    if choice == '1':
        new_suffix = Prompt.ask("[cyan]Enter new domain suffix (e.g., .local, .dev, .test)[/cyan]")
        
        # Validate domain suffix
        if not new_suffix.startswith('.'):
            new_suffix = '.' + new_suffix
        
        # Check for valid characters
        if not re.match(r'^\.([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+$', new_suffix):
            console.print("[red]❌ Invalid domain suffix format[/red]")
            console.print("[yellow]Please use format like: .local, .dev, .test[/yellow]")
            return
        
        old_suffix = DOMAIN_SUFFIX
        DOMAIN_SUFFIX = new_suffix
        
        console.print(f"[green]✅ Domain suffix changed from {old_suffix} to {DOMAIN_SUFFIX}[/green]")
        
        # Ask if user wants to save
        if Confirm.ask("[yellow]Save this configuration?[/yellow]"):
            save_config()
            console.print("[cyan]💡 New sites will use the updated domain suffix[/cyan]")
            console.print("[yellow]⚠️ Existing sites will keep their current domains[/yellow]")
        else:
            DOMAIN_SUFFIX = old_suffix
            console.print("[yellow]⚠️ Changes discarded[/yellow]")
    
    elif choice == '2':
        old_suffix = DOMAIN_SUFFIX
        DOMAIN_SUFFIX = ".yen"
        console.print(f"[green]✅ Domain suffix reset to {DOMAIN_SUFFIX}[/green]")
        
        if Confirm.ask("[yellow]Save this configuration?[/yellow]"):
            save_config()
        else:
            DOMAIN_SUFFIX = old_suffix
            console.print("[yellow]⚠️ Changes discarded[/yellow]")
    
    elif choice == '3':
        console.print("\n[bold]Current Configuration:[/bold]")
        console.print(f"  Domain Suffix: {DOMAIN_SUFFIX}")
        console.print(f"  Port: {PORT}")
        console.print(f"  Config File: {CONFIG_FILE}")
        console.print(f"  Config Exists: {'Yes' if CONFIG_FILE.exists() else 'No'}")
    
    elif choice == '0':
        return


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
                port_display = f":{domain_port}" if domain_port else " :?"
                
                print(f"• http://{domain}{port_display} {type_emoji} {project_type}")
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


def check_apache_config():
    """Check Apache configuration for common issues."""
    console.print("[blue]🔍 Checking Apache Configuration...[/blue]")
    
    # Check if Apache config exists
    if not Path(APACHE_CONF).exists():
        console.print(f"[red]❌ Apache config not found: {APACHE_CONF}[/red]")
        return False
    
    # Check for virtual host configuration
    try:
        with open(APACHE_CONF, 'r') as f:
            content = f.read()
            
        # Check for commented out include (virtual host disabled)
        if "#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" in content:
            console.print(f"[yellow]⚠️ Virtual host configuration is commented out (disabled)[/yellow]")
            console.print(f"[cyan]Found: #Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf[/cyan]")
            console.print(f"[blue]💡 To enable virtual hosts, run:[/blue]")
            console.print(f"[green]   ./fix_apache_config.sh[/green]")
            return False
        # Check for active include (virtual host enabled)
        elif "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" in content:
            console.print(f"[green]✅ Virtual host configuration is enabled[/green]")
            return True
        # Check for incorrect relative path
        elif "Include conf/extra/httpd-vhosts.conf" in content:
            console.print(f"[yellow]⚠️ Found incorrect relative path in Apache config[/yellow]")
            console.print(f"[cyan]Current: Include conf/extra/httpd-vhosts.conf[/cyan]")
            console.print(f"[cyan]Should be: Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf[/cyan]")
            console.print(f"[blue]💡 To fix this, run:[/blue]")
            console.print(f"[green]   ./fix_apache_config.sh[/green]")
            return False
        # Check for commented relative path
        elif "#Include conf/extra/httpd-vhosts.conf" in content:
            console.print(f"[yellow]⚠️ Virtual host configuration is commented out (disabled)[/yellow]")
            console.print(f"[cyan]Found: #Include conf/extra/httpd-vhosts.conf[/cyan]")
            console.print(f"[blue]💡 To enable virtual hosts, run:[/blue]")
            console.print(f"[green]   ./fix_apache_config.sh[/green]")
            return False
        else:
            console.print(f"[yellow]⚠️ No include statement found for httpd-vhosts.conf[/yellow]")
            console.print(f"[blue]💡 To add the include statement, run:[/blue]")
            console.print(f"[green]   ./fix_apache_config.sh[/green]")
            return False
            
    except OSError as e:
        console.print(f"[red]❌ Error reading Apache config: {e}[/red]")
        return False


def check_vhost_status():
    """Display detailed virtual host configuration status."""
    console.print(Panel("[bold cyan]Virtual Host Status[/bold cyan]", expand=False))
    
    # Check Apache configuration file
    apache_conf_exists = Path(APACHE_CONF).exists()
    console.print(f"[blue]Apache Config:[/blue] {APACHE_CONF}")
    console.print(f"  Status: {'✅ Exists' if apache_conf_exists else '❌ Not found'}")
    
    # Check Apache configuration for issues
    if apache_conf_exists:
        apache_config_ok = check_apache_config()
        if not apache_config_ok:
            console.print()
    
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


def detect_mamp_running() -> Dict[str, bool]:
    """Detect whether MAMP services are running (Apache and MySQL) by scanning processes."""
    apache_running = False
    mysql_running = False

    try:
        # Use ps to list processes and look for MAMP-specific binaries
        result = subprocess.run([
            "/bin/ps", "aux"
        ], check=True, capture_output=True, text=True)
        output = result.stdout

        # Common MAMP process paths
        apache_markers = [
            "/Applications/MAMP/Library/bin/httpd",
            "/Applications/MAMP/bin/apache2/bin/httpd",
            "/Applications/MAMP/bin/apache2/bin/apachectl",
        ]
        mysql_markers = [
            "/Applications/MAMP/Library/bin/mysqld",
            "/Applications/MAMP/Library/bin/mysql.server",
        ]

        apache_running = any(marker in output for marker in apache_markers)
        mysql_running = any(marker in output for marker in mysql_markers)
    except subprocess.CalledProcessError:
        pass

    return {"apache": apache_running, "mysql": mysql_running}


def detect_php_path() -> Dict[str, Optional[str]]:
    """Detect the current PHP binary path and whether it points to MAMP PHP."""
    php_path = shutil.which("php")
    is_mamp_php = bool(php_path and "/Applications/MAMP/bin/php/" in php_path)

    php_version = None
    try:
        res = subprocess.run([php_path or "php", "-v"], check=True, capture_output=True, text=True)
        # First line like: PHP 8.2.x (cli) (built: ...)
        first_line = res.stdout.splitlines()[0] if res.stdout else ""
        m = re.search(r"PHP\s+([0-9]+\.[0-9]+\.[0-9]+)", first_line)
        if m:
            php_version = m.group(1)
    except Exception:
        pass

    # Try to infer MAMP PHP version from path
    mamp_php_version = None
    if is_mamp_php and php_path:
        # Path looks like: /Applications/MAMP/bin/php/php8.2.0/bin/php
        m = re.search(r"/Applications/MAMP/bin/php/(php[0-9.]+)/bin/php", php_path)
        if m:
            mamp_php_version = m.group(1)

    return {
        "php_path": php_path,
        "is_mamp_php": "yes" if is_mamp_php else "no",
        "php_version": php_version,
        "mamp_php_version_dir": mamp_php_version,
    }


def show_mamp_runtime_status():
    """Display whether MAMP is running and where PHP is pointing to."""
    console.print(Panel("[bold cyan]MAMP Runtime Status[/bold cyan]", expand=False))

    services = detect_mamp_running()
    console.print(f"[blue]Apache (MAMP):[/blue] {'✅ Running' if services.get('apache') else '❌ Stopped'}")
    console.print(f"[blue]MySQL (MAMP):[/blue] {'✅ Running' if services.get('mysql') else '❌ Stopped'}")

    php_info = detect_php_path()
    console.print("\n[bold]PHP Resolver[/bold]")
    console.print(f"  Path: {php_info.get('php_path') or 'Unknown'}")
    console.print(f"  Version: {php_info.get('php_version') or 'Unknown'}")
    console.print(f"  Using MAMP PHP: {php_info.get('is_mamp_php')}")
    if php_info.get('mamp_php_version_dir'):
        console.print(f"  MAMP PHP Dir: {php_info['mamp_php_version_dir']}")


def import_database():
    """Import a database from a SQL file into MAMP MySQL.
    - Supports .sql and .sql.gz
    - Creates database if it does not exist
    - Uses MAMP defaults (host 127.0.0.1, port 8889, user root, password root)
    """
    console.print("[blue]\n🗄️ Database Import[/blue]")

    # Validate mysql binary
    if not Path(MAMP_MYSQL).exists():
        console.print(f"[red bold]❌ MySQL client not found:[/red bold] {MAMP_MYSQL}")
        console.print("[cyan]Please ensure MAMP is installed and MySQL tools are available[/cyan]")
        return

    sql_path_str = Prompt.ask("Enter path to SQL file (.sql or .sql.gz)")
    sql_path = Path(sql_path_str).expanduser()
    if not sql_path.exists() or not sql_path.is_file():
        console.print(f"[red bold]❌ File not found:[/red bold] {sql_path}")
        return

    db_name = Prompt.ask("Enter target database name")
    if not db_name or not re.match(r"^[A-Za-z0-9_]+$", db_name):
        console.print("[red]❌ Invalid database name. Use letters, numbers, and underscore only[/red]")
        return

    host = "127.0.0.1"
    port = "8889"
    user = "root"
    # For non-interactive and typical MAMP default, use 'root'. Prompt if user wants custom
    use_default_pwd = Prompt.ask("Use default MAMP MySQL password 'root'?", choices=["y", "n"], default="y")
    if use_default_pwd == "y":
        password = "root"
    else:
        # getpass hides input in supported terminals; otherwise it will just read normally
        try:
            password = getpass("Enter MySQL password: ")
        except Exception:
            password = Prompt.ask("Enter MySQL password")

    # Prepare commands
    create_db_cmd = [
        MAMP_MYSQL, "-h", host, "-P", port, "-u", user, f"-p{password}",
        "-e", f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    ]

    is_gzip = sql_path.suffix == ".gz" or sql_path.name.endswith(".sql.gz")
    if is_gzip and not shutil.which("gunzip"):
        console.print("[red]❌ gunzip not found. Please install it to import .gz files[/red]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating database if missing...", total=None)

        try:
            subprocess.run(create_db_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red bold]❌ Failed to create database:[/red bold] {e}")
            if e.stderr:
                console.print(e.stderr.decode(errors='ignore'))
            return

        progress.update(task, description="Importing data into database...")

        try:
            if is_gzip:
                # gunzip -c file.sql.gz | mysql ... db
                sh_cmd = (
                    f"gunzip -c '{sql_path}' | "
                    f"'{MAMP_MYSQL}' -h {host} -P {port} -u {user} -p{password} {db_name}"
                )
            else:
                # cat file.sql | mysql ... db
                sh_cmd = (
                    f"cat '{sql_path}' | "
                    f"'{MAMP_MYSQL}' -h {host} -P {port} -u {user} -p{password} {db_name}"
                )

            subprocess.run(["/bin/sh", "-c", sh_cmd], check=True)
            console.print(f"[green]✅ Database imported into[/green] [bold]{db_name}[/bold]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red bold]❌ Import failed:[/red bold] {e}")
            return


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='fe_local',
        description='FE Local CLI - MAMP Virtual Host Management Tool',
        add_help=False  # We'll handle help manually
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show help message and exit'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version information and exit'
    )
    
    return parser.parse_args()


def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle help and version flags
    if args.help:
        show_help()
        sys.exit(0)
    
    if args.version:
        show_version()
        sys.exit(0)
    
    # Load configuration
    load_config()
    
    # Start interactive CLI
    check_mamp_installed()

    console.print(Panel(f"[bold cyan]MAMP HOST TOOL ({DOMAIN_SUFFIX})[/bold cyan]", expand=False))
    print("[green]1)[/green] Create new site")
    print("[green]2)[/green] Delete site")
    print("[green]3)[/green] List existing sites")
    print("[green]4)[/green] Create sample WordPress/Laravel project")
    print("[green]5)[/green] Check virtual host status")
    print("[green]6)[/green] Update default port")
    print("[green]7)[/green] Refresh domain configuration")
    print("[green]8)[/green] Manage domain suffix")
    print("[green]9)[/green] Import database into MAMP MySQL")
    print("[green]10)[/green] Show MAMP runtime status & PHP path")
    print("[green]0)[/green] Exit")

    choice = Prompt.ask("[yellow]Choose an option[/yellow]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

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

    elif choice == '8':
        manage_domain_suffix()

    elif choice == '9':
        import_database()

    elif choice == '10':
        show_mamp_runtime_status()

    elif choice == '0':
        console.print("[bold]Goodbye![/bold]", style="magenta")
        sys.exit(0)


if __name__ == '__main__':
    main()