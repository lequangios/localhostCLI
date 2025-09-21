from pathlib import Path
from functools import lru_cache
from typing import Literal

ProjectType = Literal["WordPress", "Laravel", "Symfony", "Drupal", "Magento", "Plain PHP", "Static HTML", "JavaScript", "Unknown"]


class LampSiteDetector:
	"""Detects site/project types based on filesystem heuristics.

	Detection strategy:
	- Fast checks for well-known framework markers
	- Fallback to simple file presence checks for PHP/HTML/JS
	- Avoids expensive recursive scans
	"""

	@lru_cache(maxsize=256)
	def detect(self, path_str: str) -> ProjectType:
		path = Path(path_str)
		if not path.exists():
			return "Unknown"

		def check_markers(p: Path) -> ProjectType:
			# Framework markers
			if (p / 'wp-config.php').exists():
				return 'WordPress'
			if (p / 'artisan').exists():
				return 'Laravel'
			if (p / 'bin' / 'console').exists() or (p / 'symfony.lock').exists():
				return 'Symfony'
			if (p / 'core' / 'lib' / 'Drupal.php').exists() or (p / 'web' / 'core' / 'lib' / 'Drupal.php').exists():
				return 'Drupal'
			if (p / 'app' / 'code').exists() and (p / 'bin' / 'magento').exists():
				return 'Magento'
			return 'Unknown'

		# Try current path markers first
		marker_type = check_markers(path)
		if marker_type != 'Unknown':
			return marker_type

		# If not found, try direct parent for common cases like Laravel (public/)
		parent = path.parent if path.parent != path else None
		if parent and parent.exists():
			marker_type = check_markers(parent)
			if marker_type != 'Unknown':
				return marker_type

		# Language/stack hints
		php_candidates = ['index.php', 'config.php', 'app.php', 'bootstrap.php']
		for name in php_candidates:
			if (path / name).exists():
				return 'Plain PHP'

		html_candidates = ['index.html', 'home.html', 'main.html']
		for name in html_candidates:
			if (path / name).exists():
				return 'Static HTML'

		js_candidates = ['package.json']
		for name in js_candidates:
			if (path / name).exists():
				return 'JavaScript'

		# Shallow one-level scan fallback (current path)
		try:
			for item in path.iterdir():
				if item.is_file() and item.suffix == '.php':
					return 'Plain PHP'
				if item.is_file() and item.suffix == '.html':
					return 'Static HTML'
		except Exception:
			pass

		# Shallow one-level scan fallback (parent path)
		if parent and parent.exists():
			try:
				for item in parent.iterdir():
					if item.is_file() and item.suffix == '.php':
						return 'Plain PHP'
					if item.is_file() and item.suffix == '.html':
						return 'Static HTML'
			except Exception:
				pass

		return 'Unknown'
