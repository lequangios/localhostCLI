import os
import subprocess
import re
import json
from pathlib import Path
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
from functools import lru_cache
from typing import Optional, List, Dict, Any
import shutil
from getpass import getpass
import platform
from datetime import datetime

from .lamp_site_detector import LampSiteDetector
from .lamp_vhost_manager import LampVHostManager
from .lamp_hosts_mamager import LampHostsManager
from .lamp_vhost_manager import LampVHostManager

console = Console()

# Version information
VERSION = "1.0.0"
APP_NAME = "LAMP Site Manager"

# Configuration paths
LAMP_CONFIG_DIR = "/opt/fe_lamp"
LAMP_CONFIG_FILE = f"{LAMP_CONFIG_DIR}/fe_lamp.json"
SITE_CONFIG_FILE = f"{LAMP_CONFIG_DIR}/fe_lamp_site.json"

# Default settings
DEFAULT_PORT = 8080
DEFAULT_DOMAIN_SUFFIX = ".local"
DEFAULT_DOC_ROOT = "/opt/homebrew/var/www"

# Cache for vhost content to avoid repeated file reads
_vhost_cache: Optional[str] = None
_vhost_cache_mtime: Optional[float] = None


class LampSiteManager:
    """LAMP Site Manager for managing virtual hosts and local development sites."""
    
    def __init__(self):
        self.config = self._load_lamp_config()
        self.sites = self._load_sites_config()
        self.console = Console()
        self.detector = LampSiteDetector()
        
        # Get configuration from LAMP setup
        self.apache_port = self.config.get("system", {}).get("apache_port", DEFAULT_PORT)
        self.doc_root = self.config.get("system", {}).get("doc_root", DEFAULT_DOC_ROOT)
        self.httpd_conf = self.config.get("system", {}).get("httpd_conf", "/opt/homebrew/etc/httpd/httpd.conf")
        self.vhost_conf = "/opt/homebrew/etc/httpd/extra/httpd-vhosts.conf"
        self.domain_suffix = DEFAULT_DOMAIN_SUFFIX
        self.vhost = LampVHostManager(self.vhost_conf)
        self.hosts = LampHostsManager()
        self.vhost = LampVHostManager(self.vhost_conf)
        
    def _load_lamp_config(self) -> Dict[str, Any]:
        """Load LAMP configuration from fe_lamp.json."""
        try:
            if os.path.exists(LAMP_CONFIG_FILE):
                with open(LAMP_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not load LAMP config: {e}[/yellow]")
        
        return {}
    
    def _load_sites_config(self) -> Dict[str, Any]:
        """Load sites configuration from fe_lamp_site.json."""
        try:
            if os.path.exists(SITE_CONFIG_FILE):
                with open(SITE_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not load sites config: {e}[/yellow]")
        
        return {"sites": {}, "settings": {"domain_suffix": DEFAULT_DOMAIN_SUFFIX, "port": DEFAULT_PORT}}
    
    def _save_sites_config(self) -> bool:
        """Save sites configuration to fe_lamp_site.json."""
        try:
            # Ensure directory exists
            os.makedirs(LAMP_CONFIG_DIR, exist_ok=True)
            
            with open(SITE_CONFIG_FILE, 'w') as f:
                json.dump(self.sites, f, indent=2)
            return True
        except Exception as e:
            self.console.print(f"[red]Error saving sites config: {e}[/red]")
            return False
    
    def _ensure_sudo_permissions(self) -> bool:
        """Check if user has sudo permissions and request password if needed."""
        self.console.print("[yellow]🔐 Checking sudo permissions...[/yellow]")
        
        try:
            # Test sudo access without password first
            result = subprocess.run(
                ["sudo", "-n", "true"], 
                capture_output=True, 
                timeout=5
            )
            if result.returncode == 0:
                self.console.print("[green]✅ Sudo access confirmed[/green]")
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        # Check if we're in an interactive environment
        if not sys.stdin.isatty():
            self.console.print("[yellow]⚠️ Non-interactive environment detected[/yellow]")
            self.console.print("[cyan]Sudo will be requested when needed during operations[/cyan]")
            return True
        
        # If no passwordless sudo and we're interactive, request password
        self.console.print("[yellow]⚠️ Sudo access required for virtual host operations[/yellow]")
        self.console.print("[cyan]Please enter your password when prompted[/cyan]")
        
        try:
            # Request sudo password by running a simple command
            result = subprocess.run(
                ["sudo", "true"], 
                check=True,
                timeout=30
            )
            self.console.print("[green]✅ Sudo access granted[/green]")
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self.console.print("[red bold]❌ Sudo access denied or timeout[/red bold]")
            self.console.print("[yellow]Please ensure you have sudo privileges and try again[/yellow]")
            return False
    
    def _get_vhost_content(self) -> str:
        """Get vhost content with caching to avoid repeated file reads."""
        global _vhost_cache, _vhost_cache_mtime
        
        try:
            if not os.path.exists(self.vhost_conf):
                return ""
                
            current_mtime = os.path.getmtime(self.vhost_conf)
            if _vhost_cache is None or _vhost_cache_mtime != current_mtime:
                with open(self.vhost_conf, 'r') as f:
                    _vhost_cache = f.read()
                _vhost_cache_mtime = current_mtime
            return _vhost_cache
        except (FileNotFoundError, OSError):
            return ""
    
    def _check_vhost_module_enabled(self) -> bool:
        """Check if virtual host module is enabled in Apache configuration."""
        try:
            if not os.path.exists(self.httpd_conf):
                return False
                
            with open(self.httpd_conf, 'r') as f:
                content = f.read()
            
            # Check for vhost module inclusion (must be active, not commented)
            lines = content.split('\n')
            vhost_include = False
            vhost_module = False
            
            for line in lines:
                line = line.strip()
                # Check for active include (not commented)
                if line == f"Include {self.vhost_conf}":
                    vhost_include = True
                # Check for vhost module
                if "LoadModule vhost_alias_module" in line and not line.startswith('#'):
                    vhost_module = True
            
            # Both must be present and active (not commented out)
            return vhost_include and vhost_module
        except (FileNotFoundError, PermissionError):
            return False
    
    def _enable_vhost_module(self) -> bool:
        """Enable virtual host module in Apache configuration."""
        self.console.print("[blue]🔧 Enabling virtual host module...[/blue]")
        
        try:
            if not os.path.exists(self.httpd_conf):
                self.console.print(f"[red]Apache config not found: {self.httpd_conf}[/red]")
                return False
                
            with open(self.httpd_conf, 'r') as f:
                content = f.read()
            
            # Check if already enabled
            if self._check_vhost_module_enabled():
                self.console.print("[green]✅ Virtual host module already enabled[/green]")
                return True
            
            # Create backup
            self.console.print("[blue]💾 Creating backup...[/blue]")
            subprocess.run([
                "sudo", "cp", self.httpd_conf, f"{self.httpd_conf}.backup.$(date +%Y%m%d_%H%M%S)"
            ], check=True)
            
            # Add vhost module if not present
            if "LoadModule vhost_alias_module" not in content:
                self.console.print("[blue]🔧 Adding virtual host module...[/blue]")
                # Find the LoadModule section and add vhost module
                lines = content.split('\n')
                new_lines = []
                module_added = False
                
                for line in lines:
                    new_lines.append(line)
                    if line.startswith("LoadModule") and not module_added:
                        new_lines.append("LoadModule vhost_alias_module lib/httpd/modules/mod_vhost_alias.so")
                        module_added = True
                
                content = '\n'.join(new_lines)
            
            # Handle virtual host include configuration
            self.console.print("[blue]🔧 Configuring virtual host include...[/blue]")
            
            # Check if include is missing (add it)
            if f"Include {self.vhost_conf}" not in content:
                content += f"\n\n# Virtual hosts\nInclude {self.vhost_conf}\n"
                self.console.print("[green]✅ Added virtual host configuration[/green]")
            
            # Write back to file
            self.console.print("[blue]💾 Writing configuration...[/blue]")
            subprocess.run([
                "sudo", "sh", "-c",
                f"cat > {self.httpd_conf} << 'EOF'\n{content}\nEOF"
            ], check=True)
            
            # Test Apache configuration
            self.console.print("[blue]🧪 Testing Apache configuration...[/blue]")
            try:
                subprocess.run(["brew", "services", "info", "httpd"], check=True, capture_output=True)
                self.console.print("[green]✅ Apache configuration is valid[/green]")
            except subprocess.CalledProcessError:
                self.console.print("[yellow]⚠️ Apache configuration test failed, but changes were applied[/yellow]")
            
            self.console.print("[green]✅ Virtual host module enabled successfully[/green]")
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red bold]❌ Failed to enable virtual host module:[/red bold] {e}")
            self.console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
            return False
        except (FileNotFoundError, PermissionError) as e:
            self.console.print(f"[red bold]❌ Cannot access Apache configuration:[/red bold] {e}")
            return False
    
    def _check_and_enable_vhost(self) -> bool:
        """Check and enable virtual host functionality if needed."""
        self.console.print("[blue]🔍 Checking virtual host configuration...[/blue]")
        
        if self._check_vhost_module_enabled():
            self.console.print("[green]✅ Virtual host module is enabled[/green]")
            return True
        else:
            self.console.print("[yellow]⚠️ Virtual host module not enabled[/yellow]")
            self.console.print("[cyan]Attempting to enable virtual host module...[/cyan]")
            
            if self._enable_vhost_module():
                self.console.print("[green]✅ Virtual host module enabled successfully[/green]")
                self.console.print("[yellow]⚠️ Apache restart required for changes to take effect[/yellow]")
                return True
            else:
                self.console.print("[red bold]❌ Failed to enable virtual host module[/red bold]")
                return False
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if domain already exists in vhost config."""
        return self.vhost.find_block_by_server_name(domain) is not None
    
    def _check_hosts_entry_exists(self, domain: str) -> bool:
        """Check if domain already exists in /etc/hosts file."""
        return self.hosts.has_domain(domain)
    
    def _validate_new_site(self, domain: str) -> bool:
        """Validate that the new site doesn't already exist."""
        vhost_exists = self._check_domain_exists(domain)
        hosts_exists = self._check_hosts_entry_exists(domain)
        
        if vhost_exists or hosts_exists:
            self.console.print(f"[red bold]❌ Site '{domain}' already exists![/red bold]")
            
            if vhost_exists:
                self.console.print(f"[yellow]  • Virtual host configuration found[/yellow]")
            if hosts_exists:
                self.console.print(f"[yellow]  • Hosts file entry found[/yellow]")
            
            self.console.print(f"[cyan]Please choose a different name or delete the existing site first[/cyan]")
            return False
        
        return True
    
    def create_site(self, site_name: str, project_path: str, description: str = "", website_type: str = None) -> bool:
        """Create a new virtual host site."""
        domain = site_name if site_name.endswith(self.domain_suffix) else site_name + self.domain_suffix
        
        # Validate that the site doesn't already exist
        if not self._validate_new_site(domain):
            return False

        # Validate provided path
        path = Path(project_path).expanduser()
        if not path or not path.exists():
            self.console.print(f"[red bold]❌ Path not found:[/red bold] {path}")
            return False

        # Determine actual document root
        actual_docroot = path

        # Use provided website_type or auto-detect
        if website_type:
            project_type = website_type
        else:
            try:
                project_type = self.detector.detect(str(path))
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
                    self.console.print(
                        f"[red bold]❌ Laravel detected but 'public' directory not found in:[/red bold] {path}"
                    )
                    return False
                actual_docroot = laravel_public
            else:
                # path might already be the public directory
                actual_docroot = path

        # Final safety: docroot must exist
        if not actual_docroot.exists():
            self.console.print(f"[red bold]❌ DocumentRoot not found:[/red bold] {actual_docroot}")
            return False

        self.console.print(f"[blue]🚀 Creating virtual host for {domain}...[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Creating virtual host...", total=None)

            # Write to vhost config file via manager
            progress.update(task, description="Writing virtual host configuration...")
            added = self.vhost.add_vhost(domain=domain, document_root=str(actual_docroot), port=self.apache_port)
            if not added:
                self.console.print(f"[yellow]⚠️ A VirtualHost for {domain} already exists[/yellow]")
                return False
            self.console.print("[green]✅ Virtual host configuration written[/green]")

            # Add to hosts file and restart Apache
            progress.update(task, description="Adding to hosts file and restarting Apache...")

            try:
                changed = self.hosts.ensure_entry("127.0.0.1", domain)
                subprocess.run(["brew", "services", "restart", "httpd"], check=True)
                self.console.print("[green]✅ Hosts file updated and Apache restarted[/green]")
                
                # Save site to configuration
                self.sites["sites"][domain] = {
                    "name": site_name,
                    "domain": domain,
                    "path": str(actual_docroot),
                    "project_type": project_type,
                    "description": description,
                    "port": self.apache_port,
                    "created_at": datetime.now().isoformat()
                }
                self._save_sites_config()
                
                return True
            except subprocess.CalledProcessError as e:
                self.console.print(f"[red bold]❌ Failed to update hosts file or restart Apache:[/red bold] {e}")
                self.console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
                return False

    def delete_site(self, site_name: str) -> bool:
        """Delete a virtual host site."""
        domain = site_name if site_name.endswith(self.domain_suffix) else site_name + self.domain_suffix

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Deleting virtual host...", total=None)
            
            # Remove block via manager
            progress.update(task, description="Updating virtual host configuration...")
            removed = self.vhost.remove_vhost(domain)
            if not removed:
                self.console.print(f"[yellow]⚠️ Site not found:[/yellow] {domain}")
                return False
            
            progress.update(task, description="Removing from hosts file and restarting Apache...")

                # Safely remove only the specific domain token from /etc/hosts (any IP)
                try:
                    self.hosts.remove_domain(domain)
                    subprocess.run(["brew", "services", "restart", "httpd"], check=True)
                    
                    # Remove from sites configuration
                    if domain in self.sites["sites"]:
                        del self.sites["sites"][domain]
                        self._save_sites_config()
                    
                    self.console.print(f"[red]🗑️ Deleted virtual host:[/red] {domain}")
                    return True
                except subprocess.CalledProcessError as e:
                    self.console.print(f"[red bold]❌ Failed to update hosts file or restart Apache:[/red bold] {e}")
                    self.console.print(f"[yellow]Please ensure you have sudo privileges[/yellow]")
                    return False
            else:
                self.console.print(f"[yellow]⚠️ Site not found:[/yellow] {domain}")
                return False

    def list_sites(self) -> None:
        """List all virtual host sites."""
        self.console.print("[bold cyan]\n📋 Registered sites:[/bold cyan]")

        sites = self.sites.get("sites", {})
        if not sites:
            self.console.print("[yellow]No sites found in configuration.[/yellow]")
            return

        # Sort by domain for stable output
        for domain in sorted(sites.keys()):
            info = sites.get(domain, {})
            site_name = info.get("name", domain.split('.')[0])
            path_str = info.get("path", "")
            project_type = info.get("project_type", "Unknown")
            description = info.get("description", "")
            port = info.get("port") or self._get_domain_port(domain) or self.apache_port

            # Resolve status
            path = Path(path_str) if path_str else None
            path_exists = bool(path and path.exists())
            vhost_exists = self.vhost.find_block_by_server_name(domain) is not None
            hosts_exists = self.hosts.has_domain(domain)

            # Auto-detect type if missing and path exists
            if project_type == "Unknown" and path_exists:
                try:
                    project_type = self.detector.detect(str(path))
                except Exception:
                    project_type = "Unknown"

            type_emoji = {
                'WordPress': '🔵',
                'Laravel': '🔴',
                'PHP': '🟡',
                'HTML': '🟢',
                'Symfony': '🟣',
                'Drupal': '🟠',
                'Magento': '🟤',
                'JavaScript': '🟦',
                'Unknown': '⚪'
            }.get(project_type, '⚪')

            status_bits = []
            status_bits.append("[green]PATH[/green]" if path_exists else "[red]PATH[/red]")
            status_bits.append("[green]VHOST[/green]" if vhost_exists else "[red]VHOST[/red]")
            status_bits.append("[green]HOSTS[/green]" if hosts_exists else "[red]HOSTS[/red]")
            status_str = " ".join(status_bits)

            url = f"http://{domain}:{port}"
            self.console.print(f"• [bold]{site_name}[/bold] — {type_emoji} {project_type}  {status_str}")
            self.console.print(f"  🌐 {url}")
            self.console.print(f"  📁 {path_str if path_str else 'Unknown path'}")
            if description:
                self.console.print(f"  📝 {description}")

    def _get_domain_path(self, domain: str) -> Optional[Path]:
        """Get the document root path for a domain from vhost manager."""
        from .lamp_vhost_manager import LampVHostManager  # local import to avoid cycles in editors
        block = self.vhost.find_block_by_server_name(domain)
        if block and block.document_root:
            return Path(block.document_root)
        return None

    def _get_domain_port(self, domain: str) -> Optional[int]:
        """Get the port number for a domain from vhost config."""
        block = self.vhost.find_block_by_server_name(domain)
        return block.port if block and block.port is not None else None

    def check_status(self) -> None:
        """Check virtual host configuration status."""
        self.console.print(Panel("[bold cyan]Virtual Host Status[/bold cyan]", expand=False))
        
        # Check Apache configuration file
        apache_conf_exists = os.path.exists(self.httpd_conf)
        self.console.print(f"[blue]Apache Config:[/blue] {self.httpd_conf}")
        self.console.print(f"  Status: {'✅ Exists' if apache_conf_exists else '❌ Not found'}")
        
        # Check virtual host config file
        vhost_conf_exists = os.path.exists(self.vhost_conf)
        self.console.print(f"[blue]Virtual Host Config:[/blue] {self.vhost_conf}")
        self.console.print(f"  Status: {'✅ Exists' if vhost_conf_exists else '❌ Not found'}")
        
        # Check virtual host module
        vhost_enabled = self._check_vhost_module_enabled()
        self.console.print(f"[blue]Virtual Host Module:[/blue] {'✅ Enabled' if vhost_enabled else '❌ Disabled'}")
        
        # Show current port
        self.console.print(f"[blue]Current Port:[/blue] {self.apache_port}")
        
        # Summary
        self.console.print("\n[bold]Summary:[/bold]")
        if apache_conf_exists and vhost_conf_exists and vhost_enabled:
            self.console.print("[green]✅ Virtual host functionality is fully configured and ready[/green]")
        else:
            self.console.print("[yellow]⚠️ Virtual host functionality needs attention[/yellow]")
        
        # Show current virtual hosts
        self.console.print("\n[bold]Current Virtual Hosts:[/bold]")
        self.list_sites()

    def ensure_setup(self) -> bool:
        """Ensure virtual host setup is complete."""
        if not self._ensure_sudo_permissions():
            return False
        
        return self._check_and_enable_vhost()
