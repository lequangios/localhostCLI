import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple


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
        subprocess.run([
            "sudo", "cp", self.vhost_conf_path,
            f"{self.vhost_conf_path}.backup.$(date +%Y%m%d_%H%M%S)"
        ], check=False)

    def _sudo_write(self, content: str) -> None:
        self._sudo_backup()
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
        m = re.search(r"ServerName\s+([^\s]+)", block_text)
        return m.group(1) if m else None

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
        content = self._read_file()
        for block in self._iter_blocks(content):
            if block.server_name == domain:
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

        # Prevent duplicate ServerName
        if self.find_block_by_server_name(domain):
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

        self._sudo_write(content + block)
        return True

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


