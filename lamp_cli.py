#!/usr/bin/env python3

import argparse
import os
import sys
from typing import List, Optional

# Import LampManager with robust fallback for both source and bundled modes
def _get_binary_name() -> str:
    name = os.path.basename(sys.argv[0]) or "lamp_cli"
    if name.endswith(".py"):
        name = "lamp_cli"
    return os.environ.get("FE_LAMP_NAME", name)

BINARY_NAME = _get_binary_name()

# Robust import for bundled/source environments (mirror of lamp_site_cli)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
try:
    # In bundled onefile, PyInstaller often exposes modules at top-level
    from lamp_manager import LampManager  # type: ignore  # noqa: E402
except Exception:
    try:
        # When running from source with package layout
        from src.lamp_manager import LampManager  # type: ignore  # noqa: E402
    except Exception:
        # Last resort: ensure src in sys.path and import plain
        if SRC_DIR not in sys.path:
            sys.path.insert(0, SRC_DIR)
        from lamp_manager import LampManager  # type: ignore  # noqa: E402


def status_command(_: argparse.Namespace) -> int:
    manager = LampManager()
    lines = manager.get_status_lines()
    print("\n".join(lines))
    return 0


def install_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    manager.install_or_update(db_choice=args.db or "mysql")
    print("LAMP components installed/updated and configured successfully!")
    return 0


def uninstall_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    manager.uninstall(
        export_db=args.export_db,
        export_path=args.export_path,
        db_user=args.db_user,
        db_password=args.db_password,
    )
    return 0


def configure_php_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.setup_and_test_php():
        print("PHP configuration and test completed successfully!")
        return 0
    else:
        print("PHP configuration or test failed.", file=sys.stderr)
        return 1


def configure_mysql_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    password = args.password or "fe_root"
    if manager.setup_mysql_complete(password):
        print("MySQL configuration completed successfully!")
        return 0
    else:
        print("MySQL configuration failed.", file=sys.stderr)
        return 1


def test_mysql_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    password = args.password or "fe_root"
    if manager.test_mysql_connection("root", password):
        print("MySQL connection test successful!")
        return 0
    else:
        print("MySQL connection test failed.", file=sys.stderr)
        return 1


def configure_phpmyadmin_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.setup_phpmyadmin_complete():
        print("phpMyAdmin configuration completed successfully!")
        return 0
    else:
        print("phpMyAdmin configuration failed.", file=sys.stderr)
        return 1


def test_phpmyadmin_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.test_phpmyadmin_setup():
        print("phpMyAdmin test successful!")
        return 0
    else:
        print("phpMyAdmin test failed.", file=sys.stderr)
        return 1


def import_database_command(args: argparse.Namespace) -> int:
    """Import a database from a SQL file into MySQL.
    - Supports .sql and .sql.gz files
    - Creates database if it does not exist
    - Uses MySQL connection parameters from args or defaults
    """
    import subprocess
    import shutil
    from pathlib import Path
    from getpass import getpass
    import re
    
    # Get SQL file path
    sql_path_str = args.sql_file
    sql_path = Path(sql_path_str).expanduser()
    if not sql_path.exists() or not sql_path.is_file():
        print(f"Error: File not found: {sql_path}", file=sys.stderr)
        return 1
    
    # Get database name
    db_name = args.database
    if not db_name or not re.match(r"^[A-Za-z0-9_]+$", db_name):
        print("Error: Invalid database name. Use letters, numbers, and underscore only", file=sys.stderr)
        return 1
    
    # Get connection parameters
    host = args.host or "127.0.0.1"
    port = args.port or "3306"
    user = args.user or "root"
    password = args.password or "fe_root"
    
    # If no password provided and not using default, prompt for it
    if not args.password and not args.user:
        try:
            password = getpass("Enter MySQL password: ")
        except Exception:
            password = input("Enter MySQL password: ")
    
    # Find MySQL client
    mysql_client = shutil.which("mysql")
    if not mysql_client:
        print("Error: MySQL client not found. Please ensure MySQL is installed and in PATH", file=sys.stderr)
        return 1
    
    # Prepare commands
    create_db_cmd = [
        mysql_client, "-h", host, "-P", port, "-u", user, f"-p{password}",
        "-e", f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    ]
    
    # Check if file is gzipped
    is_gzip = sql_path.suffix == ".gz" or sql_path.name.endswith(".sql.gz")
    if is_gzip and not shutil.which("gunzip"):
        print("Error: gunzip not found. Please install it to import .gz files", file=sys.stderr)
        return 1
    
    print(f"Creating database '{db_name}' if it doesn't exist...")
    try:
        subprocess.run(create_db_cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to create database: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr.decode(errors='ignore'), file=sys.stderr)
        return 1
    
    print(f"Importing data into database '{db_name}'...")
    try:
        if is_gzip:
            # gunzip -c file.sql.gz | mysql ... db
            sh_cmd = (
                f"gunzip -c '{sql_path}' | "
                f"'{mysql_client}' -h {host} -P {port} -u {user} -p{password} {db_name}"
            )
        else:
            # cat file.sql | mysql ... db
            sh_cmd = (
                f"cat '{sql_path}' | "
                f"'{mysql_client}' -h {host} -P {port} -u {user} -p{password} {db_name}"
            )
        
        subprocess.run(["/bin/sh", "-c", sh_cmd], check=True)
        print(f"✅ Database imported successfully into '{db_name}'")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Import failed: {e}", file=sys.stderr)
        return 1


def configure_apache_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    port = args.port or 8080
    doc_root = args.doc_root or "/opt/fe_lamp/www"
    
    if manager.configure_apache_complete(port, doc_root):
        print("Apache configuration completed successfully!")
        return 0
    else:
        print("Apache configuration failed.", file=sys.stderr)
        return 1


def show_apache_config_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    config = manager.get_current_apache_config()
    
    print("Current Apache Configuration:")
    print(f"  Config File: {config['config_file']}")
    print(f"  Port: {config['port'] or 'Not configured'}")
    print(f"  Document Root: {config['document_root'] or 'Not configured'}")
    return 0


def enable_mod_rewrite_command(args: argparse.Namespace) -> int:
    """Enable mod_rewrite for Apache."""
    manager = LampManager()
    am = manager._get_apache_manager()
    if not am:
        print("❌ Failed to get Apache manager", file=sys.stderr)
        return 1
    
    if am.enable_mod_rewrite():
        print("✅ mod_rewrite enabled successfully!")
        return 0
    else:
        print("❌ Failed to enable mod_rewrite", file=sys.stderr)
        return 1


def disable_mod_rewrite_command(args: argparse.Namespace) -> int:
    """Disable mod_rewrite for Apache."""
    manager = LampManager()
    am = manager._get_apache_manager()
    if not am:
        print("❌ Failed to get Apache manager", file=sys.stderr)
        return 1
    
    if am.disable_mod_rewrite():
        print("✅ mod_rewrite disabled successfully!")
        return 0
    else:
        print("❌ Failed to disable mod_rewrite", file=sys.stderr)
        return 1


def check_rewrite_status_command(args: argparse.Namespace) -> int:
    """Check mod_rewrite status."""
    manager = LampManager()
    am = manager._get_apache_manager()
    if not am:
        print("❌ Failed to get Apache manager", file=sys.stderr)
        return 1
    
    status = am.mod_rewrite_status()
    print("mod_rewrite Status:")
    print(f"  Module Enabled: {'✅ Yes' if status['enabled'] else '❌ No'}")
    print(f"  AllowOverride: {status['allow_override']}")
    
    if status['enabled'] and status['allow_override'] == 'All':
        print("✅ mod_rewrite is fully configured and ready to use")
        return 0
    else:
        print("⚠️ mod_rewrite needs configuration")
        return 1


def export_databases_command(args: argparse.Namespace) -> int:
    """Export all databases with enhanced options."""
    manager = LampManager()
    
    # Get connection parameters
    user = args.user or "root"
    password = args.password or "fe_root"
    output_dir = args.output_dir or "./db_exports"
    schema_only = args.schema_only
    no_compress = args.no_compress
    
    print(f"Exporting databases to: {output_dir}")
    print(f"Schema only: {'Yes' if schema_only else 'No'}")
    print(f"Compression: {'Disabled' if no_compress else 'Enabled (.sql.gz)'}")
    
    if args.database:
        # Export single database
        result = manager.export_single_database(
            database=args.database,
            export_dir=output_dir,
            user=user,
            password=password,
            schema_only=schema_only,
            compress=not no_compress
        )
        if result:
            print(f"✅ Single database export completed: {result}")
            return 0
        else:
            print("❌ Single database export failed", file=sys.stderr)
            return 1
    else:
        # Export all databases
        results = manager.export_all_databases(
            export_dir=output_dir,
            user=user,
            password=password,
            schema_only=schema_only,
            compress=not no_compress
        )
        if results:
            print(f"✅ All databases export completed. {len(results)} files exported:")
            for file_path in results:
                print(f"  - {file_path}")
            return 0
        else:
            print("❌ Database export failed", file=sys.stderr)
            return 1


def start_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.start_services():
        print("LAMP services started successfully!")
        return 0
    else:
        print("Failed to start LAMP services.", file=sys.stderr)
        return 1


def stop_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.stop_services():
        print("LAMP services stopped successfully!")
        return 0
    else:
        print("Failed to stop LAMP services.", file=sys.stderr)
        return 1


def restart_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    if manager.restart_services():
        print("LAMP services restarted successfully!")
        return 0
    else:
        print("Failed to restart LAMP services.", file=sys.stderr)
        return 1


# Argument parser

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=BINARY_NAME,
        description="LAMP Stack Management CLI - Manage Apache, PHP, MySQL, and phpMyAdmin",
        epilog=f"""
Examples:
  {BINARY_NAME} status                           # Check installation status
  {BINARY_NAME} install                          # Install LAMP stack
  {BINARY_NAME} configure-apache --port 80       # Configure Apache on port 80
  {BINARY_NAME} show-apache-config               # Show current Apache settings
  {BINARY_NAME} enable-mod-rewrite                # Enable mod_rewrite for Apache
  {BINARY_NAME} check-rewrite-status             # Check mod_rewrite status
  {BINARY_NAME} export-databases                 # Export all databases (compressed)
  {BINARY_NAME} export-databases --schema-only   # Export schema only
  {BINARY_NAME} export-databases --database mydb  # Export specific database
  {BINARY_NAME} import-database backup.sql mydb  # Import database from SQL file
  {BINARY_NAME} start                            # Start all services
  {BINARY_NAME} stop                             # Stop all services
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument('-v', '--version', action='version', version=f"{BINARY_NAME} v1.0.0")

    sub = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = sub.add_parser(
        "status", 
        help="Show installation and service status",
        description="Check which LAMP components are installed and their current status"
    )
    p_status.set_defaults(func=status_command)

    # install
    p_install = sub.add_parser(
        "install", 
        help="Install or update LAMP components via Homebrew",
        description="Install Apache, PHP, MySQL/MariaDB, and phpMyAdmin. Automatically configures all components."
    )
    p_install.add_argument("--db", choices=["mysql", "mariadb"], default="mysql", help="Database server to install (default: mysql)")
    p_install.set_defaults(func=install_command)

    # uninstall
    p_uninstall = sub.add_parser(
        "uninstall", 
        help="Uninstall LAMP components while preserving website directory",
        description="Remove all LAMP components while preserving website directories. Optionally export databases."
    )
    p_uninstall.add_argument("--export-db", action="store_true", help="Export all databases before uninstalling")
    p_uninstall.add_argument("--export-path", help="Directory to store exported SQL dump (default: ./db_exports)")
    p_uninstall.add_argument("--db-user", default="root", help="Database user for export (default: root)")
    p_uninstall.add_argument("--db-password", default=os.environ.get("MYSQL_PWD"), help="Database password for export (or set MYSQL_PWD env)")
    p_uninstall.set_defaults(func=uninstall_command)

    # start
    p_start = sub.add_parser(
        "start", 
        help="Start LAMP services",
        description="Start Apache, MySQL, and other LAMP services"
    )
    p_start.set_defaults(func=start_command)

    # stop
    p_stop = sub.add_parser(
        "stop", 
        help="Stop LAMP services",
        description="Stop all running LAMP services"
    )
    p_stop.set_defaults(func=stop_command)

    # restart
    p_restart = sub.add_parser(
        "restart", 
        help="Restart LAMP services",
        description="Restart all LAMP services (stop then start)"
    )
    p_restart.set_defaults(func=restart_command)

    # configure-php
    p_configure_php = sub.add_parser(
        "configure-php", 
        help="Configure Apache for PHP and test the setup",
        description="Configure Apache to work with PHP and test PHP setup"
    )
    p_configure_php.set_defaults(func=configure_php_command)

    # configure-mysql
    p_configure_mysql = sub.add_parser(
        "configure-mysql", 
        help="Configure MySQL root user with password",
        description="Set up MySQL root user with specified password"
    )
    p_configure_mysql.add_argument("--password", default="fe_root", help="MySQL root password (default: fe_root)")
    p_configure_mysql.set_defaults(func=configure_mysql_command)

    # test-mysql
    p_test_mysql = sub.add_parser(
        "test-mysql", 
        help="Test MySQL connection",
        description="Test MySQL connection with current credentials"
    )
    p_test_mysql.add_argument("--password", default="fe_root", help="MySQL root password (default: fe_root)")
    p_test_mysql.set_defaults(func=test_mysql_command)

    # configure-phpmyadmin
    p_configure_phpmyadmin = sub.add_parser(
        "configure-phpmyadmin", 
        help="Configure phpMyAdmin for Apache",
        description="Configure phpMyAdmin to work with Apache and MySQL"
    )
    p_configure_phpmyadmin.set_defaults(func=configure_phpmyadmin_command)

    # test-phpmyadmin
    p_test_phpmyadmin = sub.add_parser(
        "test-phpmyadmin", 
        help="Test phpMyAdmin setup",
        description="Test phpMyAdmin configuration and accessibility"
    )
    p_test_phpmyadmin.set_defaults(func=test_phpmyadmin_command)

    # configure-apache
    p_configure_apache = sub.add_parser(
        "configure-apache", 
        help="Configure Apache port and document root",
        description="Configure Apache to listen on specified port and use custom document root"
    )
    p_configure_apache.add_argument("--port", type=int, help="Apache port (default: 8080)")
    p_configure_apache.add_argument("--doc-root", help="Document root directory (default: /opt/homebrew/var/www)")
    p_configure_apache.set_defaults(func=configure_apache_command)

    # show-apache-config
    p_show_apache = sub.add_parser(
        "show-apache-config", 
        help="Show current Apache configuration",
        description="Display current Apache port and document root settings"
    )
    p_show_apache.set_defaults(func=show_apache_config_command)

    # enable-mod-rewrite
    p_enable_rewrite = sub.add_parser(
        "enable-mod-rewrite", 
        help="Enable mod_rewrite for Apache",
        description="Enable mod_rewrite module and configure AllowOverride for .htaccess files"
    )
    p_enable_rewrite.set_defaults(func=enable_mod_rewrite_command)

    # disable-mod-rewrite
    p_disable_rewrite = sub.add_parser(
        "disable-mod-rewrite", 
        help="Disable mod_rewrite for Apache",
        description="Disable mod_rewrite module and set AllowOverride to None"
    )
    p_disable_rewrite.set_defaults(func=disable_mod_rewrite_command)

    # check-rewrite-status
    p_check_rewrite = sub.add_parser(
        "check-rewrite-status", 
        help="Check mod_rewrite status",
        description="Display current mod_rewrite configuration status"
    )
    p_check_rewrite.set_defaults(func=check_rewrite_status_command)

    # export-databases
    p_export_db = sub.add_parser(
        "export-databases", 
        help="Export databases with enhanced options",
        description="Export all databases or a specific database with options for schema-only export and compression"
    )
    p_export_db.add_argument("--database", help="Export specific database (default: export all databases)")
    p_export_db.add_argument("--output-dir", help="Output directory for exported files (default: ./db_exports)")
    p_export_db.add_argument("--schema-only", action="store_true", help="Export only schema (no data)")
    p_export_db.add_argument("--no-compress", action="store_true", help="Disable compression (default: compress to .sql.gz)")
    p_export_db.add_argument("--user", default="root", help="Database user (default: root)")
    p_export_db.add_argument("--password", help="Database password (default: fe_root)")
    p_export_db.set_defaults(func=export_databases_command)

    # import-database
    p_import_db = sub.add_parser(
        "import-database", 
        help="Import a database from SQL file",
        description="Import a database from a SQL file (.sql or .sql.gz) into MySQL. Creates database if it doesn't exist."
    )
    p_import_db.add_argument("sql_file", help="Path to SQL file (.sql or .sql.gz)")
    p_import_db.add_argument("database", help="Target database name")
    p_import_db.add_argument("--host", default="127.0.0.1", help="MySQL host (default: 127.0.0.1)")
    p_import_db.add_argument("--port", default="3306", help="MySQL port (default: 3306)")
    p_import_db.add_argument("--user", default="root", help="MySQL user (default: root)")
    p_import_db.add_argument("--password", help="MySQL password (default: fe_root, or prompt if not provided)")
    p_import_db.set_defaults(func=import_database_command)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    # If no arguments provided, show help
    if argv is None and len(sys.argv) == 1:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
