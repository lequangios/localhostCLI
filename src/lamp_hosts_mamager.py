import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple


HOSTS_DEFAULT_PATH = "/etc/hosts"


@dataclass
class HostLine:
    """Represents a parsed line in /etc/hosts."""
    raw: str
    is_comment: bool
    ip: Optional[str]
    hostnames: List[str]


class LampHostsManager:
    """Manage /etc/hosts style files safely.

    - Preserves comments and formatting where possible
    - Updates only specific domain tokens on a line
    - Creates sudo backups before write
    """

    def __init__(self, hosts_path: str = HOSTS_DEFAULT_PATH) -> None:
        self.hosts_path = hosts_path

    # ---------- Low-level helpers ----------
    def _read_text(self) -> str:
        try:
            with open(self.hosts_path, 'r') as f:
                return f.read()
        except (FileNotFoundError, PermissionError, OSError):
            return ""

    def _sudo_backup(self) -> None:
        if not os.path.exists(self.hosts_path):
            return
        subprocess.run([
            "sudo", "cp", self.hosts_path,
            f"{self.hosts_path}.backup.$(date +%Y%m%d_%H%M%S)"
        ], check=False)

    def _sudo_write(self, content: str) -> None:
        self._sudo_backup()
        subprocess.run([
            "sudo", "sh", "-c",
            f"cat > {self.hosts_path} << 'EOF'\n{content}\nEOF"
        ], check=True)

    # ---------- Parsing ----------
    def _parse_lines(self, text: str) -> List[HostLine]:
        lines: List[HostLine] = []
        for raw in text.splitlines():
            stripped = raw.strip()
            if stripped == "" or stripped.startswith('#'):
                lines.append(HostLine(raw=raw, is_comment=True, ip=None, hostnames=[]))
                continue

            tokens = stripped.split()
            if len(tokens) == 0:
                lines.append(HostLine(raw=raw, is_comment=True, ip=None, hostnames=[]))
                continue

            ip = tokens[0]
            hostnames = tokens[1:]
            lines.append(HostLine(raw=raw, is_comment=False, ip=ip, hostnames=hostnames))
        return lines

    # ---------- Query operations ----------
    def list_entries(self) -> List[Tuple[str, List[str]]]:
        """Return a list of (ip, [hostnames]) for non-comment lines."""
        text = self._read_text()
        entries: List[Tuple[str, List[str]]] = []
        for line in self._parse_lines(text):
            if not line.is_comment and line.ip:
                entries.append((line.ip, list(line.hostnames)))
        return entries

    def search(self, pattern: str, ignore_case: bool = True) -> List[Tuple[int, str]]:
        """Search raw lines. Returns (line_no, raw_line)."""
        flags = re.IGNORECASE if ignore_case else 0
        results: List[Tuple[int, str]] = []
        for i, raw in enumerate(self._read_text().splitlines(), 1):
            if re.search(pattern, raw, flags):
                results.append((i, raw))
        return results

    def has_domain(self, domain: str) -> bool:
        """Check if a domain exists anywhere in hosts file."""
        for _, hostnames in self.list_entries():
            if domain in hostnames:
                return True
        return False

    # ---------- Mutation operations ----------
    def add_entry(self, ip: str, domain: str) -> bool:
        """Append a domain on its own line (idempotent). Returns True if changed."""
        if self.has_domain(domain):
            return False
        text = self._read_text()
        new_line = f"{ip} {domain}\n"
        self._sudo_write(text + ("\n" if not text.endswith('\n') and text != "" else "") + new_line)
        return True

    def remove_domain(self, domain: str) -> bool:
        """Remove only the specific domain token; preserves other hostnames on a line.

        Returns True if any change was made.
        """
        text = self._read_text()
        changed = False
        out_lines: List[str] = []
        for line in self._parse_lines(text):
            if line.is_comment or not line.ip:
                out_lines.append(line.raw)
                continue

            if domain in line.hostnames:
                remaining = [h for h in line.hostnames if h != domain]
                changed = True
                if remaining:
                    out_lines.append(f"{line.ip} {' '.join(remaining)}")
                else:
                    # Keep the IP-only line to avoid losing mappings like 127.0.0.1
                    out_lines.append(f"{line.ip}")
            else:
                out_lines.append(line.raw)

        if not changed:
            return False

        self._sudo_write("\n".join(out_lines) + "\n")
        return True

    def update_domain_ip(self, domain: str, new_ip: str) -> bool:
        """Move domain to new IP if present, or add if missing. Returns True if changed."""
        text = self._read_text()
        lines = self._parse_lines(text)

        found = False
        out_lines: List[str] = []
        for line in lines:
            if line.is_comment or not line.ip:
                out_lines.append(line.raw)
                continue

            if domain in line.hostnames:
                found = True
                # Remove from current line
                remaining = [h for h in line.hostnames if h != domain]
                if remaining:
                    out_lines.append(f"{line.ip} {' '.join(remaining)}")
                else:
                    out_lines.append(f"{line.ip}")
            else:
                out_lines.append(line.raw)

        # Append or merge into an existing new_ip line
        if found:
            merged = False
            for i, raw in enumerate(out_lines):
                parts = raw.split()
                if len(parts) > 0 and parts[0] == new_ip:
                    # Merge the domain into this line
                    existing = parts[1:]
                    if domain not in existing:
                        existing.append(domain)
                    out_lines[i] = f"{new_ip} {' '.join(existing)}"
                    merged = True
                    break
            if not merged:
                out_lines.append(f"{new_ip} {domain}")

            self._sudo_write("\n".join(out_lines) + "\n")
            return True

        # If domain not found, just add it
        return self.add_entry(new_ip, domain)

    def ensure_entry(self, ip: str, domain: str) -> bool:
        """Ensure (ip, domain) exists. Returns True if added/changed, False if already present."""
        text = self._read_text()
        for line in self._parse_lines(text):
            if line.is_comment or not line.ip:
                continue
            if line.ip == ip and domain in line.hostnames:
                return False
        # Not present as-is. If domain exists elsewhere, move it.
        if self.has_domain(domain):
            return self.update_domain_ip(domain, ip)
        # Otherwise simply add
        return self.add_entry(ip, domain)


