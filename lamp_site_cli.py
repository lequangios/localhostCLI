#!/usr/bin/env python3
"""
LAMP Site CLI - Virtual Host Management for LAMP Stack
Similar to mphm_cli.py but for LAMP stack using /opt/fe_lamp/ configuration
"""

import os
import sys
import argparse
from pathlib import Path
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lamp_site_manager import LampSiteManager

console = Console()

# Version information
VERSION = "1.0.0"
APP_NAME = "LAMP Site CLI"

# Default settings
DEFAULT_DOMAIN_SUFFIX = ".local"
DEFAULT_PORT = 8080


def show_help():
    """Display help information for the CLI tool."""
    console.print(Panel(f"[bold cyan]{APP_NAME} v{VERSION}[/bold cyan]", expand=False))
    console.print()
    
    console.print("[bold]DESCRIPTION[/bold]")
    console.print("LAMP Site CLI is a powerful tool for managing LAMP virtual hosts and local development environments.")
    console.print()
    
    console.print("[bold]USAGE[/bold]")
    console.print("  lamp_site_cli [OPTIONS]")
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
    console.print("  • Virtual host status monitoring")
    console.print("  • Sample project template creation")
    console.print()
    
    console.print("[bold]EXAMPLES[/bold]")
    console.print("  lamp_site_cli                    # Start interactive CLI")
    console.print("  lamp_site_cli --help             # Show this help")
    console.print("  lamp_site_cli --version          # Show version")
    console.print()
    
    console.print("[bold]REQUIREMENTS[/bold]")
    console.print("  • LAMP stack installed and running")
    console.print("  • Sudo privileges for virtual host operations")
    console.print("  • macOS (tested on macOS)")
    console.print()
    
    console.print("[bold]SUPPORT[/bold]")
    console.print("  For issues and feature requests, please contact levietquangt2@gmail.com.")
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


def create_site():
    """Create a new virtual host site."""
    console.print("[blue]🚀 Create New Site[/blue]")
    
    site_name = Prompt.ask("Enter site name (e.g., mysite)")
    project_path = Prompt.ask("Enter full project folder path")
    site_description = Prompt.ask("Enter site description (optional)", default="")
    
    # Website type selection
    console.print("\n[bold]Select website type:[/bold]")
    console.print("[green]P)[/green] PHP")
    console.print("[green]L)[/green] Laravel")
    console.print("[green]S)[/green] Symfony")
    console.print("[green]W)[/green] WordPress")
    console.print("[green]D)[/green] Drupal")
    console.print("[green]M)[/green] Magento")
    console.print("[green]J)[/green] JavaScript")
    console.print("[green]H)[/green] HTML")
    console.print("[green]A)[/green] Auto-detect")
    
    website_type_choice = Prompt.ask("[yellow]Choose website type[/yellow]", choices=["P", "L", "S", "W", "D", "M", "J", "H", "A"])
    
    # Map choice to website type
    website_type_map = {
        "P": "PHP",
        "L": "Laravel", 
        "S": "Symfony",
        "W": "WordPress",
        "D": "Drupal",
        "M": "Magento",
        "J": "JavaScript",
        "H": "HTML",
        "A": "Auto-detect"
    }
    
    selected_type = website_type_map[website_type_choice]
    
    path = Path(project_path).expanduser()
    if not path.exists():
        console.print("[red]❌ Folder not found.[/red]")
        return
    
    # Initialize site manager
    manager = LampSiteManager()
    
    # Ensure setup is complete
    if not manager.ensure_setup():
        console.print("[red]❌ Failed to setup virtual host functionality[/red]")
        return
    
    # Detect or use selected project type
    if selected_type == "Auto-detect":
        project_type = manager.detector.detect(str(path))
        console.print(f"[cyan]Auto-detected project type:[/cyan] [bold]{project_type}[/bold]")
    else:
        project_type = selected_type
        console.print(f"[cyan]Selected project type:[/cyan] [bold]{project_type}[/bold]")
    
    # Create the site with additional metadata
    if manager.create_site(site_name, str(path), description=site_description, website_type=project_type):
        domain = site_name if site_name.endswith(manager.domain_suffix) else site_name + manager.domain_suffix
        console.print(f"[green]✅ Site created:[/green] http://{domain}:{manager.apache_port}")
        console.print(f"[cyan]Description:[/cyan] {site_description if site_description else 'No description'}")
        console.print(f"[cyan]Type:[/cyan] {project_type}")
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(f"http://{domain}:{manager.apache_port}")
        except:
            pass
    else:
        console.print("[yellow]⚠️ Site creation cancelled[/yellow]")


def delete_site():
    """Delete a virtual host site."""
    console.print("[blue]🗑️ Delete Site[/blue]")
    
    site_name = Prompt.ask("Enter site name or domain to delete")
    
    # Initialize site manager
    manager = LampSiteManager()
    
    if manager.delete_site(site_name):
        console.print(f"[green]✅ Site deleted successfully[/green]")
    else:
        console.print("[yellow]⚠️ Site deletion failed or site not found[/yellow]")


def list_sites():
    """List all virtual host sites."""
    console.print("[blue]📋 List Sites[/blue]")
    
    # Initialize site manager
    manager = LampSiteManager()
    manager.list_sites()


def check_status():
    """Check virtual host configuration status."""
    console.print("[blue]🔍 Check Status[/blue]")
    
    # Initialize site manager
    manager = LampSiteManager()
    manager.check_status()


def create_project_template():
    """Create project template with progress indicators and optimized operations."""
    project_type = Prompt.ask("Choose project type", choices=["wordpress", "laravel", "php", "html"])
    name = Prompt.ask("Enter project name")
    base_path = Path.home() / "Sites" / name
    base_path.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        if project_type == "wordpress":
            task = progress.add_task("Downloading WordPress...", total=None)
            import subprocess
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
            import subprocess
            subprocess.run([
                "composer", "create-project", "--prefer-dist", 
                "laravel/laravel", str(base_path / "public")
            ], check=True)
            
        elif project_type == "php":
            task = progress.add_task("Creating PHP project...", total=None)
            # Create a simple PHP project
            (base_path / "public").mkdir(exist_ok=True)
            (base_path / "public" / "index.php").write_text("""<?php
echo "<h1>Welcome to PHP!</h1>";
echo "<p>This is a simple PHP project.</p>";
phpinfo();
?>""")
            
        elif project_type == "html":
            task = progress.add_task("Creating HTML project...", total=None)
            # Create a simple HTML project
            (base_path / "public").mkdir(exist_ok=True)
            (base_path / "public" / "index.html").write_text("""<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome to HTML!</h1>
    <p>This is a simple HTML project.</p>
</body>
</html>""")

        progress.update(task, description="Setting up virtual host...")
        
        # Initialize site manager
        manager = LampSiteManager()
        
        # Ensure setup is complete
        if not manager.ensure_setup():
            console.print("[red]❌ Failed to setup virtual host functionality[/red]")
            return
        
        if manager.create_site(name, str(base_path / "public")):
            domain = name if name.endswith(manager.domain_suffix) else name + manager.domain_suffix
            console.print(f"[green]✅ {project_type.capitalize()} site created:[/green] http://{domain}:{manager.apache_port}")
            
            # Try to open in browser
            try:
                import webbrowser
                webbrowser.open(f"http://{domain}:{manager.apache_port}")
            except:
                pass
        else:
            console.print("[yellow]⚠️ Site creation cancelled[/yellow]")


def manage_domain_suffix():
    """Manage domain suffix configuration."""
    console.print("[blue]🔧 Domain Suffix Management[/blue]")
    
    # Initialize site manager
    manager = LampSiteManager()
    
    console.print(f"[cyan]Current domain suffix:[/cyan] [bold]{manager.domain_suffix}[/bold]")
    console.print()
    
    console.print("[bold]Options:[/bold]")
    console.print("1) Change domain suffix")
    console.print("2) Reset to default (.local)")
    console.print("3) Show current configuration")
    console.print("0) Back to main menu")
    
    choice = Prompt.ask("[yellow]Choose an option[/yellow]", choices=["0", "1", "2", "3"])
    
    if choice == '1':
        new_suffix = Prompt.ask("[cyan]Enter new domain suffix (e.g., .local, .dev, .test)[/cyan]")
        
        # Validate domain suffix
        if not new_suffix.startswith('.'):
            new_suffix = '.' + new_suffix
        
        # Check for valid characters
        import re
        if not re.match(r'^\.([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+$', new_suffix):
            console.print("[red]❌ Invalid domain suffix format[/red]")
            console.print("[yellow]Please use format like: .local, .dev, .test[/yellow]")
            return
        
        old_suffix = manager.domain_suffix
        manager.domain_suffix = new_suffix
        
        console.print(f"[green]✅ Domain suffix changed from {old_suffix} to {manager.domain_suffix}[/green]")
        
        # Ask if user wants to save
        if Confirm.ask("[yellow]Save this configuration?[/yellow]"):
            # Update settings in sites config
            manager.sites["settings"]["domain_suffix"] = new_suffix
            manager._save_sites_config()
            console.print("[cyan]💡 New sites will use the updated domain suffix[/cyan]")
            console.print("[yellow]⚠️ Existing sites will keep their current domains[/yellow]")
        else:
            manager.domain_suffix = old_suffix
            console.print("[yellow]⚠️ Changes discarded[/yellow]")
    
    elif choice == '2':
        old_suffix = manager.domain_suffix
        manager.domain_suffix = ".local"
        console.print(f"[green]✅ Domain suffix reset to {manager.domain_suffix}[/green]")
        
        if Confirm.ask("[yellow]Save this configuration?[/yellow]"):
            manager.sites["settings"]["domain_suffix"] = ".local"
            manager._save_sites_config()
        else:
            manager.domain_suffix = old_suffix
            console.print("[yellow]⚠️ Changes discarded[/yellow]")
    
    elif choice == '3':
        console.print("\n[bold]Current Configuration:[/bold]")
        console.print(f"  Domain Suffix: {manager.domain_suffix}")
        console.print(f"  Apache Port: {manager.apache_port}")
        console.print(f"  Document Root: {manager.doc_root}")
        console.print(f"  Apache Config: {manager.httpd_conf}")
        console.print(f"  VHost Config: {manager.vhost_conf}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='lamp_site_cli',
        description='LAMP Site CLI - Virtual Host Management Tool',
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
    
    # Start interactive CLI
    console.print(Panel(f"[bold cyan]LAMP SITE TOOL ({DEFAULT_DOMAIN_SUFFIX})[/bold cyan]", expand=False))
    print("[green]1)[/green] Create new site")
    print("[green]2)[/green] List existing sites")
    print("[red]3)[/red] Delete site")
    print("[green]4)[/green] Create sample WordPress/Laravel/PHP/HTML project")
    print("[green]5)[/green] Check virtual host status")
    print("[green]6)[/green] Manage domain suffix")
    print("[green]0)[/green] Exit")

    choice = Prompt.ask("[yellow]Choose an option[/yellow]", choices=["0", "1", "2", "3", "4", "5", "6"])

    if choice == '1':
        create_site()

    elif choice == '2':
        list_sites()

    elif choice == '3':
        delete_site()

    elif choice == '4':
        create_project_template()

    elif choice == '5':
        check_status()

    elif choice == '6':
        manage_domain_suffix()

    elif choice == '0':
        console.print("[bold]Goodbye![/bold]", style="magenta")
        sys.exit(0)


if __name__ == '__main__':
    main()
