import os
import sys
import shutil
from datetime import datetime
from typing import List, Optional


class LampApacheManager:
    """Manage core Apache (httpd.conf) settings for a Homebrew-based LAMP.

    Features:
      - Enable/disable VirtualHosts include
      - Ensure DirectoryIndex prioritizes PHP
      - Configure global ErrorLog path
      - Configure DirectoryIndex list (global or for a specific Directory)
      - Enable basic SSL/TLS (mod_ssl, Listen 443, simple vhost)
    """

    def __init__(self, httpd_conf_path: str) -> None:
        self.httpd_conf_path = httpd_conf_path

    # --------- low level helpers ---------
    def _read(self) -> str:
        if not os.path.exists(self.httpd_conf_path):
            raise FileNotFoundError(self.httpd_conf_path)
        with open(self.httpd_conf_path, 'r') as f:
            return f.read()

    def _backup(self) -> str:
        backup = f"{self.httpd_conf_path}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copyfile(self.httpd_conf_path, backup)
        return backup

    def _write(self, content: str) -> None:
        self._backup()
        with open(self.httpd_conf_path, 'w') as f:
            f.write(content)

    # --------- vhost include ---------
    def enable_vhosts(self, vhost_conf_path: Optional[str] = None) -> bool:
        """Ensure Include to vhosts file is active and absolute.

        If vhost_conf_path is None, use Homebrew default:
            /opt/homebrew/etc/httpd/extra/httpd-vhosts.conf
        """
        vhost_conf_path = vhost_conf_path or \
            "/opt/homebrew/etc/httpd/extra/httpd-vhosts.conf"
        try:
            content = self._read()
            lines = content.split('\n')

            # Normalize: remove commented include variants and ensure one active include
            include_found = False
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('Include') and 'httpd-vhosts.conf' in s:
                    lines[i] = f"Include {vhost_conf_path}"
                    include_found = True
                elif s.startswith('#Include') and 'httpd-vhosts.conf' in s:
                    lines[i] = f"Include {vhost_conf_path}"
                    include_found = True

            if not include_found:
                # Append at end
                lines.extend(['', '# Virtual hosts', f'Include {vhost_conf_path}'])

            updated = '\n'.join(lines)

            # Ensure a default :8080 vhost exists at the beginning (to avoid 403 for bare IP:8080)
            import re
            def has_default_8080_vhost(text: str) -> bool:
                # Find any :8080 vhost without active ServerName
                pattern = re.compile(r"<VirtualHost[^>]*:\s*8080>.*?</VirtualHost>", re.DOTALL)
                for m in pattern.finditer(text):
                    block = m.group(0)
                    # Check active ServerName line
                    has_server_name = False
                    for ln in block.splitlines():
                        s = ln.strip()
                        if not s or s.startswith('#'):
                            continue
                        if s.startswith('ServerName '):
                            has_server_name = True
                            break
                    if not has_server_name:
                        return True
                return False

            if not has_default_8080_vhost(updated):
                default_block = [
                    f'<VirtualHost *:8080>',
                    f'    DocumentRoot "/opt/fe_lamp/var/www/"',
                    f'    # Không đặt ServerName để block này làm default',
                    f'    <Directory "/opt/fe_lamp/var/www">',
                    f'        Options Indexes FollowSymLinks',
                    f'        AllowOverride All',
                    f'        Require all granted',
                    f'    </Directory>',
                    f'    ErrorLog "/opt/homebrew/var/log/httpd/default_error.log"',
                    f'    CustomLog "/opt/homebrew/var/log/httpd/default_access.log" common',
                    f'</VirtualHost>',
                    ''
                ]
                updated = '\n'.join(default_block) + updated

            self._write(updated)
            print(f"✅ Enabled vhosts include: {vhost_conf_path}")
            return True
        except Exception as e:
            print(f"❌ enable_vhosts failed: {e}", file=sys.stderr)
            return False

    def disable_vhosts(self) -> bool:
        """Comment out Include to httpd-vhosts.conf."""
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('Include') and 'httpd-vhosts.conf' in s and not s.startswith('#'):
                    lines[i] = '#' + line if not line.lstrip().startswith('#') else line
                    changed = True

            if changed:
                self._write('\n'.join(lines))
                print("✅ Disabled vhosts include")
            else:
                print("ℹ️ Vhosts include already disabled")
            return True
        except Exception as e:
            print(f"❌ disable_vhosts failed: {e}", file=sys.stderr)
            return False

    def vhosts_status(self, vhost_conf_path: Optional[str] = None) -> dict:
        """Return vhost include status.

        Returns a dict: { 'enabled': bool, 'path': str, 'found': bool }
        enabled = Include line exists and is not commented.
        found   = any Include (commented or not) referencing httpd-vhosts.conf is present.
        path    = resolved vhost path (argument or detected from first matching include).
        """
        default_path = vhost_conf_path or "/opt/homebrew/etc/httpd/extra/httpd-vhosts.conf"
        try:
            content = self._read()
            lines = content.split('\n')
            found = False
            enabled = False
            detected_path = default_path

            for line in lines:
                s = line.strip()
                if 'httpd-vhosts.conf' in s and ('Include' in s or '#Include' in s):
                    found = True
                    # Try to extract path after Include token
                    parts = s.lstrip('#').split()
                    if len(parts) >= 2 and parts[0] == 'Include':
                        detected_path = parts[1]
                    if s.startswith('Include'):
                        enabled = True
                    # stop at first match
                    break

            return {
                'enabled': enabled,
                'found': found,
                'path': detected_path,
                'exists': os.path.exists(detected_path),
            }
        except Exception as e:
            print(f"❌ vhosts_status failed: {e}", file=sys.stderr)
            return {
                'enabled': False,
                'found': False,
                'path': default_path,
                'exists': os.path.exists(default_path),
            }

    # --------- directory index ---------
    def set_directory_index_priority_php(self) -> bool:
        """Ensure DirectoryIndex puts index.php before index.html."""
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False
            in_dir = False
            directory_index_found = False
            
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('<IfModule') and 'dir_module' in s:
                    in_dir = True
                elif s.startswith('</IfModule>') and in_dir:
                    in_dir = False
                elif in_dir and s.startswith('DirectoryIndex'):
                    directory_index_found = True
                    if 'index.php' not in s or (('index.html' in s) and s.index('index.php') > s.index('index.html')):
                        # keep indentation
                        indent = line[:len(line) - len(line.lstrip(' '))]
                        lines[i] = f"{indent}DirectoryIndex index.php index.html"
                        changed = True

            if not directory_index_found:
                # No DirectoryIndex found, add new one
                lines.extend(['', '# Ensure PHP index takes priority', '<IfModule dir_module>', '    DirectoryIndex index.php index.html', '</IfModule>'])
                changed = True

            if changed:
                self._write('\n'.join(lines))
                print('✅ DirectoryIndex prioritizes PHP')
            else:
                print('ℹ️ DirectoryIndex already prioritizes PHP')
            return True
        except Exception as e:
            print(f"❌ set_directory_index_priority_php failed: {e}", file=sys.stderr)
            return False

    def set_directory_index(self, filenames: List[str]) -> bool:
        """Set global DirectoryIndex list inside <IfModule dir_module>."""
        try:
            content = self._read()
            lines = content.split('\n')
            directive = ' '.join(['DirectoryIndex'] + filenames)
            in_dir = False
            updated = False
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('<IfModule') and 'dir_module' in s:
                    in_dir = True
                elif s.startswith('</IfModule>') and in_dir:
                    in_dir = False
                elif in_dir and s.startswith('DirectoryIndex'):
                    indent = line[:len(line) - len(line.lstrip(' '))]
                    lines[i] = f"{indent}{directive}"
                    updated = True

            if not updated:
                lines.extend(['', '<IfModule dir_module>', f'    {directive}', '</IfModule>'])

            self._write('\n'.join(lines))
            print(f"✅ DirectoryIndex set: {directive}")
            return True
        except Exception as e:
            print(f"❌ set_directory_index failed: {e}", file=sys.stderr)
            return False

    def set_directory_index_for_directory(self, directory_path: str, filenames: List[str]) -> bool:
        """Ensure a <Directory "path"> block sets the desired DirectoryIndex."""
        try:
            content = self._read()
            lines = content.split('\n')
            directive = ' '.join(['DirectoryIndex'] + filenames)

            # naive approach: append a Directory block (safer than modifying existing unknown blocks)
            lines.extend([
                '',
                f'<Directory "{directory_path}">',
                '    AllowOverride All',
                f'    {directive}',
                '    Require all granted',
                '</Directory>'
            ])
            self._write('\n'.join(lines))
            print(f"✅ DirectoryIndex set for {directory_path}: {directive}")
            return True
        except Exception as e:
            print(f"❌ set_directory_index_for_directory failed: {e}", file=sys.stderr)
            return False

    # --------- logging ---------
    def set_error_log_path(self, log_path: str) -> bool:
        """Set global ErrorLog path."""
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('ErrorLog '):
                    indent = line[:len(line) - len(line.lstrip(' '))]
                    lines[i] = f"{indent}ErrorLog \"{log_path}\""
                    changed = True
            if not changed:
                lines.append(f'ErrorLog "{log_path}"')

            self._write('\n'.join(lines))
            print(f"✅ ErrorLog set to {log_path}")
            return True
        except Exception as e:
            print(f"❌ set_error_log_path failed: {e}", file=sys.stderr)
            return False

    # --------- SSL/TLS ---------
    def enable_ssl(self, cert_file: str, key_file: str, port: int = 443, chain_file: Optional[str] = None) -> bool:
        """Enable basic SSL: load mod_ssl, listen 443, add a minimal vhost if none exists.

        Note: This updates httpd.conf directly. For advanced setups, manage httpd-ssl.conf separately.
        """
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False

            # LoadModule ssl_module
            has_ssl_module = any('ssl_module' in l and 'LoadModule' in l and not l.strip().startswith('#') for l in lines)
            if not has_ssl_module:
                # insert after last LoadModule
                insert_at = 0
                for i, l in enumerate(lines):
                    if l.strip().startswith('LoadModule'):
                        insert_at = i + 1
                lines.insert(insert_at, 'LoadModule ssl_module lib/httpd/modules/mod_ssl.so')
                lines.insert(insert_at + 1, '')
                changed = True

            # Listen 443
            if not any(l.strip().startswith('Listen ') and l.strip().endswith(str(port)) for l in lines):
                lines.append(f'Listen {port}')
                changed = True

            # Add a default SSL vhost if none exists (very basic)
            ssl_vhost_exists = any('<VirtualHost' in l and ':443' in l for l in lines)
            if not ssl_vhost_exists:
                vhost_block = [
                    '',
                    f'<VirtualHost _default_:{port}>',
                    '    SSLEngine on',
                    f'    SSLCertificateFile "{cert_file}"',
                    f'    SSLCertificateKeyFile "{key_file}"',
                ]
                if chain_file:
                    vhost_block.append(f'    SSLCertificateChainFile "{chain_file}"')
                vhost_block.extend([
                    '    <Location "/">',
                    '        Require all granted',
                    '    </Location>',
                    '</VirtualHost>'
                ])
                lines.extend(vhost_block)
                changed = True

            if changed:
                self._write('\n'.join(lines))
                print('✅ SSL/TLS basic configuration applied')
            else:
                print('ℹ️ SSL/TLS already configured')
            return True
        except Exception as e:
            print(f"❌ enable_ssl failed: {e}", file=sys.stderr)
            return False

    # --------- mod_rewrite ---------
    def enable_mod_rewrite(self) -> bool:
        """Enable mod_rewrite module for Apache.
        
        This function:
        - Loads the rewrite_module if not already loaded
        - Ensures AllowOverride is set to allow .htaccess files
        """
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False

            # Check if rewrite_module is already loaded
            has_rewrite_module = any('rewrite_module' in l and 'LoadModule' in l and not l.strip().startswith('#') for l in lines)
            if not has_rewrite_module:
                # Insert after last LoadModule
                insert_at = 0
                for i, l in enumerate(lines):
                    if l.strip().startswith('LoadModule'):
                        insert_at = i + 1
                lines.insert(insert_at, 'LoadModule rewrite_module lib/httpd/modules/mod_rewrite.so')
                lines.insert(insert_at + 1, '')
                changed = True

            # Ensure AllowOverride is set to allow .htaccess files
            # Look for existing AllowOverride directives and update them
            allow_override_found = False
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('AllowOverride'):
                    # Update existing AllowOverride to All
                    indent = line[:len(line) - len(line.lstrip(' '))]
                    lines[i] = f"{indent}AllowOverride All"
                    allow_override_found = True
                    changed = True

            # If no AllowOverride found, add a global one
            if not allow_override_found:
                lines.extend(['', '# Enable .htaccess files', '<Directory "/opt/homebrew/var/www">', '    AllowOverride All', '</Directory>'])
                changed = True

            if changed:
                self._write('\n'.join(lines))
                print('✅ mod_rewrite enabled and AllowOverride set to All')
            else:
                print('ℹ️ mod_rewrite already enabled')
            return True
        except Exception as e:
            print(f"❌ enable_mod_rewrite failed: {e}", file=sys.stderr)
            return False

    def disable_mod_rewrite(self) -> bool:
        """Disable mod_rewrite module for Apache.
        
        This function:
        - Comments out the rewrite_module LoadModule directive
        - Sets AllowOverride to None to disable .htaccess files
        """
        try:
            content = self._read()
            lines = content.split('\n')
            changed = False

            # Comment out rewrite_module LoadModule
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('LoadModule') and 'rewrite_module' in s and not s.startswith('#'):
                    lines[i] = '#' + line if not line.lstrip().startswith('#') else line
                    changed = True

            # Set AllowOverride to None
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith('AllowOverride'):
                    indent = line[:len(line) - len(line.lstrip(' '))]
                    lines[i] = f"{indent}AllowOverride None"
                    changed = True

            if changed:
                self._write('\n'.join(lines))
                print('✅ mod_rewrite disabled and AllowOverride set to None')
            else:
                print('ℹ️ mod_rewrite already disabled')
            return True
        except Exception as e:
            print(f"❌ disable_mod_rewrite failed: {e}", file=sys.stderr)
            return False

    def mod_rewrite_status(self) -> dict:
        """Check mod_rewrite status.
        
        Returns a dict with:
        - 'enabled': bool - whether rewrite_module is loaded
        - 'allow_override': str - current AllowOverride setting
        """
        try:
            content = self._read()
            lines = content.split('\n')
            
            enabled = False
            allow_override = "None"
            
            for line in lines:
                s = line.strip()
                if s.startswith('LoadModule') and 'rewrite_module' in s and not s.startswith('#'):
                    enabled = True
                elif s.startswith('AllowOverride'):
                    allow_override = s.split()[1] if len(s.split()) > 1 else "None"
            
            return {
                'enabled': enabled,
                'allow_override': allow_override
            }
        except Exception as e:
            print(f"❌ mod_rewrite_status failed: {e}", file=sys.stderr)
            return {
                'enabled': False,
                'allow_override': "None"
            }


