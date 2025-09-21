#!/usr/bin/env python3

import argparse
import os
import sys
from typing import List, Optional

# Ensure src is importable when running as a script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = SCRIPT_DIR
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from lamp_manager import LampManager  # noqa: E402


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


def configure_apache_command(args: argparse.Namespace) -> int:
    manager = LampManager()
    port = args.port or 8080
    doc_root = args.doc_root or "/opt/homebrew/var/www"
    
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
        prog="lamp_cli",
        description="LAMP Stack Management CLI - Manage Apache, PHP, MySQL, and phpMyAdmin",
        epilog="""
Examples:
  lamp_cli status                           # Check installation status
  lamp_cli install                          # Install LAMP stack
  lamp_cli configure-apache --port 80       # Configure Apache on port 80
  lamp_cli show-apache-config               # Show current Apache settings
  lamp_cli start                            # Start all services
  lamp_cli stop                             # Stop all services
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

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

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
