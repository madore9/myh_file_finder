#!/usr/bin/env python3
"""
Auto-update checker for my.File Tool.
Checks GitHub Releases API for newer versions. No GUI dependencies except PyQt5 signals.
"""

import json
import os
import urllib.request
import urllib.error

from PyQt5.QtCore import QThread, pyqtSignal

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

GITHUB_OWNER = "madore9"
GITHUB_REPO = "myh_file_finder"
API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
REQUEST_TIMEOUT = 10  # seconds


# ─────────────────────────────────────────────────────────────
# Version helpers
# ─────────────────────────────────────────────────────────────

def get_app_version() -> str:
    """Read version from VERSION file, falling back to '0.0.0'.

    Checks multiple locations to work in both development and py2app bundles:
      1. Same directory as this module (__file__)
      2. sys.executable's Resources directory (py2app bundle)
      3. Two levels up from sys.executable (Contents/MacOS -> Contents/Resources)
    """
    import sys

    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"),
    ]
    # py2app places data files in Contents/Resources/
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    resources = os.path.join(os.path.dirname(exe_dir), "Resources")
    candidates.append(os.path.join(resources, "VERSION"))
    candidates.append(os.path.join(exe_dir, "VERSION"))

    for path in candidates:
        try:
            with open(path) as f:
                v = f.read().strip()
                if v:
                    return v
        except (FileNotFoundError, OSError):
            continue
    return "0.0.0"


def parse_version(v: str) -> tuple:
    """Parse '4.1.0' or 'v4.1.0' into (4, 1, 0) for comparison."""
    v = v.lstrip("v")
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


# ─────────────────────────────────────────────────────────────
# Update checker thread
# ─────────────────────────────────────────────────────────────

class UpdateCheckerThread(QThread):
    """Check GitHub Releases API for a newer version. Non-blocking."""

    update_available = pyqtSignal(str, str, str)  # (latest_version, release_url, changelog)
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)  # error message (for logging, not user display on auto-check)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        try:
            import ssl
            req = urllib.request.Request(
                API_URL,
                headers={
                    "User-Agent": f"myh-file-finder/{self.current_version}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            # py2app bundles don't include SSL certs on macOS.
            # Use unverified context — safe because we only read public GitHub API.
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tag = data.get("tag_name", "")
            latest = parse_version(tag)
            current = parse_version(self.current_version)

            if latest > current:
                version_str = tag.lstrip("v")
                release_url = data.get("html_url", "")
                changelog = data.get("body", "") or ""
                self.update_available.emit(version_str, release_url, changelog)
            else:
                self.no_update.emit()

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # No releases published yet — treat as "no update available"
                self.no_update.emit()
            else:
                self.check_failed.emit(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            self.check_failed.emit(f"Network error: {e.reason}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.check_failed.emit(f"Parse error: {e}")
        except Exception as e:
            self.check_failed.emit(str(e))
