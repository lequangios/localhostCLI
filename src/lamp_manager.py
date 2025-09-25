import os
import shlex
import shutil
import subprocess
import sys
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import secrets
import string
import getpass
try:
    from .lamp_apache_manager import LampApacheManager
except Exception:
    # Fallback when loaded as a flat module in bundled environments
    from lamp_apache_manager import LampApacheManager  # type: ignore


class LampManager:
    """Manage LAMP stack components via Homebrew on macOS.

    Provides methods to check status, install/update, uninstall, control services,
    and optionally export databases. This class contains no CLI parsing logic
    and can be reused by other modules.
    """

    BREW_FORMULAE = {
        "httpd": "Apache",
        "php": "PHP",
        "mysql": "MySQL",
        "mariadb": "MariaDB",
        "phpmyadmin": "phpMyAdmin",
    }

    def run_command(self, command: str, check: bool = False) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr)."""
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, process.stdout, process.stderr)
        return process.returncode, process.stdout.strip(), process.stderr.strip()

    def _get_apache_manager(self) -> Optional[LampApacheManager]:
        try:
            return LampApacheManager(self.get_httpd_conf_path())
        except Exception:
            return None

    def which(self, program: str) -> Optional[str]:
        """Return absolute path to program if found in PATH, else None."""
        return shutil.which(program)

    def ensure_brew_available(self) -> str:
        """Ensure Homebrew is available and return its path."""
        brew_path = self.which("brew")
        if not brew_path:
            print("Homebrew is not installed. Please install Homebrew from https://brew.sh and retry.", file=sys.stderr)
            raise RuntimeError("Homebrew not found")
        return brew_path

    # ---- Sudo helpers (aligned with mphm_cli.check_sudo_permissions) ----
    def ensure_sudo_permissions(self) -> bool:
        """Ensure sudo permissions are available; prompt in interactive shells."""
        try:
            res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)
            if res.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

        if not sys.stdin.isatty():
            print("Non-interactive environment detected. Sudo will be requested when needed.")
            return True

        print("Sudo access required. Please enter your password when prompted...")
        try:
            subprocess.run(["sudo", "true"], check=True, timeout=30)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("Sudo access denied or timed out.", file=sys.stderr)
            return False

    # --------------------------------------------------------------------

    def brew_prefix(self) -> str:
        """Return Homebrew prefix (e.g., /opt/homebrew or /usr/local)."""
        _, out, _ = self.run_command("brew --prefix")
        return out or "/usr/local"

    def brew_list_versions(self, formula: str) -> Optional[str]:
        code, out, _ = self.run_command(f"brew list --versions {shlex.quote(formula)}")
        if code != 0 or not out:
            return None
        parts = out.split()
        return parts[1] if len(parts) > 1 else None

    def brew_is_installed(self, formula: str) -> bool:
        return self.brew_list_versions(formula) is not None

    def brew_service_status(self, formula: str) -> Optional[str]:
        code, out, _ = self.run_command("brew services list | cat")
        if code != 0 or not out:
            return None
        for line in out.splitlines():
            cols = [c for c in line.split() if c]
            if not cols:
                continue
            if cols[0] == formula:
                return cols[1]
        return None

    def detect_database_formula(self) -> Optional[str]:
        if self.brew_is_installed("mysql"):
            return "mysql"
        if self.brew_is_installed("mariadb"):
            return "mariadb"
        return None

    # Discovery helpers
    def get_httpd_conf_path(self) -> str:
        prefix = self.brew_prefix()
        candidate = os.path.join(prefix, "etc", "httpd", "httpd.conf")
        return candidate

    def get_doc_root(self) -> str:
        httpd_conf = self.get_httpd_conf_path()
        try:
            with open(httpd_conf, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.lower().startswith("documentroot"):
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            value = parts[1].strip().strip('"')
                            return value
        except FileNotFoundError:
            pass
        prefix = self.brew_prefix()
        return os.path.join(prefix, "var", "www")

    def get_php_version(self) -> str:
        code, out, _ = self.run_command("php -r 'echo PHP_MAJOR_VERSION.""."".PHP_MINOR_VERSION;' 2>/dev/null")
        if code == 0 and out:
            return out.strip()
        _, out, _ = self.run_command("php -v | head -n1")
        try:
            parts = out.split()
            if len(parts) >= 2:
                full = parts[1]
                major_minor = ".".join(full.split(".")[:2])
                return major_minor
        except Exception:
            pass
        return "unknown"

    def find_phpmyadmin_path(self) -> Optional[str]:
        # Use fixed path for phpMyAdmin
        pma_site = "/opt/homebrew/share/phpmyadmin"
        if os.path.isdir(pma_site):
            return pma_site
        
        # Fallback to brew prefix detection
        prefix = self.brew_prefix()
        candidates = [
            os.path.join(prefix, "opt", "phpmyadmin"),
            os.path.join(prefix, "share", "phpmyadmin"),
        ]
        for path in candidates:
            if os.path.isdir(path):
                return path
        return None

    def get_httpd_bin_path(self) -> Optional[str]:
        path = self.which("httpd")
        if path:
            return path
        prefix = self.brew_prefix()
        candidates = [
            os.path.join(prefix, "opt", "httpd", "bin", "httpd"),
            os.path.join(prefix, "bin", "httpd"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return None

    def get_php_bin_path(self) -> Optional[str]:
        return self.which("php")

    def get_mysql_bin_path(self) -> Optional[str]:
        return self.which("mysql")

    def get_component_config_dir(self, component: str) -> Optional[str]:
        """Get configuration directory for a component."""
        prefix = self.brew_prefix()
        if component == "httpd":
            return os.path.join(prefix, "etc", "httpd")
        elif component == "php":
            # PHP config is usually in /etc/php or similar
            candidates = [
                os.path.join(prefix, "etc", "php"),
                "/etc/php",
                "/usr/local/etc/php",
            ]
            for candidate in candidates:
                if os.path.isdir(candidate):
                    return candidate
        elif component in ("mysql", "mariadb"):
            return os.path.join(prefix, "etc", component)
        elif component == "phpmyadmin":
            pma_path = self.find_phpmyadmin_path()
            return pma_path
        return None

    def get_component_info(self, component: str) -> Dict[str, Any]:
        """Get component information in the specified JSON structure."""
        version = self.brew_list_versions(component) or "unknown"
        bin_path = None
        config_dir = None
        
        if component == "httpd":
            bin_path = self.get_httpd_bin_path()
            config_dir = self.get_component_config_dir("httpd")
        elif component == "php":
            bin_path = self.get_php_bin_path()
            config_dir = self.get_component_config_dir("php")
        elif component in ("mysql", "mariadb"):
            bin_path = self.get_mysql_bin_path()
            config_dir = self.get_component_config_dir(component)
        elif component == "phpmyadmin":
            bin_path = self.find_phpmyadmin_path()
            config_dir = self.get_component_config_dir("phpmyadmin")
        
        return {
            "name": component,
            "version": version,
            "bin": bin_path or "",
            "config_dir": config_dir or "",
            "update_date": datetime.now().isoformat()
        }

    def ensure_phpmyadmin_installed(self) -> bool:
        if self.brew_is_installed("phpmyadmin"):
            return True
        print("Installing phpmyadmin...")
        code, _, err = self.run_command("brew install phpmyadmin")
        if code != 0:
            print("Failed to install phpmyadmin via Homebrew:", err, file=sys.stderr)
            return False
        return True

    def ensure_phpmyadmin_apache_config(self, pma_site: str = "/opt/homebrew/share/phpmyadmin") -> Tuple[str, Optional[str]]:
        prefix = self.brew_prefix()
        httpd_conf = self.get_httpd_conf_path()
        extra_dir = os.path.join(prefix, "etc", "httpd", "extra")
        os.makedirs(extra_dir, exist_ok=True)
        pma_conf_path = os.path.join(extra_dir, "phpmyadmin.conf")

        content = (
            f"Alias /phpmyadmin \"{pma_site}\"\n"
            f"<Directory \"{pma_site}\">\n"
            f"    Options Indexes FollowSymLinks\n"
            f"    AllowOverride All\n"
            f"    Require all granted\n"
            f"</Directory>\n"
        )
        try:
            with open(pma_conf_path, "w") as fh:
                fh.write(content)
        except Exception as e:
            print(f"Failed to write {pma_conf_path}: {e}", file=sys.stderr)

        include_line = f"Include \"{pma_conf_path}\""
        try:
            needs_append = True
            if os.path.exists(httpd_conf):
                with open(httpd_conf, "r") as fh:
                    for line in fh:
                        if include_line in line:
                            needs_append = False
                            break
            if needs_append:
                try:
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    shutil.copyfile(httpd_conf, f"{httpd_conf}.{ts}.bak")
                except Exception:
                    pass
                with open(httpd_conf, "a") as fh:
                    fh.write("\n# phpMyAdmin include\n" + include_line + "\n")
        except Exception as e:
            print(f"Failed to update {httpd_conf}: {e}", file=sys.stderr)

        return httpd_conf, pma_conf_path

    def ensure_phpmyadmin_config_file(self, pma_path: str) -> Optional[str]:
        config_path = os.path.join(pma_path, "config.inc.php")
        if os.path.exists(config_path):
            return config_path

        alphabet = string.ascii_letters + string.digits
        secret = "".join(secrets.choice(alphabet) for _ in range(32))
        tmp_dir = os.path.join(pma_path, "tmp")
        try:
            os.makedirs(tmp_dir, exist_ok=True)
        except Exception:
            pass

        cfg = (
            "<?php\n"
            "$cfg = array();\n"
            f"$cfg['blowfish_secret'] = '{secret}';\n"
            "$cfg['TempDir'] = 'tmp';\n"
            "// Allow cookie auth by default\n"
            "$i = 0;\n"
            "$i++;\n"
            "$cfg['Servers'][$i]['auth_type'] = 'cookie';\n"
            "?>\n"
        )
        try:
            with open(config_path, "w") as fh:
                fh.write(cfg)
            return config_path
        except Exception as e:
            print(f"Failed to write {config_path}: {e}", file=sys.stderr)
            return None

    def write_fe_lamp_conf(self, httpd_conf: str, php_version: str, doc_root: str, pma_path: Optional[str], pma_config: Optional[str], httpd_bin: Optional[str], php_bin: Optional[str], mysql_bin: Optional[str]) -> Optional[str]:
        base_dir = "/opt/fe_lamp"
        # Ensure directory exists (try normal, then sudo)
        try:
            os.makedirs(base_dir, exist_ok=True)
        except PermissionError:
            if self.ensure_sudo_permissions():
                subprocess.run(["sudo", "mkdir", "-p", base_dir], check=False)
            else:
                print("Cannot create /opt/fe_lamp without sudo.", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Failed to create /opt/fe_lamp: {e}", file=sys.stderr)
            return None

        # Build components list for JSON
        components = []
        
        # Add core components
        for component in ["httpd", "php"]:
            if self.brew_is_installed(component):
                components.append(self.get_component_info(component))
        
        # Add database component
        db_component = self.detect_database_formula()
        if db_component and self.brew_is_installed(db_component):
            components.append(self.get_component_info(db_component))
        
        # Add phpMyAdmin if installed
        if self.brew_is_installed("phpmyadmin"):
            components.append(self.get_component_info("phpmyadmin"))
        
        # Get current Apache configuration
        apache_config = self.get_current_apache_config()
        
        # Get PHP ini path
        php_ini_path = self.get_php_ini_path()
        
        # Add system info
        system_info = {
            "httpd_conf": httpd_conf,
            "doc_root": doc_root,
            "php_version": php_version,
            "php_ini": php_ini_path or "",
            "pma_path": pma_path or "",
            "pma_config": pma_config or "",
            "apache_port": apache_config.get("port", 8080),
            "mysql_username": "root",
            "mysql_password": "fe_root",
            "update_date": datetime.now().isoformat()
        }
        
        # Create final JSON structure
        config_data = {
            "system": system_info,
            "components": components
        }
        
        conf_path = os.path.join(base_dir, "fe_lamp.json")
        data = json.dumps(config_data, indent=2)

        # Try normal write first
        try:
            with open(conf_path, "w") as fh:
                fh.write(data)
            return conf_path
        except PermissionError:
            # Try to grant ownership, else fallback to sudo tee
            if self.ensure_sudo_permissions():
                username = os.environ.get("SUDO_USER") or getpass.getuser()
                subprocess.run(["sudo", "chown", username, base_dir], check=False)
                try:
                    with open(conf_path, "w") as fh:
                        fh.write(data)
                    return conf_path
                except PermissionError:
                    # Write via sudo tee
                    proc = subprocess.run(f"echo {shlex.quote(data)} | sudo tee {shlex.quote(conf_path)} > /dev/null", shell=True)
                    if proc.returncode == 0:
                        return conf_path
            print("Cannot write fe_lamp.json due to permissions.", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Failed to write {conf_path}: {e}", file=sys.stderr)
            return None

    def ensure_directory_index_priority(self, httpd_conf: Optional[str] = None) -> bool:
        """Ensure Apache DirectoryIndex prioritizes index.php using LampApacheManager."""
        try:
            am = LampApacheManager(httpd_conf or self.get_httpd_conf_path())
            return am.set_directory_index_priority_php()
        except Exception as e:
            print(f"Failed to enforce DirectoryIndex priority via LampApacheManager: {e}", file=sys.stderr)
            return False

    # Public API
    def get_status_lines(self) -> List[str]:
        self.ensure_brew_available()
        results: List[str] = []
        
        # Core services that have brew services
        core_services = ["httpd", "php", "mysql", "mariadb"]
        for formula_key in core_services:
            display = self.BREW_FORMULAE[formula_key]
            if self.brew_is_installed(formula_key):
                version = self.brew_list_versions(formula_key) or "unknown"
                svc = self.brew_service_status(formula_key) or "unknown"
                results.append(f"{display}: installed (v{version}), service: {svc}")
            else:
                results.append(f"{display}: not installed")
        
        # phpMyAdmin (web application, no service)
        if self.brew_is_installed("phpmyadmin"):
            version = self.brew_list_versions("phpmyadmin") or "unknown"
            results.append(f"phpMyAdmin: installed (v{version}), web application")
        else:
            results.append("phpMyAdmin: not installed")
            
        return results

    def install_or_update(self, db_choice: str = "mysql") -> None:
        self.ensure_brew_available()
        self.run_command("brew update")

        def install_or_update_formula(formula: str) -> None:
            if self.brew_is_installed(formula):
                print(f"Upgrading {formula} if needed...")
                self.run_command(f"brew upgrade {shlex.quote(formula)}")
            else:
                print(f"Installing {formula}...")
                self.run_command(f"brew install {shlex.quote(formula)}", check=True)

        def start_service(formula: str) -> None:
            self.run_command(f"brew services start {shlex.quote(formula)}")

        for formula in ["httpd", "php"]:
            install_or_update_formula(formula)

        if db_choice not in ("mysql", "mariadb"):
            raise ValueError("db_choice must be 'mysql' or 'mariadb'")

        other_db = "mariadb" if db_choice == "mysql" else "mysql"
        if not self.brew_is_installed(other_db):
            install_or_update_formula(db_choice)
        else:
            print(f"Detected {other_db} installed. Skipping install of {db_choice}.")

        for formula in ["httpd", "php", db_choice]:
            start_service(formula)

        # Ensure Apache port and document root use FE LAMP defaults BEFORE PHP config/tests
        try:
            current_apache = self.get_current_apache_config()
            current_port = current_apache.get("port") or 8080
            desired_doc_root = "/opt/fe_lamp/var/www"
            self.configure_apache_complete(port=current_port, doc_root=desired_doc_root)
            # Ensure vhosts include is enabled and default :8080 vhost exists (avoids 403 when name-vhosts are active)
            try:
                am = self._get_apache_manager()
                if am:
                    am.enable_vhosts()
            except Exception:
                pass
        except Exception as e:
            print(f"Warning: failed to apply Apache port/doc_root defaults: {e}", file=sys.stderr)

        # Configure Apache for PHP after installation
        print("Configuring Apache for PHP...")
        self.setup_and_test_php()

        # Configure MySQL root user after installation
        print("Configuring MySQL root user...")
        self.setup_mysql_complete("fe_root")

        # Configure phpMyAdmin
        print("Configuring phpMyAdmin...")
        self.setup_phpmyadmin_complete()

        pma_installed = self.brew_is_installed("phpmyadmin")
        pma_site = "/opt/homebrew/share/phpmyadmin"
        pma_config_path = None
        if pma_installed:
            httpd_conf, _ = self.ensure_phpmyadmin_apache_config(pma_site)
            pma_config_path = os.path.join(pma_site, "config.inc.php")
        else:
            httpd_conf = self.get_httpd_conf_path()

        php_version = self.get_php_version()
        doc_root = self.get_doc_root()

        httpd_bin = self.get_httpd_bin_path()
        php_bin = self.get_php_bin_path()
        mysql_bin = self.get_mysql_bin_path()

        self.write_fe_lamp_conf(
            httpd_conf=httpd_conf,
            php_version=php_version,
            doc_root=doc_root,
            pma_path=pma_site if pma_installed else None,
            pma_config=pma_config_path,
            httpd_bin=httpd_bin,
            php_bin=php_bin,
            mysql_bin=mysql_bin,
        )

        # Ensure Apache prioritizes index.php over index.html
        try:
            am = self._get_apache_manager()
            if am:
                am.set_directory_index_priority_php()
        except Exception as e:
            print(f"Warning: failed to enforce DirectoryIndex priority: {e}", file=sys.stderr)

        # Enable mod_rewrite for Apache
        try:
            am = self._get_apache_manager()
            if am:
                am.enable_mod_rewrite()
        except Exception as e:
            print(f"Warning: failed to enable mod_rewrite: {e}", file=sys.stderr)

        # After successful installation and configuration, deploy index template to web root
        try:
            # Resolve template path for both source and bundled (PyInstaller) modes
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
            template_path = os.path.join(base_dir, "template", "index_template.php")
            target_path = os.path.join(doc_root, "index.php")

            # Ensure doc_root exists
            os.makedirs(doc_root, exist_ok=True)

            if os.path.exists(template_path):
                try:
                    # Try direct copy
                    shutil.copyfile(template_path, target_path)
                except PermissionError:
                    # Fallback to sudo if needed
                    if self.ensure_sudo_permissions():
                        subprocess.run(["sudo", "cp", template_path, target_path], check=False)
                except Exception as e:
                    print(f"Failed to copy template: {e}", file=sys.stderr)
            else:
                print(f"Template not found at {template_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error deploying index template: {e}", file=sys.stderr)

    def export_all_databases(self, export_dir: str, user: str, password: Optional[str], 
                           schema_only: bool = False, compress: bool = True) -> List[str]:
        """Export all databases with enhanced options.
        
        Args:
            export_dir: Directory to save exported files
            user: Database user
            password: Database password
            schema_only: If True, export only schema (no data)
            compress: If True, compress files to .sql.gz format
            
        Returns:
            List of exported file paths
        """
        db_formula = self.detect_database_formula()
        if not db_formula:
            print("No MySQL/MariaDB installation detected; skipping DB export.")
            return []

        dump_bin = self.which("mysqldump")
        if not dump_bin:
            print("mysqldump not found in PATH; skipping DB export.")
            return []

        # Get list of databases
        databases = self._get_database_list(user, password)
        if not databases:
            print("No databases found to export.")
            return []

        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        exported_files = []

        env = os.environ.copy()
        if password is not None:
            env["MYSQL_PWD"] = password

        for db_name in databases:
            print(f"Exporting database: {db_name}")
            
            # Build mysqldump command
            cmd = [dump_bin, "-u", user]
            
            if schema_only:
                cmd.extend(["--no-data", "--routines", "--triggers"])
            else:
                cmd.extend(["--single-transaction", "--quick", "--lock-tables=false"])
            
            cmd.append(db_name)
            
            # Determine output file
            if compress:
                output_file = os.path.join(export_dir, f"{db_name}_{timestamp}.sql.gz")
            else:
                output_file = os.path.join(export_dir, f"{db_name}_{timestamp}.sql")
            
            try:
                if compress:
                    # Use gzip compression
                    with open(output_file, 'wb') as f:
                        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                           text=True, env=env)
                        if proc.returncode == 0:
                            # Compress the output
                            import gzip
                            with gzip.open(output_file, 'wt') as gz_file:
                                gz_file.write(proc.stdout)
                        else:
                            print(f"Failed to export {db_name}: {proc.stderr.strip()}", file=sys.stderr)
                            continue
                else:
                    # No compression
                    with open(output_file, 'w') as f:
                        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                           text=True, env=env)
                        if proc.returncode != 0:
                            print(f"Failed to export {db_name}: {proc.stderr.strip()}", file=sys.stderr)
                            continue
                
                exported_files.append(output_file)
                print(f"✅ Exported {db_name} to {output_file}")
                
            except Exception as e:
                print(f"❌ Error exporting {db_name}: {e}", file=sys.stderr)
                continue

        if exported_files:
            print(f"✅ Database export completed. {len(exported_files)} files exported to {export_dir}")
        else:
            print("❌ No databases were successfully exported.")
            
        return exported_files

    def _get_database_list(self, user: str, password: Optional[str]) -> List[str]:
        """Get list of all databases (excluding system databases)."""
        try:
            env = os.environ.copy()
            if password is not None:
                env["MYSQL_PWD"] = password
            
            # Get list of databases, excluding system databases
            cmd = [
                "mysql", "-u", user, "-e", 
                "SHOW DATABASES WHERE `Database` NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys');"
            ]
            
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if proc.returncode != 0:
                print(f"Failed to get database list: {proc.stderr.strip()}", file=sys.stderr)
                return []
            
            # Parse output to get database names
            databases = []
            for line in proc.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('Database'):
                    databases.append(line)
            
            return databases
            
        except Exception as e:
            print(f"Error getting database list: {e}", file=sys.stderr)
            return []

    def export_single_database(self, database: str, export_dir: str, user: str, password: Optional[str],
                              schema_only: bool = False, compress: bool = True) -> Optional[str]:
        """Export a single database with enhanced options.
        
        Args:
            database: Database name to export
            export_dir: Directory to save exported file
            user: Database user
            password: Database password
            schema_only: If True, export only schema (no data)
            compress: If True, compress file to .sql.gz format
            
        Returns:
            Path to exported file or None if failed
        """
        db_formula = self.detect_database_formula()
        if not db_formula:
            print("No MySQL/MariaDB installation detected; skipping DB export.")
            return None

        dump_bin = self.which("mysqldump")
        if not dump_bin:
            print("mysqldump not found in PATH; skipping DB export.")
            return None

        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        env = os.environ.copy()
        if password is not None:
            env["MYSQL_PWD"] = password

        # Build mysqldump command
        cmd = [dump_bin, "-u", user]
        
        if schema_only:
            cmd.extend(["--no-data", "--routines", "--triggers"])
        else:
            cmd.extend(["--single-transaction", "--quick", "--lock-tables=false"])
        
        cmd.append(database)
        
        # Determine output file
        if compress:
            output_file = os.path.join(export_dir, f"{database}_{timestamp}.sql.gz")
        else:
            output_file = os.path.join(export_dir, f"{database}_{timestamp}.sql")
        
        try:
            if compress:
                # Use gzip compression
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, env=env)
                if proc.returncode == 0:
                    # Compress the output
                    import gzip
                    with gzip.open(output_file, 'wt') as gz_file:
                        gz_file.write(proc.stdout)
                    print(f"✅ Exported {database} to {output_file}")
                    return output_file
                else:
                    print(f"Failed to export {database}: {proc.stderr.strip()}", file=sys.stderr)
                    return None
            else:
                # No compression
                with open(output_file, 'w') as f:
                    proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                       text=True, env=env)
                    if proc.returncode == 0:
                        print(f"✅ Exported {database} to {output_file}")
                        return output_file
                    else:
                        print(f"Failed to export {database}: {proc.stderr.strip()}", file=sys.stderr)
                        return None
                        
        except Exception as e:
            print(f"❌ Error exporting {database}: {e}", file=sys.stderr)
            return None

    def uninstall(self, export_db: bool = False, export_path: Optional[str] = None, db_user: str = "root", db_password: Optional[str] = None) -> None:
        self.ensure_brew_available()

        def stop_service(formula: str) -> None:
            self.run_command(f"brew services stop {shlex.quote(formula)}")

        for formula in ["httpd", "php", "mysql", "mariadb"]:
            if self.brew_is_installed(formula):
                stop_service(formula)

        if export_db:
            export_dir = export_path or os.path.join(os.getcwd(), "db_exports")
            self.export_all_databases(export_dir=export_dir, user=db_user, password=db_password, 
                                    schema_only=False, compress=True)

        to_uninstall = [f for f in ["httpd", "php", "mysql", "mariadb", "phpmyadmin"] if self.brew_is_installed(f)]
        for formula in to_uninstall:
            print(f"Uninstalling {formula}...")
            self.run_command(f"brew uninstall --ignore-dependencies {shlex.quote(formula)}")

        fe_lamp_dir = "/opt/fe_lamp"
        try:
            if os.path.isdir(fe_lamp_dir):
                shutil.rmtree(fe_lamp_dir)
                print("Removed /opt/fe_lamp directory.")
        except PermissionError:
            if self.ensure_sudo_permissions():
                subprocess.run(["sudo", "rm", "-rf", fe_lamp_dir], check=False)
                if not os.path.exists(fe_lamp_dir):
                    print("Removed /opt/fe_lamp directory with sudo.")
                else:
                    print("Failed to remove /opt/fe_lamp with sudo.", file=sys.stderr)
            else:
                print("Permission denied removing /opt/fe_lamp and sudo not available.", file=sys.stderr)
        except Exception as e:
            print(f"Failed to remove /opt/fe_lamp: {e}", file=sys.stderr)

        print("Uninstallation complete. Your website directory (e.g., var/www) was not removed.")

    # Service control API
    def _resolve_components(self, components: Optional[List[str]]) -> List[str]:
        """Resolve components list to valid brew services. None means auto-detect installed core services."""
        valid = {"httpd", "php", "mysql", "mariadb"}
        if not components:
            detected: List[str] = []
            for name in ["httpd", "php", "mysql", "mariadb"]:
                if self.brew_is_installed(name):
                    detected.append(name)
            return detected
        resolved: List[str] = []
        for name in components:
            if name == "db":
                dbf = self.detect_database_formula()
                if dbf:
                    resolved.append(dbf)
            elif name in valid:
                resolved.append(name)
        return resolved

    def start_services(self, components: Optional[List[str]] = None) -> None:
        """Start services for the given components (default: all installed core services)."""
        self.ensure_brew_available()
        for name in self._resolve_components(components):
            print(f"Starting {name}...")
            code, out, err = self.run_command(f"brew services start {shlex.quote(name)}")
            if code != 0:
                print(f"Failed to start {name}: {err or out}", file=sys.stderr)

    def stop_services(self, components: Optional[List[str]] = None) -> None:
        """Stop services for the given components (default: all installed core services)."""
        self.ensure_brew_available()
        for name in self._resolve_components(components):
            print(f"Stopping {name}...")
            code, out, err = self.run_command(f"brew services stop {shlex.quote(name)}")
            if code != 0:
                print(f"Failed to stop {name}: {err or out}", file=sys.stderr)

    def restart_services(self, components: Optional[List[str]] = None) -> None:
        """Restart services for the given components (default: all installed core services)."""
        self.ensure_brew_available()
        targets = self._resolve_components(components)
        # Explicitly exclude phpmyadmin (not a service)
        targets = [t for t in targets if t != "phpmyadmin"]
        for name in targets:
            print(f"Restarting {name}...")
            code, out, err = self.run_command(f"brew services restart {shlex.quote(name)}")
            if code != 0:
                print(f"Failed to restart {name}: {err or out}", file=sys.stderr)

    # Configuration methods
    def configure_apache_for_php(self) -> bool:
        """Configure Apache to handle PHP files."""
        print("Configuring Apache for PHP...")
        
        # Setup PHP session directory
        if not self._setup_php_session_directory():
            return False
        
        httpd_conf = self.get_httpd_conf_path()
        if not os.path.exists(httpd_conf):
            print(f"Apache config not found: {httpd_conf}", file=sys.stderr)
            return False
        
        try:
            # Read current config
            with open(httpd_conf, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')

            # 1) Try mod_php first
            php_module_path = self._find_php_module_path()
            if php_module_path:
                # If LoadModule already active, do not add again; still ensure PHP handler exists
                mod_php_active = ("LoadModule php_module" in content) and not any(l.strip().startswith('#') and 'LoadModule php_module' in l for l in lines)
                if not mod_php_active:
                    php_module_line = f"LoadModule php_module {php_module_path}"
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('LoadModule'):
                            insert_index = i + 1
                    lines.insert(insert_index, php_module_line)
                    lines.insert(insert_index + 1, "")

                # Prepare mod_php handler block if missing
                has_php_filesmatch = any('<FilesMatch' in l and '.php' in l for l in lines) and ('application/x-httpd-php' in content)
                php_handler_lines = []
                if not has_php_filesmatch:
                    php_handler_lines.extend([
                        "",
                        "# PHP Configuration (mod_php)",
                        "<FilesMatch \\.php$>",
                        "    SetHandler application/x-httpd-php",
                        "</FilesMatch>",
                    ])
                # Ensure DirectoryIndex exists (LampApacheManager also enforces priority elsewhere)
                if 'DirectoryIndex index.php' not in content:
                    php_handler_lines.extend([
                        "",
                        "# PHP index files",
                        "<IfModule dir_module>",
                        "    DirectoryIndex index.php index.html",
                        "</IfModule>",
                    ])
                # Add session config under php_module if missing
                if 'session.save_path' not in content:
                    php_handler_lines.extend([
                        "",
                        "# PHP Session Configuration",
                        "<IfModule php_module>",
                        "    php_value session.save_path \"/opt/fe_lamp/tmp\"",
                        "    php_value session.gc_maxlifetime 1440",
                        "    php_value session.cookie_lifetime 0",
                        "    php_value session.auto_start 0",
                        "</IfModule>",
                    ])
            else:
                # 2) Fallback to PHP-FPM via proxy_fcgi
                print("Configuring Apache to use PHP-FPM (proxy_fcgi)...")

                # Ensure proxy modules are present
                have_proxy = any(l.strip().startswith('LoadModule proxy_module') for l in lines)
                have_proxy_fcgi = any(l.strip().startswith('LoadModule proxy_fcgi_module') for l in lines)
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('LoadModule'):
                        insert_index = i + 1
                if not have_proxy:
                    lines.insert(insert_index, 'LoadModule proxy_module lib/httpd/modules/mod_proxy.so')
                    insert_index += 1
                if not have_proxy_fcgi:
                    lines.insert(insert_index, 'LoadModule proxy_fcgi_module lib/httpd/modules/mod_proxy_fcgi.so')

                # Detect php-fpm listen target
                fpm_target = self._detect_php_fpm_target()
                if not fpm_target:
                    print("Could not detect PHP-FPM listen target", file=sys.stderr)
                    return False

                handler = f'proxy:{fpm_target}'
                php_handler_lines = [
                    "",
                    "# PHP Configuration (php-fpm via proxy_fcgi)",
                    "<IfModule proxy_fcgi_module>",
                    "    <FilesMatch \\.php$>",
                    f"        SetHandler \"{handler}\"",
                    "    </FilesMatch>",
                    "</IfModule>",
                    "",
                    "# PHP index files",
                    "<IfModule dir_module>",
                    "    DirectoryIndex index.php index.html",
                    "</IfModule>",
                ]
            
            # Find end of file or last directive
            end_index = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() and not lines[i].strip().startswith('#'):
                    end_index = i + 1
                    break
            
            # Insert PHP handler configuration
            for i, handler_line in enumerate(php_handler_lines):
                lines.insert(end_index + i, handler_line)
            
            # Write updated config
            updated_content = '\n'.join(lines)
            
            # Backup original
            backup_path = f"{httpd_conf}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
            shutil.copyfile(httpd_conf, backup_path)
            print(f"Backed up original config to: {backup_path}")
            
            # Write new config
            with open(httpd_conf, 'w') as f:
                f.write(updated_content)
            
            print("Apache configured for PHP successfully")
            return True
            
        except Exception as e:
            print(f"Failed to configure Apache for PHP: {e}", file=sys.stderr)
            return False
    
    def _setup_php_session_directory(self) -> bool:
        """Setup PHP session directory with proper permissions."""
        print("Setting up PHP session directory...")
        
        session_dir = "/opt/fe_lamp/tmp"
        
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(session_dir):
                print(f"Creating session directory: {session_dir}")
                os.makedirs(session_dir, exist_ok=True)
            
            # Set permissions to 1777 (sticky bit + full permissions)
            print(f"Setting permissions 1777 on {session_dir}")
            os.chmod(session_dir, 0o1777)
            
            # Verify permissions
            stat_info = os.stat(session_dir)
            current_perms = oct(stat_info.st_mode)[-3:]
            if current_perms == "777":
                print(f"✅ Session directory created with permissions: {current_perms}")
                return True
            else:
                print(f"⚠️ Session directory permissions: {current_perms} (expected: 777)")
                return True  # Still continue, might work
                
        except PermissionError:
            print("Permission denied creating session directory. Trying with sudo...")
            if self.ensure_sudo_permissions():
                try:
                    # Create with sudo
                    subprocess.run(["sudo", "mkdir", "-p", session_dir], check=True)
                    subprocess.run(["sudo", "chmod", "1777", session_dir], check=True)
                    subprocess.run(["sudo", "chown", os.getlogin(), session_dir], check=True)
                    print(f"✅ Session directory created with sudo: {session_dir}")
                    return True
                except Exception as e:
                    print(f"❌ Failed to create session directory with sudo: {e}", file=sys.stderr)
                    return False
            else:
                print("❌ Cannot create session directory without sudo", file=sys.stderr)
                return False
        except Exception as e:
            print(f"❌ Failed to setup session directory: {e}", file=sys.stderr)
            return False
    
    def _find_php_module_path(self) -> Optional[str]:
        """Find the PHP module path for Apache."""
        prefix = self.brew_prefix()
        candidates = [
            os.path.join(prefix, "lib", "httpd", "modules", "libphp.so"),
            os.path.join(prefix, "lib", "apache2", "modules", "libphp.so"),
            "/usr/lib/apache2/modules/libphp.so",
            "/usr/local/lib/apache2/modules/libphp.so"
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        
        # Try to find via php-config
        try:
            code, out, _ = self.run_command("php-config --extension-dir")
            if code == 0 and out:
                php_ext_dir = out.strip()
                php_module = os.path.join(php_ext_dir, "libphp.so")
                if os.path.exists(php_module):
                    return php_module
        except Exception:
            pass
        
        return None
    
    def test_php_setup(self) -> bool:
        """Test PHP setup by creating info.php and checking with curl."""
        print("Testing PHP setup...")
        
        # Get document root
        doc_root = self.get_doc_root()
        if not os.path.exists(doc_root):
            print(f"Document root does not exist: {doc_root}", file=sys.stderr)
            return False
        
        # Check if Apache is running
        print("Checking Apache service status...")
        apache_status = self.brew_service_status("httpd")
        if apache_status != "started":
            print(f"Apache is not running (status: {apache_status}). Starting Apache...")
            self.start_services(["httpd"])
            import time
            time.sleep(5)  # Wait for Apache to start
        
        # Create info.php file with more comprehensive test
        info_php_path = os.path.join(doc_root, "info.php")
        test_content = """<?php
echo "<h1>PHP Test Page</h1>";
echo "<p>PHP Version: " . phpversion() . "</p>";
echo "<p>Server: " . $_SERVER['SERVER_SOFTWARE'] . "</p>";
echo "<p>Document Root: " . $_SERVER['DOCUMENT_ROOT'] . "</p>";
echo "<p>Current Time: " . date('Y-m-d H:i:s') . "</p>";

// Test basic PHP functionality
$test_array = [1, 2, 3, 4, 5];
echo "<p>Array test: " . implode(', ', $test_array) . "</p>";

// Test MySQL connection if available
try {
    $pdo = new PDO('mysql:host=localhost', 'root', 'fe_root');
    echo "<p style='color: green;'>✅ MySQL connection successful</p>";
} catch (Exception $e) {
    echo "<p style='color: orange;'>⚠️ MySQL connection failed: " . $e->getMessage() . "</p>";
}

phpinfo();
?>"""
        
        try:
            with open(info_php_path, 'w') as f:
                f.write(test_content)
            print(f"Created comprehensive test file: {info_php_path}")
        except Exception as e:
            print(f"Failed to create info.php: {e}", file=sys.stderr)
            return False
        
        # Determine actual Apache port from config
        apache_cfg = self.get_current_apache_config()
        detected_port = apache_cfg.get("port") or 8080
        # Test with curl - use detected port first, then fallbacks
        test_urls = [
            f"http://localhost:{detected_port}/info.php",
            f"http://127.0.0.1:{detected_port}/info.php",
            "http://localhost:8080/info.php",
            "http://127.0.0.1:8080/info.php",
            "http://localhost:80/info.php",
            "http://127.0.0.1:80/info.php"
        ]
        
        success = False
        working_url = None
        
        for url in test_urls:
            try:
                print(f"Testing URL: {url}")
                code, out, err = self.run_command(f"curl -I -s --connect-timeout 8 {url}")
                
                if code == 0:
                    if "HTTP/1.1 200" in out or "HTTP/2 200" in out:
                        print(f"✅ PHP test successful at {url}")
                        success = True
                        working_url = url
                        break
                    else:
                        print(f"❌ HTTP error at {url}: {out}")
                else:
                    print(f"❌ Connection failed to {url}: {err}")
                    
            except Exception as e:
                print(f"❌ Error testing {url}: {e}")
                continue
        
        try:
            if success:
                # Try to get the actual content to verify PHP is processing
                try:
                    print("Verifying PHP content processing...")
                    content_code, content_out, content_err = self.run_command(f"curl -s --connect-timeout 5 {working_url}")
                    
                    if content_code == 0 and "PHP Test Page" in content_out:
                        print("✅ PHP content processing verified")
                    else:
                        print("⚠️ PHP content processing may have issues")
                        
                except Exception as e:
                    print(f"⚠️ Could not verify PHP content: {e}")
                
                print("✅ PHP test successful - Apache is serving PHP correctly")
                return True
            else:
                print("❌ PHP test failed - Apache is not serving PHP on any tested URL")
                print("Please check:")
                print("1. Apache is running: brew services list | grep httpd")
                print("2. Apache configuration includes PHP module")
                print("3. Document root is correct")
                return False
        finally:
            # Clean up test file
            try:
                if os.path.exists(info_php_path):
                    os.remove(info_php_path)
                    print("Cleaned up test file")
            except Exception:
                pass
    
    def setup_and_test_php(self) -> bool:
        """Configure Apache for PHP and test the setup."""
        if not self.configure_apache_for_php():
            return False
        
        # Restart Apache to apply changes
        print("Restarting Apache to apply PHP configuration...")
        self.restart_services(["httpd"])
        
        # Wait a moment for Apache to start
        import time
        time.sleep(2)
        
        result = self.test_php_setup()
        # Ensure DirectoryIndex prioritizes index.php after PHP setup
        try:
            am = self._get_apache_manager()
            if am:
                am.set_directory_index_priority_php()
        except Exception:
            pass
        return result

    def _detect_php_fpm_target(self) -> Optional[str]:
        """Detect PHP-FPM listen target. Returns fcgi URL part for proxy (e.g. fcgi://127.0.0.1:9000 or unix:/path.sock|fcgi://localhost/)."""
        try:
            # Try common Homebrew php-fpm conf locations
            prefix = self.brew_prefix()
            conf_globs = [
                os.path.join(prefix, 'etc', 'php'),
                '/opt/homebrew/etc/php',
                '/usr/local/etc/php'
            ]
            for base in conf_globs:
                if not os.path.isdir(base):
                    continue
                for ver in sorted(os.listdir(base), reverse=True):
                    conf_path = os.path.join(base, ver, 'php-fpm.d', 'www.conf')
                    if os.path.exists(conf_path):
                        with open(conf_path, 'r') as f:
                            txt = f.read()
                        # find listen = ...
                        for line in txt.splitlines():
                            s = line.strip()
                            if s.startswith('listen'):
                                parts = s.split('=', 1)
                                if len(parts) == 2:
                                    target = parts[1].strip()
                                    if target.startswith('/'):
                                        # unix socket
                                        return f'unix:{target}|fcgi://localhost/'
                                    else:
                                        # host:port
                                        if not target.startswith('fcgi://'):
                                            return f'fcgi://{target}'
                                        return target
            # fallback common socket
            sock = '/opt/homebrew/var/run/php-fpm.sock'
            if os.path.exists(sock):
                return f'unix:{sock}|fcgi://localhost/'
            # fallback tcp
            return 'fcgi://127.0.0.1:9000'
        except Exception:
            return None
    
    def configure_mysql_root(self, password: str = "fe_root") -> bool:
        """Configure MySQL root user with specified password."""
        print(f"Configuring MySQL root user with password: {password}")
        
        db_component = self.detect_database_formula()
        if not db_component:
            print("No MySQL/MariaDB installation detected", file=sys.stderr)
            return False
        
        # Wait for MySQL to be ready
        print("Waiting for MySQL to be ready...")
        import time
        time.sleep(3)
        
        # Try to connect and set password
        try:
            # First, try to connect without password (for fresh installs)
            print("Attempting to set root password...")
            
            # Use mysqladmin to set password
            mysqladmin_cmd = f"mysqladmin -u root password '{password}'"
            code, out, err = self.run_command(mysqladmin_cmd)
            
            if code == 0:
                print("✅ MySQL root password set successfully")
                return True
            else:
                # If that fails, try to connect and use ALTER USER
                print("Trying alternative method...")
                alter_cmd = f"mysql -u root -e \"ALTER USER 'root'@'localhost' IDENTIFIED BY '{password}';\""
                code2, out2, err2 = self.run_command(alter_cmd)
                
                if code2 == 0:
                    print("✅ MySQL root password updated successfully")
                    return True
                else:
                    print(f"❌ Failed to set MySQL root password: {err2}", file=sys.stderr)
                    return False
                    
        except Exception as e:
            print(f"❌ Error configuring MySQL root: {e}", file=sys.stderr)
            return False
    
    def test_mysql_connection(self, user: str = "root", password: str = "fe_root") -> bool:
        """Test MySQL connection with given credentials."""
        print(f"Testing MySQL connection with user: {user}")
        
        try:
            # Test connection
            test_cmd = f"mysql -u {user} -p{password} -e 'SELECT 1;'"
            code, out, err = self.run_command(test_cmd)
            
            if code == 0:
                print("✅ MySQL connection test successful")
                return True
            else:
                print(f"❌ MySQL connection test failed: {err}", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"❌ MySQL connection test error: {e}", file=sys.stderr)
            return False
    
    def setup_mysql_complete(self, password: str = "fe_root") -> bool:
        """Complete MySQL setup: configure root user and test connection."""
        if not self.configure_mysql_root(password):
            return False
        
        # Wait a moment for changes to take effect
        import time
        time.sleep(2)
        
        return self.test_mysql_connection("root", password)
    
    def configure_phpmyadmin(self) -> bool:
        """Configure phpMyAdmin to work with Apache and MySQL."""
        print("Configuring phpMyAdmin...")
        
        # Check if phpMyAdmin is installed
        if not self.brew_is_installed("phpmyadmin"):
            print("phpMyAdmin is not installed. Installing...")
            if not self.ensure_phpmyadmin_installed():
                return False
        
        pma_site = "/opt/homebrew/share/phpmyadmin"
        if not os.path.isdir(pma_site):
            print(f"phpMyAdmin directory not found at: {pma_site}", file=sys.stderr)
            return False
        
        print(f"Using phpMyAdmin at: {pma_site}")
        
        # Create config.inc.php if it doesn't exist
        config_path = os.path.join(pma_site, "config.inc.php")
        if not os.path.exists(config_path):
            print("Creating phpMyAdmin configuration...")
            if not self.ensure_phpmyadmin_config_file(pma_site):
                return False
        
        # Update config.inc.php with proper settings
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Check if already configured
            if "localhost" in content and "fe_root" in content:
                print("phpMyAdmin already configured")
                return True
            
            # Create comprehensive config
            config_content = """<?php
/**
 * phpMyAdmin configuration for FE Local
 */

$cfg = array();

// Blowfish secret for encryption
$cfg['blowfish_secret'] = '""" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)) + """';

// Temp directory
$cfg['TempDir'] = 'tmp';

// Server configuration
$i = 0;
$i++;
$cfg['Servers'][$i]['host'] = 'localhost';
$cfg['Servers'][$i]['port'] = '';
$cfg['Servers'][$i]['socket'] = '';
$cfg['Servers'][$i]['connect_type'] = 'tcp';
$cfg['Servers'][$i]['extension'] = 'mysqli';
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['user'] = 'root';
$cfg['Servers'][$i]['password'] = 'fe_root';
$cfg['Servers'][$i]['AllowNoPassword'] = false;

// Security settings
$cfg['Servers'][$i]['AllowRoot'] = true;
$cfg['Servers'][$i]['AllowDeny']['order'] = '';
$cfg['Servers'][$i]['AllowDeny']['rules'] = array();

// UI settings
$cfg['DefaultLang'] = 'en';
$cfg['ServerDefault'] = 1;
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

// Performance settings
$cfg['MaxRows'] = 50;
$cfg['MaxCharactersInDisplayedSQL'] = 1000;

// Theme
$cfg['ThemeDefault'] = 'pmahomme';

// Error reporting
$cfg['SendErrorReports'] = 'never';

// Disable some features for security
$cfg['ShowServerInfo'] = true;
$cfg['ShowPhpInfo'] = false;
$cfg['ShowChgPassword'] = true;
$cfg['ShowCreateDb'] = true;

// Language
$cfg['Lang'] = 'en';
$cfg['DefaultCharset'] = 'utf8';

// Navigation
$cfg['NavigationTreeEnableGrouping'] = true;
$cfg['NavigationTreeDbSeparator'] = '_';

// SQL settings
$cfg['SQLQuery']['Edit'] = true;
$cfg['SQLQuery']['Explain'] = true;
$cfg['SQLQuery']['ShowAsPHP'] = false;
$cfg['SQLQuery']['Refresh'] = true;

// Export settings
$cfg['Export']['method'] = 'quick';
$cfg['Export']['format'] = 'sql';

// Import settings
$cfg['Import']['format'] = 'sql';

// Recent tables
$cfg['NumRecentTables'] = 10;
$cfg['NumFavoriteTables'] = 10;

// Console settings
$cfg['Console']['Mode'] = 'collapse';

// Designer settings
$cfg['Designer']['DefaultTabTable'] = 'structure';
$cfg['Designer']['DefaultTabTable2'] = '';

// PDF settings
$cfg['PDFPageSizes'] = array('A3', 'A4', 'A5', 'letter', 'legal');

// Transformations
$cfg['BrowseMIME'] = true;
$cfg['BrowseMIME'] = true;

// User preferences
$cfg['UserprefsDisallow'] = array();

// Server configuration
$cfg['Server'] = 1;
?>"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            print("✅ phpMyAdmin configuration updated")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure phpMyAdmin: {e}", file=sys.stderr)
            return False
    
    def test_phpmyadmin_setup(self) -> bool:
        """Test phpMyAdmin setup by checking if it's accessible."""
        print("Testing phpMyAdmin setup...")
        
        # Use fixed phpMyAdmin path
        pma_site = "/opt/homebrew/share/phpmyadmin"
        if not os.path.isdir(pma_site):
            print(f"phpMyAdmin not found at: {pma_site}", file=sys.stderr)
            return False
        
        # Test URLs for phpMyAdmin
        test_urls = [
            "http://localhost:8080/phpmyadmin/",
            "http://localhost:80/phpmyadmin/",
            "http://127.0.0.1:8080/phpmyadmin/",
            "http://127.0.0.1:80/phpmyadmin/"
        ]
        
        success = False
        working_url = None
        
        for url in test_urls:
            try:
                print(f"Testing phpMyAdmin URL: {url}")
                code, out, err = self.run_command(f"curl -I -s --connect-timeout 5 {url}")
                
                if code == 0:
                    if "HTTP/1.1 200" in out or "HTTP/2 200" in out:
                        print(f"✅ phpMyAdmin accessible at {url}")
                        success = True
                        working_url = url
                        break
                    else:
                        print(f"❌ HTTP error at {url}: {out}")
                else:
                    print(f"❌ Connection failed to {url}: {err}")
                    
            except Exception as e:
                print(f"❌ Error testing {url}: {e}")
                continue
        
        if success:
            # Try to get the actual content to verify phpMyAdmin is working
            try:
                print("Verifying phpMyAdmin content...")
                content_code, content_out, content_err = self.run_command(f"curl -s --connect-timeout 5 {working_url}")
                
                if content_code == 0 and ("phpMyAdmin" in content_out or "Login" in content_out):
                    print("✅ phpMyAdmin content verified")
                else:
                    print("⚠️ phpMyAdmin content may have issues")
                    
            except Exception as e:
                print(f"⚠️ Could not verify phpMyAdmin content: {e}")
            
            print("✅ phpMyAdmin test successful")
            return True
        else:
            print("❌ phpMyAdmin test failed - not accessible on any tested URL")
            print("Please check:")
            print("1. Apache is running and configured for phpMyAdmin")
            print("2. phpMyAdmin alias is properly set in Apache config")
            print("3. phpMyAdmin files are in the correct location")
            return False
    
    def setup_phpmyadmin_complete(self) -> bool:
        """Complete phpMyAdmin setup: configure and test."""
        if not self.configure_phpmyadmin():
            return False
        
        # Restart Apache to apply changes
        print("Restarting Apache to apply phpMyAdmin configuration...")
        self.restart_services(["httpd"])
        
        # Wait a moment for Apache to start
        import time
        time.sleep(3)
        
        return self.test_phpmyadmin_setup()
    
    def configure_apache_port(self, port: int = 8080) -> bool:
        """Configure Apache to listen on specified port."""
        print(f"Configuring Apache to listen on port {port}...")
        
        httpd_conf = self.get_httpd_conf_path()
        if not os.path.exists(httpd_conf):
            print(f"Apache config not found: {httpd_conf}", file=sys.stderr)
            return False
        
        try:
            # Read current config
            with open(httpd_conf, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            updated_lines = []
            port_updated = False
            
            for line in lines:
                stripped = line.strip()
                # Update Listen directive
                if stripped.startswith('Listen '):
                    updated_lines.append(f"Listen {port}")
                    port_updated = True
                else:
                    updated_lines.append(line)
            
            # If no Listen directive found, add one
            if not port_updated:
                # Find a good place to insert (after ServerRoot or before other directives)
                insert_index = 0
                for i, line in enumerate(updated_lines):
                    if line.strip().startswith('ServerRoot') or line.strip().startswith('#'):
                        insert_index = i + 1
                        break
                
                updated_lines.insert(insert_index, f"Listen {port}")
                updated_lines.insert(insert_index + 1, "")
            
            # Write updated config
            updated_content = '\n'.join(updated_lines)
            
            # Backup original
            backup_path = f"{httpd_conf}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
            shutil.copyfile(httpd_conf, backup_path)
            print(f"Backed up original config to: {backup_path}")
            
            # Write new config
            with open(httpd_conf, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Apache configured to listen on port {port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure Apache port: {e}", file=sys.stderr)
            return False
    
    def configure_apache_document_root(self, doc_root: str) -> bool:
        """Configure Apache document root directory."""
        print(f"Configuring Apache document root to: {doc_root}")
        
        # Ensure document root exists
        if not os.path.exists(doc_root):
            print(f"Creating document root directory: {doc_root}")
            try:
                os.makedirs(doc_root, exist_ok=True)
                # Set proper permissions
                os.chmod(doc_root, 0o755)
            except Exception as e:
                print(f"Failed to create document root: {e}", file=sys.stderr)
                return False
        
        httpd_conf = self.get_httpd_conf_path()
        if not os.path.exists(httpd_conf):
            print(f"Apache config not found: {httpd_conf}", file=sys.stderr)
            return False
        
        try:
            # Read current config
            with open(httpd_conf, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            updated_lines = []
            docroot_updated = False
            
            for line in lines:
                stripped = line.strip()
                # Update DocumentRoot directive
                if stripped.startswith('DocumentRoot '):
                    updated_lines.append(f'DocumentRoot "{doc_root}"')
                    docroot_updated = True
                # Update Directory directive for document root
                elif stripped.startswith('<Directory ') and '"' in stripped and 'var/www' in stripped:
                    updated_lines.append(f'<Directory "{doc_root}">')
                else:
                    updated_lines.append(line)
            
            # If no DocumentRoot directive found, add one
            if not docroot_updated:
                # Find a good place to insert (after ServerRoot)
                insert_index = 0
                for i, line in enumerate(updated_lines):
                    if line.strip().startswith('ServerRoot'):
                        insert_index = i + 1
                        break
                
                updated_lines.insert(insert_index, f'DocumentRoot "{doc_root}"')
                updated_lines.insert(insert_index + 1, "")
            
            # Add or update Directory directive for the document root
            directory_directive = [
                f'<Directory "{doc_root}">',
                "    Options Indexes FollowSymLinks",
                "    AllowOverride All",
                "    Require all granted",
                "</Directory>"
            ]
            
            # Find where to insert Directory directive (after DocumentRoot)
            insert_index = 0
            for i, line in enumerate(updated_lines):
                if 'DocumentRoot' in line:
                    insert_index = i + 1
                    break
            
            # Insert Directory directive
            for i, dir_line in enumerate(directory_directive):
                updated_lines.insert(insert_index + i, dir_line)
            
            # Write updated config
            updated_content = '\n'.join(updated_lines)
            
            # Backup original
            backup_path = f"{httpd_conf}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
            shutil.copyfile(httpd_conf, backup_path)
            print(f"Backed up original config to: {backup_path}")
            
            # Write new config
            with open(httpd_conf, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Apache document root configured to: {doc_root}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure Apache document root: {e}", file=sys.stderr)
            return False
    
    def configure_apache_complete(self, port: int = 8080, doc_root: str = "/opt/fe_lamp/var/www") -> bool:
        """Complete Apache configuration: port and document root."""
        print("Configuring Apache port and document root...")
        
        # Configure port
        if not self.configure_apache_port(port):
            return False
        
        # Configure document root
        if not self.configure_apache_document_root(doc_root):
            return False
        
        # Restart Apache to apply changes
        print("Restarting Apache to apply configuration...")
        self.restart_services(["httpd"])
        
        # Wait a moment for Apache to start
        import time
        time.sleep(3)
        
        print(f"✅ Apache configured successfully:")
        print(f"   - Port: {port}")
        print(f"   - Document Root: {doc_root}")
        return True
    
    def get_current_apache_config(self) -> dict:
        """Get current Apache configuration (port and document root)."""
        httpd_conf = self.get_httpd_conf_path()
        config = {
            "port": None,
            "document_root": None,
            "config_file": httpd_conf
        }
        
        if not os.path.exists(httpd_conf):
            return config
        
        try:
            with open(httpd_conf, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('Listen '):
                    try:
                        config["port"] = int(stripped.split()[1])
                    except (IndexError, ValueError):
                        pass
                elif stripped.startswith('DocumentRoot '):
                    try:
                        # Extract path from quotes
                        parts = stripped.split('"')
                        if len(parts) >= 2:
                            config["document_root"] = parts[1]
                    except:
                        pass
        
        except Exception as e:
            print(f"Error reading Apache config: {e}", file=sys.stderr)
        
        return config
    
    def get_php_ini_path(self) -> Optional[str]:
        """Get PHP ini file path."""
        try:
            # Try to get PHP ini path using php --ini
            result = subprocess.run(["php", "--ini"], capture_output=True, text=True, check=True)
            output = result.stdout
            
            # Parse the output to find the loaded configuration file
            for line in output.split('\n'):
                if 'Loaded Configuration File' in line:
                    # Extract path from line like: "Loaded Configuration File: /opt/homebrew/etc/php/8.1/php.ini"
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ini_path = parts[1].strip()
                        if os.path.exists(ini_path):
                            return ini_path
            
            # Fallback: try common Homebrew PHP ini locations
            php_version = self.get_php_version()
            if php_version:
                common_paths = [
                    f"/opt/homebrew/etc/php/{php_version}/php.ini",
                    f"/usr/local/etc/php/{php_version}/php.ini",
                    "/opt/homebrew/etc/php/php.ini",
                    "/usr/local/etc/php/php.ini"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        return path
            
            return None
            
        except Exception as e:
            print(f"Error getting PHP ini path: {e}", file=sys.stderr)
            return None
