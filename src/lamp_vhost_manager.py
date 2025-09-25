import os
import re
import subprocess
import json
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime


@dataclass
class VHostBlock:
    """Represents a <VirtualHost> block in the vhost config file."""
    start_index: int
    end_index: int
    text: str
    server_name: Optional[str]
    port: Optional[int]
    document_root: Optional[str]


class LampVHostManager:
    """Manage Apache VirtualHost configuration file.

    Provides utilities to read, search, add, update, and delete <VirtualHost> blocks.
    All writes are performed via sudo and include an automatic backup step.
    """

    def __init__(self, vhost_conf_path: str) -> None:
        self.vhost_conf_path = vhost_conf_path

    @staticmethod
    def _normalize_domain(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        v = value.strip().rstrip('.')
        return v.lower()

    # ---------- Low-level file helpers ----------
    def _read_file(self) -> str:
        try:
            with open(self.vhost_conf_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _sudo_backup(self) -> None:
        if not os.path.exists(self.vhost_conf_path):
            return
        # Use sudo -n (non-interactive). If credentials not cached, skip backup to avoid blocking
        try:
            subprocess.run([
                "sudo", "-n", "cp", self.vhost_conf_path,
                f"{self.vhost_conf_path}.backup.$(date +%Y%m%d_%H%M%S)"
            ], check=True)
        except subprocess.CalledProcessError:
            # Fallback to interactive sudo if allowed (may prompt)
            try:
                subprocess.run([
                    "sudo", "cp", self.vhost_conf_path,
                    f"{self.vhost_conf_path}.backup.$(date +%Y%m%d_%H%M%S)"
                ], check=True)
            except Exception:
                pass
        except Exception:
            pass

    def _sudo_write(self, content: str) -> None:
        self._sudo_backup()
        # Use sudo -n to avoid prompting (fail fast if no sudo cached)
        try:
            subprocess.run([
                "sudo", "-n", "sh", "-c",
                f"cat > {self.vhost_conf_path} << 'EOF'\n{content}\nEOF"
            ], check=True)
        except subprocess.CalledProcessError:
            # Fallback to interactive sudo (may prompt)
            subprocess.run([
                "sudo", "sh", "-c",
                f"cat > {self.vhost_conf_path} << 'EOF'\n{content}\nEOF"
            ], check=True)

    # ---------- Parsing helpers ----------
    def _iter_blocks(self, content: str) -> List[VHostBlock]:
        """Parse content and return all <VirtualHost> blocks with metadata."""
        blocks: List[VHostBlock] = []
        pattern = re.compile(r"<VirtualHost[^>]*>.*?</VirtualHost>", re.DOTALL)
        for m in pattern.finditer(content):
            text = m.group(0)
            start = m.start()
            end = m.end()
            server_name = self._extract_server_name(text)
            port = self._extract_port(text)
            docroot = self._extract_document_root(text)
            blocks.append(VHostBlock(start, end, text, server_name, port, docroot))
        return blocks

    def _extract_server_name(self, block_text: str) -> Optional[str]:
        """Extract active (non-commented) ServerName from a vhost block.

        Avoid matching commented lines like: `# ServerName example.local`.
        """
        for line in block_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            m = re.search(r"\bServerName\s+([^\s#]+)", stripped)
            if m:
                return m.group(1)
        return None

    def _extract_port(self, block_text: str) -> Optional[int]:
        m = re.search(r"<VirtualHost[^>]*:(\d+)", block_text)
        return int(m.group(1)) if m else None

    def _extract_document_root(self, block_text: str) -> Optional[str]:
        m = re.search(r"DocumentRoot\s+\"([^\"]+)\"", block_text)
        return m.group(1) if m else None

    # ---------- Public operations ----------
    def list_blocks(self) -> List[VHostBlock]:
        """Return all VirtualHost blocks in the file."""
        return self._iter_blocks(self._read_file())

    def find_block_by_server_name(self, domain: str) -> Optional[VHostBlock]:
        """Find a VirtualHost block by ServerName value."""
        print(f"[FE-LAMP] Scanning vhost file: {self.vhost_conf_path}")
        content = self._read_file()
        norm_target = self._normalize_domain(domain)
        for block in self._iter_blocks(content):
            sn = self._normalize_domain(block.server_name)
            if sn == norm_target:
                # Brief debug context
                preview = '\n'.join(block.text.splitlines()[:5])
                print(f"[FE-LAMP] Found matching ServerName: {block.server_name}")
                print(f"[FE-LAMP] Match context (first lines):\n{preview}")
                return block
        return None

    def search(self, pattern: str, ignore_case: bool = True) -> List[Tuple[int, str]]:
        """Search raw lines for a regex pattern. Returns list of (line_no, line)."""
        flags = re.IGNORECASE if ignore_case else 0
        lines = self._read_file().splitlines()
        results: List[Tuple[int, str]] = []
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, flags):
                results.append((i, line))
        return results

    def add_vhost(self, domain: str, document_root: str, port: int,
                  directory_allow_override: str = "All",
                  directory_require: str = "all granted") -> bool:
        """Append a new VirtualHost block. Returns True if added, False if exists."""
        content = self._read_file()

        # Prevent duplicate ServerName (normalized)
        if self.find_block_by_server_name(domain):
            print(f"[FE-LAMP] Duplicate ServerName detected for domain '{domain}' in {self.vhost_conf_path}")
            return False

        block = (
            f"\n<VirtualHost *:{port}>\n"
            f"    DocumentRoot \"{document_root}\"\n"
            f"    ServerName {domain}\n\n"
            f"    <Directory \"{document_root}\">\n"
            f"        AllowOverride {directory_allow_override}\n"
            f"        Require {directory_require}\n"
            f"    </Directory>\n"
            f"</VirtualHost>\n"
        )

        try:
            self._sudo_write(content + block)
            return True
        except subprocess.CalledProcessError:
            # Fall back to normal write if we own the file
            try:
                self._write(content + block)  # type: ignore[attr-defined]
                return True
            except Exception:
                return False

    def remove_vhost(self, domain: str) -> bool:
        """Remove a VirtualHost block by ServerName. Returns True if removed."""
        content = self._read_file()
        blocks = self._iter_blocks(content)

        removed = False
        new_content_parts: List[str] = []
        last_index = 0
        for block in blocks:
            if block.server_name == domain:
                removed = True
                # skip this block by not appending its text
                new_content_parts.append(content[last_index:block.start_index])
                last_index = block.end_index
        new_content_parts.append(content[last_index:])

        if not removed:
            return False

        self._sudo_write("".join(new_content_parts))
        return True

    def update_vhost(self, domain: str, new_document_root: Optional[str] = None,
                     new_port: Optional[int] = None) -> bool:
        """Update an existing VirtualHost block's DocumentRoot and/or port.

        Returns True if the block was found and updated.
        """
        content = self._read_file()
        block = self.find_block_by_server_name(domain)
        if not block:
            return False

        updated_text = block.text

        if new_document_root:
            # Replace DocumentRoot and Directory path occurrences inside the block
            updated_text = re.sub(
                r"(DocumentRoot\s+)\"[^\"]+\"",
                rf"\1\"{new_document_root}\"",
                updated_text,
            )
            updated_text = re.sub(
                r"(<Directory\s+)\"[^\"]+\"",
                rf"\1\"{new_document_root}\"",
                updated_text,
            )

        if new_port is not None:
            updated_text = re.sub(
                r"(<VirtualHost\s*[^>:]*:)\d+",
                rf"\1{new_port}",
                updated_text,
            )

        # Splice back into content
        new_content = content[:block.start_index] + updated_text + content[block.end_index:]
        self._sudo_write(new_content)
        return True

    # ---------- mod_rewrite functionality ----------
    def enable_mod_rewrite(self) -> bool:
        """Enable mod_rewrite for all VirtualHost blocks.
        
        This function:
        - Adds RewriteEngine On to all VirtualHost blocks
        - Updates status in JSON file
        - Provides feedback on success/failure
        """
        try:
            content = self._read_file()
            lines = content.split('\n')
            changed = False
            
            # Process each VirtualHost block
            blocks = self._iter_blocks(content)
            for block in blocks:
                block_text = block.text
                block_lines = block_text.split('\n')
                
                # Check if RewriteEngine is already enabled in this block
                has_rewrite_engine = any('RewriteEngine On' in line and not line.strip().startswith('#') 
                                       for line in block_lines)
                
                if not has_rewrite_engine:
                    # Find a good place to insert RewriteEngine On (after ServerName or DocumentRoot)
                    insert_index = 0
                    for i, line in enumerate(block_lines):
                        if ('ServerName' in line or 'DocumentRoot' in line) and not line.strip().startswith('#'):
                            insert_index = i + 1
                            break
                    
                    # Insert RewriteEngine On
                    block_lines.insert(insert_index, '    RewriteEngine On')
                    changed = True
                    
                    # Update the block in the main content
                    new_block_text = '\n'.join(block_lines)
                    content = content[:block.start_index] + new_block_text + content[block.end_index:]
            
            if changed:
                self._sudo_write(content)
                self._update_rewrite_status(True)
                print("✅ mod_rewrite enabled for all VirtualHost blocks")
                return True
            else:
                print("ℹ️ mod_rewrite already enabled for all VirtualHost blocks")
                return True
                
        except Exception as e:
            print(f"❌ enable_mod_rewrite failed: {e}")
            return False

    def disable_mod_rewrite(self) -> bool:
        """Disable mod_rewrite for all VirtualHost blocks.
        
        This function:
        - Comments out or removes RewriteEngine On from all VirtualHost blocks
        - Updates status in JSON file
        - Provides feedback on success/failure
        """
        try:
            content = self._read_file()
            lines = content.split('\n')
            changed = False
            
            # Process each VirtualHost block
            blocks = self._iter_blocks(content)
            for block in blocks:
                block_text = block.text
                block_lines = block_text.split('\n')
                
                # Find and comment out RewriteEngine On
                for i, line in enumerate(block_lines):
                    if 'RewriteEngine On' in line and not line.strip().startswith('#'):
                        block_lines[i] = '    # ' + line.strip()
                        changed = True
                
                if changed:
                    # Update the block in the main content
                    new_block_text = '\n'.join(block_lines)
                    content = content[:block.start_index] + new_block_text + content[block.end_index:]
            
            if changed:
                self._sudo_write(content)
                self._update_rewrite_status(False)
                print("✅ mod_rewrite disabled for all VirtualHost blocks")
                return True
            else:
                print("ℹ️ mod_rewrite already disabled for all VirtualHost blocks")
                return True
                
        except Exception as e:
            print(f"❌ disable_mod_rewrite failed: {e}")
            return False

    def get_rewrite_status(self) -> Dict[str, Any]:
        """Get current mod_rewrite status for all VirtualHost blocks.
        
        Returns a dictionary with:
        - 'enabled': bool - whether any VirtualHost has RewriteEngine On
        - 'blocks_with_rewrite': list - list of domains with mod_rewrite enabled
        - 'total_blocks': int - total number of VirtualHost blocks
        - 'status_file': str - path to status JSON file
        """
        try:
            content = self._read_file()
            blocks = self._iter_blocks(content)
            
            enabled_blocks = []
            total_blocks = len(blocks)
            
            for block in blocks:
                has_rewrite_engine = any('RewriteEngine On' in line and not line.strip().startswith('#') 
                                       for line in block.text.split('\n'))
                if has_rewrite_engine and block.server_name:
                    enabled_blocks.append(block.server_name)
            
            status = {
                'enabled': len(enabled_blocks) > 0,
                'blocks_with_rewrite': enabled_blocks,
                'total_blocks': total_blocks,
                'status_file': self._get_status_file_path(),
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            print(f"❌ get_rewrite_status failed: {e}")
            return {
                'enabled': False,
                'blocks_with_rewrite': [],
                'total_blocks': 0,
                'status_file': self._get_status_file_path(),
                'timestamp': datetime.now().isoformat()
            }

    def _get_status_file_path(self) -> str:
        """Get the path to the mod_rewrite status JSON file."""
        base_dir = "/opt/fe_lamp"
        return os.path.join(base_dir, "vhost_rewrite_status.json")

    def _update_rewrite_status(self, enabled: bool) -> None:
        """Update the mod_rewrite status in JSON file."""
        try:
            status_file = self._get_status_file_path()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            
            # Get current status
            current_status = self.get_rewrite_status()
            current_status['enabled'] = enabled
            current_status['last_updated'] = datetime.now().isoformat()
            
            # Write to JSON file
            with open(status_file, 'w') as f:
                json.dump(current_status, f, indent=2)
                
            print(f"✅ Status updated in {status_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to update status file: {e}")

    def show_rewrite_status(self) -> None:
        """Display current mod_rewrite status in a user-friendly format."""
        status = self.get_rewrite_status()
        
        print("VirtualHost mod_rewrite Status:")
        print(f"  Overall Status: {'✅ Enabled' if status['enabled'] else '❌ Disabled'}")
        print(f"  Total VirtualHost blocks: {status['total_blocks']}")
        print(f"  Blocks with mod_rewrite: {len(status['blocks_with_rewrite'])}")
        
        if status['blocks_with_rewrite']:
            print("  Domains with mod_rewrite enabled:")
            for domain in status['blocks_with_rewrite']:
                print(f"    - {domain}")
        
        print(f"  Status file: {status['status_file']}")
        print(f"  Last updated: {status['timestamp']}")


