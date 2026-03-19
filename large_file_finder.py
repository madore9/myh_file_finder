#!/usr/bin/env python3
"""
my.h File Finder — Sensitive / Duplicates / Large / String search
PyQt5 desktop app: scan for sensitive data, duplicates, large files, or search file content.
macOS and Windows.

Modes:
  - Sensitive: HUID, SSN, TAX, Harvard email profiles; secure delete.
  - Duplicates: same size/content hash.
  - Large: big files, last-opened, safe-to-delete rating.
  - String search: find files containing a string or regex (e.g. hardcoded credentials).

Usage:
    pip install PyQt5
    python large_file_finder.py

Repository: https://github.com/madore9/myh_file_finder
"""

import platform
import sys
import os
import subprocess
import time
import stat
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import hashlib

# Shared scanning utilities
from scan_utils import should_skip_dir as unified_should_skip_dir, fast_scandir

# Sensitive scan engine (profiles, scan_file, secure_delete)
try:
    from sensitive_scanner import (
        PROFILES as SENSITIVE_PROFILES,
        scan_file as sensitive_scan_file,
        secure_delete_file as sensitive_secure_delete_file,
        should_skip_dir as sensitive_should_skip_dir,
        load_excluded_dirs,
        save_excluded_dirs,
        MAX_FILE_SIZE as SENSITIVE_MAX_FILE_SIZE,
        mask_value as sensitive_mask_value,
        SKIP_EXTENSIONS as SENSITIVE_SKIP_EXTENSIONS,
    )
except ImportError:
    SENSITIVE_PROFILES = {}
    sensitive_scan_file = None
    sensitive_secure_delete_file = None
    sensitive_should_skip_dir = None
    load_excluded_dirs = lambda: []
    save_excluded_dirs = lambda x: None
    SENSITIVE_MAX_FILE_SIZE = 50 * 1024 * 1024
    sensitive_mask_value = lambda v, k: "****"
    SENSITIVE_SKIP_EXTENSIONS = set()

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QCheckBox, QProgressBar, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QGroupBox, QSplitter, QFrame,
    QStyle, QToolButton, QMenu, QAction, QListWidget,
    QDialog, QPlainTextEdit, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QPixmap



# ─────────────────────────────────────────────────────────────
# Embedded app icon (base64-encoded PNG)
# ─────────────────────────────────────────────────────────────

APP_ICON_BASE64 = """iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAYQklEQVR4nO3dW6xld13A8d+eazsz7bTD0CvMFE9TW6BYmkAjV4MIgsQE5AGC4AuNoqKYiTFpTE1qLC/WJxOj9UoVggQFo76ARKEVCgQSi0oLR5wBO7SczrTTy0xvc3wopz2zz95n39blf/l83ubMmTPrrHVyft/1X2vtHQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABATgZ9bwAduGF1te9NADJ088CMKJiDWwpDHuiSOMieA5gjwx5IkSjIioOVC0MfyIkYSJ4DlKoGB/6BfU19JaAmR441+MUEQXIckNQsMPgNeqALC4WBEEiGA5GCOYa+YQ+kZK4oEAO9svP7NMPgN/CBnMwUBEKgF3Z61wx9oDJiIE12dFemHPyGPlCyqWNACLTODm6bwQ+wgRDonx3blikGv6EPMGUMCIHG2aFtmDD8DX6AjSaGgAholJ3ZJIMfYGFCoBt2YlM2Gf4GP8DsNg0BEbAwO3BRzvoBWmM1oD123CKc9QN0wmpA8+y0eRj8AL0QAs3Z0vcGZMfwB+jNpr9nvW36TNTSLMb8cBn8AN0buxpgJWAqdtI0nPUDJMklgfm5BDCJ4Q+QLJcE5qeONmPJHyAbLgnMxgrAOIY/QFbG/n62EjCSABjF8AfIkgiYngAYZvgDZE0ETEcArGf4AxRBBEzmxog1I34oDH6A/I28OdCNgVYAIsLwByjYyN/nVgIEgOEPUD4RsFHdAWD4A1RDBJyp3gAw/AGqIwKeU2cAVHqwARijwrlQXwB41A+gah4RfEZ9ATCC4Q9QF7/3awsA1/0B+KHa7weoJwAMfwCG1BwBdQSA4Q/AGLVGQB0BAACcofwAcPYPwAQ1rgKUHQCGPwBTqi0Cyg6AIYY/AJupaU6UGwAFVxsAHSp0npQZAJb+AZhTLZcCygyAIYY/ALOoYW6UFwAFVhoACShsvpQVAJb+AWhI6ZcCygoAAGAq5QSAs38AGlbyKkA5ATDE8AegCaXOkzICoJAaAyATBcydMgJgSKm1BkA/Spwr+QdAARUGQIYynz/5B8CQEisNgP6VNl+KCwAAYLK8A2Bo+aW0OgMgLRvmTMaXAfIOAABgLvkGQMbVBUBBMp1H+QbAEMv/AHShlHlTTAAAANMb9L0Bc3HzX28OH4qjfW8Ds7tzOY5ctxQH+t6OJhy8JS7uexsgIuLIsaEP3DzIaqZaAYBK3LkcR/reBiAd+QVApjdbQApEALQos/mUXwAMsfwPsxEB0Izc50/2AQDMTgQAAgAqJQKgbnkFgLv/oVEiABaT80sD5xUAQONEANRJAAAiACqUTwBktKwCORIB0JBM5lU+ATDE9X9ongiA2eU6j7INAKAdIgDqIACADUQAlE8AACOJAChbHgGQyQ0VUBoRAHPKYG7lEQBDcr3hAnIkAmCyHOdSlgEAdEsEQHkEADAVEQBlEQDA1EQAlEMAADMRAVAGAQDMTARA/tIPAG8BDEkSAXCm3N4aOP0AAJIlAiBfAgBYiAiAPAkAYGEiAPIjAIBGiADIiwAAGiMCIB8CAGiUCIA8CACgcSIA0icAgFaIAEibAABaIwIgXQIAaJUIgDQJAKB1IgDSIwCATogASIsAADojAiAdAgDolAiANAgAoHMiAPonAIBeiADolwAAeiMCoD8CAOiVCIB+CACgdyIAuicAgCSIAOiWAACSIQKgOwIASIoIgG4IACA5IgDaJwCAJIkAaJcAAJIlAqA9AgBImgiAdggAIHkiAJonAIAsiABolgAAsiECoDnb+t4AoH3XLcWBvrcBSIsVAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgAoJAACokAAAgApt63sDYDOD65dv7HsbaMbqrUs39b0NwHMEAEky+MuzdkyFAKTBJQAAqJAAIDnO/svm+EIaBAAAVEgAAECFBADJcZNY2RxfSIMAAIAKeQyQJK2dJbphrBzO/CEtAoCkGRoA7XAJAAAqJAAAoEICAAAqJAAAoEICAAAqJAAAoEICAAAqJAAAoEICAAAqJAAAoEICAAAqJAAAoEIC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"""


def load_app_icon() -> QIcon:
    """Decode the embedded base64 icon and return a QIcon."""
    icon_data = base64.b64decode(APP_ICON_BASE64)
    pixmap = QPixmap()
    pixmap.loadFromData(icon_data)
    return QIcon(pixmap)


# ─────────────────────────────────────────────────────────────
# File Analyzer — Confidence scoring engine
# ─────────────────────────────────────────────────────────────

class FileAnalyzer:
    """Analyzes a file and returns a deletability confidence score + reasoning."""

    SAFE_CACHE_PATTERNS = [
        (r"/Library/Caches/", 75, "App cache — regenerated automatically"),
        (r"/Library/Logs/", 70, "App log file — safe to remove"),
        (r"/.Trash/", 90, "Already in Trash"),
        (r"/tmp/", 80, "Temporary file"),
        (r"/private/tmp/", 80, "System temp file"),
        (r"/var/folders/", 70, "System temp/cache directory"),
        (r"/DerivedData/", 85, "Xcode build cache — regenerates on build"),
        (r"/node_modules/", 70, "npm packages — reinstall with npm install"),
        (r"/__pycache__/", 85, "Python bytecode cache"),
        (r"/\.cache/", 70, "Application cache directory"),
    ]

    APP_DATA_PATTERNS = [
        (r"crashplan", 20, "CrashPlan backup data — needed if active"),
        (r"time\s?machine", 15, "Time Machine data — do not delete"),
        (r"/Backups\.backupdb/", 10, "Time Machine backup — do not delete"),
        (r"/\.ollama/models/", 60, "Ollama LLM model — re-downloadable"),
        (r"/vm_bundles/.*claudevm", 55, "Claude Code VM — re-downloadable"),
        (r"/Docker/", 50, "Docker data — check if container needed"),
        (r"/\.docker/", 50, "Docker config/data"),
        (r"/Containers/.*\.app/", 35, "App container data"),
        (r"/Final Cut/", 25, "Final Cut Pro project data"),
        (r"/iMovie/", 30, "iMovie project data"),
        (r"/GarageBand/", 30, "GarageBand project data"),
        (r"/Logic Pro/", 25, "Logic Pro project data"),
        (r"/Adobe/", 30, "Adobe application data"),
        (r"/Lightroom/", 25, "Lightroom catalog/previews"),
        (r"/System/", 5, "System file — do not delete"),
        (r"/usr/", 10, "System/Unix file — do not delete"),
        (r"/private/var/db/", 10, "System database — do not delete"),
        (r"/CoreSimulator/", 55, "Xcode iOS Simulator — safe if not developing"),
        (r"Xcode.*DeviceSupport", 60, "Xcode device support — safe to clear"),
        (r"\.vmdk$", 30, "Virtual machine disk"),
        (r"\.qcow2$", 30, "Virtual machine disk"),
        (r"\.vdi$", 30, "VirtualBox disk image"),
        (r"\.vmwarevm/", 30, "VMware virtual machine"),
        (r"\.parallels/", 30, "Parallels virtual machine"),
    ]

    EXTENSION_INFO = {
        ".mov": (-10, "QuickTime video — likely personal"),
        ".mp4": (-10, "Video file — likely personal"),
        ".avi": (-10, "Video file"), ".mkv": (-5, "Video — possibly downloaded"),
        ".m4v": (-10, "Video file"), ".insv": (-5, "Insta360 video — check backup"),
        ".heic": (-15, "Photo — likely personal"),
        ".jpg": (-15, "Photo — likely personal"),
        ".jpeg": (-15, "Photo — likely personal"),
        ".png": (-10, "Image file"),
        ".raw": (-15, "RAW photo"), ".cr2": (-15, "Canon RAW photo"),
        ".nef": (-15, "Nikon RAW photo"), ".arw": (-15, "Sony RAW photo"),
        ".mp3": (-5, "Audio file"), ".wav": (-5, "Audio file"),
        ".flac": (-5, "Audio file"), ".aac": (-5, "Audio file"),
        ".pdf": (-10, "PDF document"), ".docx": (-10, "Word document"),
        ".xlsx": (-10, "Excel spreadsheet"), ".pptx": (-10, "PowerPoint"),
        ".zip": (10, "Archive — may be extractable duplicate"),
        ".dmg": (15, "Disk image — likely installer, safe after install"),
        ".pkg": (15, "Installer package — safe after install"),
        ".iso": (15, "Disk image — likely installer"),
        ".tar": (5, "Archive"), ".gz": (5, "Compressed file"),
        ".db": (-5, "Database file"), ".sqlite": (-5, "SQLite database"),
        ".img": (0, "Disk image — context dependent"),
        ".log": (20, "Log file — generally safe to delete"),
        ".cache": (25, "Cache file — safe to delete"),
        ".tmp": (30, "Temporary file — safe to delete"),
    }

    @classmethod
    def analyze(cls, filepath: str, size_bytes: int, last_opened_str: Optional[str] = None):
        """Return (score 0-100, rating_label, reason_text)."""
        score = 50
        reasons = []
        filepath_lower = filepath.lower()
        ext = cls._get_extension(filepath_lower)

        for pattern, ps, desc in cls.SAFE_CACHE_PATTERNS:
            if re.search(pattern, filepath, re.IGNORECASE):
                score = max(score, ps)
                reasons.append(desc)
                break

        for pattern, ps, desc in cls.APP_DATA_PATTERNS:
            if re.search(pattern, filepath, re.IGNORECASE):
                score = ps
                reasons.append(desc)
                break

        if ext in cls.EXTENSION_INFO:
            modifier, ext_desc = cls.EXTENSION_INFO[ext]
            score += modifier
            reasons.append(ext_desc)

        if "/Downloads/" in filepath:
            score += 15
            reasons.append("In Downloads folder")
        if "/Desktop/" in filepath:
            score += 5
            reasons.append("On Desktop — may be temp drop")

        if last_opened_str and last_opened_str not in ("⏳ Pending…", "N/A"):
            if last_opened_str == "Never / Unknown":
                score += 15
                reasons.append("Never opened on this Mac")
            else:
                try:
                    last_dt = datetime.strptime(last_opened_str, "%Y-%m-%d %I:%M %p")
                    days_ago = (datetime.now() - last_dt).days
                    if days_ago > 730:
                        score += 20
                        reasons.append(f"Not opened in {days_ago // 365}+ years")
                    elif days_ago > 365:
                        score += 15
                        reasons.append("Not opened in over a year")
                    elif days_ago > 180:
                        score += 10
                        reasons.append("Not opened in 6+ months")
                    elif days_ago > 90:
                        score += 5
                        reasons.append("Not opened in 3+ months")
                    elif days_ago < 7:
                        score -= 15
                        reasons.append("Opened recently")
                    elif days_ago < 30:
                        score -= 5
                        reasons.append("Opened within last month")
                except ValueError:
                    pass

        if size_bytes > 5 * 1024 ** 3:
            reasons.append(f"Very large ({size_bytes / (1024**3):.1f} GB)")

        basename = os.path.basename(filepath_lower)
        if "copy" in basename or re.search(r'\(\d+\)', basename):
            score += 10
            reasons.append("Possible duplicate")

        score = max(0, min(100, score))

        if score >= 65:
            label = "🟢 Likely Safe"
        elif score >= 40:
            label = "🟡 Review"
        else:
            label = "🔴 Keep"

        return score, label, " • ".join(reasons) if reasons else "No specific indicators"

    @staticmethod
    def _get_extension(filepath: str) -> str:
        base = os.path.basename(filepath)
        if base.endswith(".tar.gz"):
            return ".tar.gz"
        _, ext = os.path.splitext(base)
        return ext.lower()

    @classmethod
    def parse_last_opened_to_days(cls, last_opened_str: str) -> Optional[int]:
        """Convert last-opened string to days ago. None if unparseable."""
        if not last_opened_str or last_opened_str in ("⏳ Pending…", "N/A"):
            return None
        if last_opened_str == "Never / Unknown":
            return 999999
        try:
            last_dt = datetime.strptime(last_opened_str, "%Y-%m-%d %I:%M %p")
            return (datetime.now() - last_dt).days
        except ValueError:
            return None


# ─────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────

def get_app_bundle_root() -> Optional[str]:
    """Return the app bundle root (e.g. .../My App.app) so we can exclude it from scans. None if not in a bundle."""
    try:
        exe = Path(sys.executable).resolve()
        # macOS .app: .../My App.app/Contents/MacOS/python or binary
        if "Contents" in exe.parts and "MacOS" in exe.parts:
            idx = exe.parts.index("Contents")
            return str(Path(*exe.parts[:idx]))
        # Windows or script: no bundle
        return None
    except Exception:
        return None


def format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    elif size_bytes < 1024 ** 4:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    else:
        return f"{size_bytes / (1024 ** 4):.2f} TB"


def get_last_opened(filepath: str) -> Optional[str]:
    """Use macOS mdls to get kMDItemLastUsedDate (Spotlight last-opened)."""
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemLastUsedDate", "-raw", filepath],
            capture_output=True, text=True, timeout=5
        )
        raw = result.stdout.strip()
        if raw and raw != "(null)":
            # Format: 2024-01-15 10:30:00 +0000
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")
                return dt.strftime("%Y-%m-%d %I:%M %p")
            except ValueError:
                return raw
        return "Never / Unknown"
    except Exception:
        return "N/A"


# ─────────────────────────────────────────────────────────────
# Scanner thread
# ─────────────────────────────────────────────────────────────

class ScannerThread(QThread):
    """Background thread to walk the filesystem and find large files.

    Signals are batched (emitted every 250ms or 100 files) to prevent
    flooding the main thread's event loop, which would make the UI unresponsive.
    """
    file_found = pyqtSignal(dict)          # Legacy — unused, kept for compat
    files_found_batch = pyqtSignal(list)   # Batched list of file_info dicts
    scan_progress = pyqtSignal(str, int)   # Current dir, file count so far
    scan_finished = pyqtSignal(int)         # Total files found
    scan_error = pyqtSignal(str)

    BATCH_INTERVAL = 0.25   # seconds between batch emissions
    BATCH_MAX_SIZE = 100    # max files before forcing a batch emit

    def __init__(self, scan_path: str, min_size_bytes: int,
                 include_hidden: bool = False, parent=None):
        super().__init__(parent)
        self.scan_path = scan_path
        self.min_size_bytes = min_size_bytes
        self.include_hidden = include_hidden
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        count = 0
        batch = []
        last_emit_time = time.monotonic()
        last_progress_time = 0.0
        min_size = self.min_size_bytes
        try:
            for dirpath, dir_entries, file_entries in fast_scandir(
                self.scan_path, include_hidden=self.include_hidden
            ):
                if self._stop_requested:
                    break

                for entry in file_entries:
                    if self._stop_requested:
                        break
                    try:
                        # DirEntry.stat() uses readdir cache — no extra syscall
                        st = entry.stat(follow_symlinks=False)
                        if not stat.S_ISREG(st.st_mode):
                            continue
                        if st.st_blocks == 0:  # cloud-only placeholder
                            continue
                        if st.st_size >= min_size:
                            # Defer date formatting to flush phase (save CPU)
                            batch.append({
                                "path": entry.path,
                                "name": entry.name,
                                "size": st.st_size,
                                "modified_ts": st.st_mtime,
                            })
                            count += 1
                    except (PermissionError, OSError):
                        continue

                # Emit file batch + progress at most every 250ms
                now = time.monotonic()
                if batch and (len(batch) >= self.BATCH_MAX_SIZE or now - last_emit_time >= self.BATCH_INTERVAL):
                    self.files_found_batch.emit(batch)
                    batch = []
                    last_emit_time = now
                if now - last_progress_time >= self.BATCH_INTERVAL:
                    self.scan_progress.emit(dirpath, count)
                    last_progress_time = now
                    # Release GIL so the main thread can process UI events
                    time.sleep(0)

        except Exception as e:
            self.scan_error.emit(str(e))

        if batch:
            self.files_found_batch.emit(batch)
        self.scan_finished.emit(count)


# ─────────────────────────────────────────────────────────────
# Build DMG thread (runs build_dmg.sh from project directory)
# ─────────────────────────────────────────────────────────────

class BuildDmgThread(QThread):
    """Run build_dmg.sh in the script's directory."""
    log_line = pyqtSignal(str)
    finished_ok = pyqtSignal(bool, str)  # success, message

    def __init__(self, script_dir: str, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir

    def run(self):
        script = os.path.join(self.script_dir, "build_dmg.sh")
        if not os.path.isfile(script):
            self.finished_ok.emit(False, f"Build script not found.\nRun build_dmg.sh from:\n{self.script_dir}")
            return
        try:
            proc = subprocess.Popen(
                ["/bin/bash", script],
                cwd=self.script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                self.log_line.emit(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                dmg_path = os.path.join(self.script_dir, "MyFileTool.dmg")
                size_str = format_size(os.path.getsize(dmg_path)) if os.path.isfile(dmg_path) else ""
                self.finished_ok.emit(True, f"DMG built successfully.\n{dmg_path}\n{size_str}")
            else:
                self.finished_ok.emit(False, f"Build script exited with code {proc.returncode}.")
        except Exception as e:
            self.finished_ok.emit(False, str(e))


# ─────────────────────────────────────────────────────────────
# Duplicate scanner thread — group by size, then by content hash
# ─────────────────────────────────────────────────────────────

def _file_quick_hash(filepath: str) -> Optional[str]:
    """Quick hash using only first 4KB — fast filter before full hash."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            h.update(f.read(4096))
        return h.hexdigest()
    except (OSError, IOError):
        return None


def _file_content_hash(filepath: str, size_bytes: int, sample_kb: int = 64) -> Optional[str]:
    """Compute a hash from first and last sample_kb of file (for large files)."""
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            head = f.read(sample_kb * 1024)
            h.update(head)
            if size_bytes > 2 * sample_kb * 1024:
                f.seek(-sample_kb * 1024, 2)
                tail = f.read()
                h.update(tail)
        return h.hexdigest()
    except (OSError, IOError):
        return None


def _unique_paths_by_inode(paths: list) -> list:
    """Return one path per distinct (st_ino, st_dev). Filters out path aliases (e.g. /Users/... and /System/Volumes/Data/Users/...)."""
    seen = {}  # (ino, dev) -> path (keep first path seen)
    for p in paths:
        try:
            st = os.stat(p)
            key = (st.st_ino, st.st_dev)
            if key not in seen:
                seen[key] = p
        except (OSError, FileNotFoundError):
            pass
    return list(seen.values())


class DuplicateScannerThread(QThread):
    """Scan for potential duplicate files: same size, then same content hash."""
    group_found = pyqtSignal(dict)       # { "paths": [...], "size": N, "reason": str }
    scan_progress = pyqtSignal(str, int)
    scan_finished = pyqtSignal(int)       # total duplicate groups
    scan_error = pyqtSignal(str)

    def __init__(self, scan_path: str, min_size_bytes: int,
                 include_hidden: bool = False, verify_content: bool = True, parent=None):
        super().__init__(parent)
        self.scan_path = scan_path
        self.min_size_bytes = min_size_bytes
        self.include_hidden = include_hidden
        self.verify_content = verify_content
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        # Phase 1: collect all files >= min_size by size
        size_to_paths = {}  # size -> list of full paths
        file_count = 0
        last_progress_time = 0.0
        min_size = self.min_size_bytes
        try:
            for dirpath, dir_entries, file_entries in fast_scandir(
                self.scan_path, include_hidden=self.include_hidden
            ):
                if self._stop_requested:
                    break
                for entry in file_entries:
                    if self._stop_requested:
                        break
                    try:
                        st = entry.stat(follow_symlinks=False)
                        if not stat.S_ISREG(st.st_mode) or st.st_blocks == 0:
                            continue
                        sz = st.st_size
                        if sz >= min_size:
                            size_to_paths.setdefault(sz, []).append(entry.path)
                            file_count += 1
                    except (PermissionError, OSError):
                        continue
                now = time.monotonic()
                if now - last_progress_time >= 0.25:
                    self.scan_progress.emit(dirpath, file_count)
                    last_progress_time = now
                    time.sleep(0)  # release GIL for main thread
        except Exception as e:
            self.scan_error.emit(str(e))
            self.scan_finished.emit(0)
            return

        # Phase 2: for each size with >1 *distinct* file, verify by hash
        group_count = 0
        for size_bytes, paths in size_to_paths.items():
            if self._stop_requested:
                break
            unique_paths = _unique_paths_by_inode(paths)
            if len(unique_paths) < 2:
                continue
            if self.verify_content:
                # Two-tier hashing: quick hash (first 4KB) then full hash
                quick_hash_to_paths = {}
                for p in unique_paths:
                    h = _file_quick_hash(p)
                    if h is not None:
                        quick_hash_to_paths.setdefault(h, []).append(p)
                for qh_paths in quick_hash_to_paths.values():
                    if len(qh_paths) < 2:
                        continue
                    # Full hash only for files that match on quick hash
                    hash_to_paths = {}
                    for p in qh_paths:
                        h = _file_content_hash(p, size_bytes)
                        if h is not None:
                            hash_to_paths.setdefault(h, []).append(p)
                    for path_list in hash_to_paths.values():
                        path_list = _unique_paths_by_inode(path_list)
                        if len(path_list) >= 2:
                            self.group_found.emit({
                                "paths": path_list,
                                "size": size_bytes,
                                "reason": f"Same size ({format_size(size_bytes)}) and same content (hash match) — likely duplicates",
                            })
                            group_count += 1
            else:
                self.group_found.emit({
                    "paths": unique_paths,
                    "size": size_bytes,
                    "reason": f"Same size ({format_size(size_bytes)}) only — content not verified; may be duplicates",
                })
                group_count += 1

        self.scan_finished.emit(group_count)


# ─────────────────────────────────────────────────────────────
# Sensitive data scanner thread
# ─────────────────────────────────────────────────────────────

SENSITIVE_FINDING_BATCH_SIZE = 200  # Emit findings in batches to avoid 10k+ main-thread slot invocations


class SensitiveScannerThread(QThread):
    """Scan directory for files containing sensitive data (HUID, SSN, TAX, EMAIL)."""
    finding_batch_ready = pyqtSignal(list)  # batch of finding dicts (avoids flooding main thread)
    scan_progress = pyqtSignal(str, int, int)  # current_dir, files_scanned, total_findings
    scan_finished = pyqtSignal(int)    # total findings count
    scan_error = pyqtSignal(str)

    def __init__(self, scan_path: str, active_profiles: list, include_hidden: bool = False,
                 excluded_dirs: list = None, parent=None):
        super().__init__(parent)
        self.scan_path = scan_path
        self.active_profiles = active_profiles
        self.include_hidden = include_hidden
        self.excluded_dirs = list(excluded_dirs) if excluded_dirs else []
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        if not sensitive_scan_file:
            self.scan_error.emit("Sensitive scanner module not available.")
            self.scan_finished.emit(0)
            return

        total_findings = 0
        files_scanned = 0
        batch = []
        last_progress_time = 0.0

        # Phase 1: collect candidate file paths (fast I/O, no CPU-heavy work)
        candidates = []
        try:
            excluded_set = set()
            for p in self.excluded_dirs:
                try:
                    excluded_set.add(os.path.realpath(p))
                except OSError:
                    pass
            for dirpath, dir_entries, file_entries in fast_scandir(
                self.scan_path,
                include_hidden=self.include_hidden,
                excluded_dirs=excluded_set or None,
            ):
                if self._stop_requested:
                    break
                for entry in file_entries:
                    if self._stop_requested:
                        break
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in SENSITIVE_SKIP_EXTENSIONS:
                        continue
                    try:
                        st = entry.stat(follow_symlinks=False)
                        if st.st_size > SENSITIVE_MAX_FILE_SIZE or st.st_size == 0:
                            continue
                    except OSError:
                        continue
                    candidates.append(entry.path)
                # Progress during collection phase
                now = time.monotonic()
                if now - last_progress_time >= 0.25:
                    self.scan_progress.emit(dirpath, len(candidates), 0)
                    last_progress_time = now
                    time.sleep(0)
        except Exception as e:
            self.scan_error.emit(str(e))
            self.scan_finished.emit(0)
            return

        if self._stop_requested:
            self.scan_finished.emit(0)
            return

        # Phase 2: scan files (single-threaded — multiprocessing has too much
        # overhead in py2app bundles). Speed comes from scan_file() optimizations:
        # - Read only first 64KB (not full 10MB files)
        # - Skip digit-based patterns if no digits in content
        # - Early context keyword exit
        total_candidates = len(candidates)
        _profiles = list(self.active_profiles)

        self.scan_progress.emit(
            f"Scanning {total_candidates:,} candidate files…",
            total_candidates, 0,
        )

        try:
            for i, filepath in enumerate(candidates):
                if self._stop_requested:
                    break
                try:
                    file_results = sensitive_scan_file(filepath, _profiles)
                except Exception:
                    file_results = []
                files_scanned += 1
                for r in file_results:
                    total_findings += 1
                    batch.append(r)
                    if len(batch) >= SENSITIVE_FINDING_BATCH_SIZE:
                        self.finding_batch_ready.emit(batch)
                        batch = []
                # Progress (throttled)
                now = time.monotonic()
                if now - last_progress_time >= 0.25:
                    self.scan_progress.emit(
                        f"Scanning ({files_scanned:,}/{total_candidates:,})…",
                        files_scanned, total_findings,
                    )
                    last_progress_time = now

            if batch:
                self.finding_batch_ready.emit(batch)
        except Exception as e:
            self.scan_error.emit(str(e))
            if batch:
                self.finding_batch_ready.emit(batch)
        self.scan_finished.emit(total_findings)


# ─────────────────────────────────────────────────────────────
# String search thread (content grep)
# ─────────────────────────────────────────────────────────────

STRING_SEARCH_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
STRING_SEARCH_SKIP_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.lib', '.zip', '.gz', '.tar', '.bz2', '.7z', '.rar',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.heic', '.mp3', '.mp4', '.avi', '.mov',
    '.mkv', '.wav', '.flac', '.db', '.sqlite', '.pyc', '.pyo', '.class', '.jar', '.woff', '.woff2',
    '.ttf', '.iso', '.dmg', '.img', '.vmdk',
}


class StringSearchThread(QThread):
    """Search files for a string or regex; emit matches in batches.

    Signals are batched (emitted every 250ms or 50 matches) to prevent
    flooding the main thread's event loop.
    """
    match_found = pyqtSignal(dict)       # Legacy — unused, kept for compat
    matches_found_batch = pyqtSignal(list)  # Batched list of match dicts
    scan_progress = pyqtSignal(str, int, int)  # current_dir, files_scanned, match_count
    scan_finished = pyqtSignal(int)
    scan_error = pyqtSignal(str)

    BATCH_INTERVAL = 0.25
    BATCH_MAX_SIZE = 50

    def __init__(self, search_string: str, use_regex: bool, scan_path: str, include_hidden: bool, parent=None):
        super().__init__(parent)
        self.search_string = search_string
        self.use_regex = use_regex
        self.scan_path = scan_path
        self.include_hidden = include_hidden
        self._stop_requested = False
        self._pattern = None
        if use_regex:
            try:
                self._pattern = re.compile(search_string)
            except re.error:
                pass

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        if self.use_regex and self._pattern is None:
            self.scan_error.emit("Invalid regex pattern.")
            self.scan_finished.emit(0)
            return
        match_count = 0
        files_scanned = 0
        batch = []
        last_emit_time = time.monotonic()
        last_progress_time = 0.0
        search_str = self.search_string
        pattern = self._pattern
        use_regex = self.use_regex
        try:
            for dirpath, dir_entries, file_entries in fast_scandir(
                self.scan_path, include_hidden=self.include_hidden
            ):
                if self._stop_requested:
                    break
                for entry in file_entries:
                    if self._stop_requested:
                        break
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in STRING_SEARCH_SKIP_EXTENSIONS:
                        continue
                    try:
                        st = entry.stat(follow_symlinks=False)
                        if st.st_size > STRING_SEARCH_MAX_FILE_SIZE or st.st_size == 0:
                            continue
                    except OSError:
                        continue
                    files_scanned += 1
                    filepath = entry.path
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                            for i, line in enumerate(f, 1):
                                if self._stop_requested:
                                    break
                                matched = (pattern.search(line) if use_regex
                                           else search_str in line)
                                if matched:
                                    snippet = line.strip()[:200] + ("..." if len(line.strip()) > 200 else "")
                                    match_count += 1
                                    batch.append({
                                        "file": entry.name,
                                        "path": dirpath,
                                        "line_num": i,
                                        "snippet": snippet,
                                        "full_path": filepath,
                                    })
                    except (OSError, ValueError):
                        continue

                # Emit match batch + progress at most every 250ms
                now = time.monotonic()
                if batch and (len(batch) >= self.BATCH_MAX_SIZE or now - last_emit_time >= self.BATCH_INTERVAL):
                    self.matches_found_batch.emit(batch)
                    batch = []
                    last_emit_time = now
                if now - last_progress_time >= self.BATCH_INTERVAL:
                    self.scan_progress.emit(dirpath, files_scanned, match_count)
                    last_progress_time = now
                    time.sleep(0)  # release GIL for main thread
        except Exception as e:
            self.scan_error.emit(str(e))
        if batch:
            self.matches_found_batch.emit(batch)
        self.scan_finished.emit(match_count)


# ─────────────────────────────────────────────────────────────
# Last-Opened fetcher thread (batch mdls for performance)
# ─────────────────────────────────────────────────────────────

MDLS_BATCH_SIZE = 50  # Files per mdls subprocess call


def _batch_get_last_opened(filepaths: list) -> dict:
    """Batch-query Spotlight metadata for multiple files via mdls.

    Returns dict of {filepath: formatted_date_string}.
    Processes in chunks of MDLS_BATCH_SIZE to avoid command-line length limits.
    """
    results = {}
    for start in range(0, len(filepaths), MDLS_BATCH_SIZE):
        chunk = filepaths[start:start + MDLS_BATCH_SIZE]
        try:
            proc = subprocess.run(
                ["mdls", "-name", "kMDItemLastUsedDate"] + chunk,
                capture_output=True, text=True, timeout=30,
            )
            # mdls outputs one block per file, separated by the filepath
            # Each block: "kMDItemLastUsedDate = 2024-01-15 10:30:00 +0000" or "(null)"
            lines = proc.stdout.splitlines()
            file_idx = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith("---"):
                    continue
                if "kMDItemLastUsedDate" in line:
                    if file_idx < len(chunk):
                        filepath = chunk[file_idx]
                        file_idx += 1
                        if "(null)" in line:
                            results[filepath] = "Never / Unknown"
                        else:
                            # Extract date value after "="
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                raw = parts[1].strip()
                                try:
                                    dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")
                                    results[filepath] = dt.strftime("%Y-%m-%d %I:%M %p")
                                except ValueError:
                                    results[filepath] = "N/A"
                            else:
                                results[filepath] = "N/A"
        except (subprocess.TimeoutExpired, OSError):
            # On failure, mark remaining in chunk as N/A
            for fp in chunk:
                if fp not in results:
                    results[fp] = "N/A"
    return results


class LastOpenedFetcher(QThread):
    """Background thread to batch-fetch kMDItemLastUsedDate for files."""
    result_ready = pyqtSignal(int, str)  # row index, last_opened string
    fetch_finished = pyqtSignal()

    def __init__(self, file_paths: list, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths  # list of (row_index, filepath)
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        # Build list of filepaths for batch query
        paths_only = [fp for _, fp in self.file_paths]
        row_map = {fp: row_idx for row_idx, fp in self.file_paths}

        batch_results = _batch_get_last_opened(paths_only)

        for filepath, last_opened in batch_results.items():
            if self._stop_requested:
                break
            row_idx = row_map.get(filepath)
            if row_idx is not None:
                self.result_ready.emit(row_idx, last_opened)

        # Emit N/A for any files not in results
        for row_idx, filepath in self.file_paths:
            if self._stop_requested:
                break
            if filepath not in batch_results:
                self.result_ready.emit(row_idx, "N/A")

        self.fetch_finished.emit()


# ─────────────────────────────────────────────────────────────
# Custom sortable table item
# ─────────────────────────────────────────────────────────────

class SizeTableItem(QTableWidgetItem):
    """Table item that sorts by raw byte value, not display string."""
    def __init__(self, display_text: str, sort_value):
        super().__init__(display_text)
        self._sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, SizeTableItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)


# ─────────────────────────────────────────────────────────────
# All-locations dialog (duplicate mode)
# ─────────────────────────────────────────────────────────────

class AllLocationsDialog(QDialog):
    """Show all file paths for a duplicate group, with Copy button."""
    def __init__(self, paths: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("All locations — duplicate group")
        self.setMinimumSize(560, 320)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"All {len(paths)} location(s):"))
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText("\n".join(paths))
        self.text.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text)
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        copy_btn = QPushButton("Copy to clipboard")
        copy_btn.clicked.connect(self._copy)
        btn_box.addButton(copy_btn, QDialogButtonBox.ActionRole)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

    def _copy(self):
        QApplication.clipboard().setText(self.text.toPlainText())


# ─────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────

class MyhFileFinder(QMainWindow):
    # Column indices
    COL_CHECK = 0
    COL_NAME = 1
    COL_PATH = 2
    COL_SIZE = 3
    COL_MODIFIED = 4
    COL_LAST_OPENED = 5
    COL_CONFIDENCE = 6

    FLUSH_CHUNK_SIZE = 200  # rows per flush chunk (timer-based incremental flush)

    SIZE_FILTERS = {
        "100 MB+": 100 * 1024 ** 2,
        "250 MB+": 250 * 1024 ** 2,
        "500 MB+": 500 * 1024 ** 2,
        "1 GB+": 1024 ** 3,
        "5 GB+": 5 * 1024 ** 3,
        "50 MB+": 50 * 1024 ** 2,
        "10 MB+": 10 * 1024 ** 2,
    }

    # Sensitive mode column indices (12 columns: one row per file, HUID/SSN/TAX/EMAIL checkmarks)
    SCOL_CHECK, SCOL_CONF, SCOL_HUID, SCOL_SSN, SCOL_TAX, SCOL_EMAIL, SCOL_NAME, SCOL_PATH, SCOL_HITS, SCOL_SIZE, SCOL_MODIFIED, SCOL_SAMPLE = range(12)
    _CONF_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    # String search mode column indices
    TCOL_FILE, TCOL_PATH, TCOL_LINE, TCOL_SNIPPET = range(4)

    def __init__(self):
        super().__init__()
        from update_checker import get_app_version
        self._app_version = get_app_version()
        self.setWindowTitle(f"my.File Tool v{self._app_version} — Sensitive / Duplicates / Large / String search")
        self.setWindowIcon(load_app_icon())
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        # State
        self._update_thread = None
        self._update_check_manual = False
        self._update_release_url = None
        self.all_files = []  # Master list of all found files (dicts)
        self.duplicate_groups = []  # List of { paths, size, reason } for duplicate mode
        self.sensitive_findings = []  # One aggregated finding dict per file (for count/filter)
        self._sensitive_file_aggregate = {}  # path -> aggregated data (profiles, confidence, hits, samples, etc.)
        self._sensitive_path_to_row = {}   # path -> table row index (for updating same file)
        self._sensitive_findings_buffer = []  # Findings collected during scan; flushed when scan finishes (avoids UI freeze)
        self.string_search_matches = []  # List of match dicts for string search mode
        self.excluded_dirs_list = load_excluded_dirs() if load_excluded_dirs else []
        self.scanner_thread = None
        self.fetcher_thread = None
        self.build_dmg_thread = None
        self.scan_start_time = None
        self._script_dir = os.path.dirname(os.path.abspath(__file__))
        self._scan_mode = "sensitive"  # "sensitive" | "duplicates" | "large" | "string_search"
        self._scan_placeholder_row = -1
        self._scan_placeholder_timer = None
        self._last_progress_ui_update = 0.0  # throttle status label updates (seconds)
        self._scan_files_scanned = 0
        self._scan_findings_count = 0

        self._build_ui()

        # Install global exception handler for crash reporting
        self._install_exception_handler()

        # Auto-check for updates silently after a short delay (let UI render first)
        QTimer.singleShot(2000, self._auto_check_for_updates)
        # Re-check every 12 hours in case the app stays open
        self._update_interval_timer = QTimer(self)
        self._update_interval_timer.timeout.connect(self._auto_check_for_updates)
        self._update_interval_timer.start(12 * 60 * 60 * 1000)  # 12 hours in ms

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Menu bar ──────────────────────────────────────
        menubar = self.menuBar()
        help_menu = menubar.addMenu("&Help")
        check_updates_action = QAction("Check for Updates…", self)
        check_updates_action.triggered.connect(self._manual_check_for_updates)
        help_menu.addAction(check_updates_action)
        help_menu.addSeparator()
        report_bug_action = QAction("Report a Bug…", self)
        report_bug_action.triggered.connect(self._report_bug)
        help_menu.addAction(report_bug_action)

        help_menu.addSeparator()
        about_action = QAction(f"About my.h File Finder v{self._app_version}", self)
        about_action.triggered.connect(lambda: QMessageBox.about(
            self, "About my.h File Finder",
            f"my.h File Finder v{self._app_version}\n\n"
            "Scan for sensitive data, duplicates, large files, or search file content.\n\n"
            "Built for macOS.\n"
            "https://github.com/madore9/myh_file_finder"
        ))
        help_menu.addAction(about_action)

        # ── Update notification banner (hidden by default) ──
        self._update_banner = QFrame()
        self._update_banner.setVisible(False)
        self._update_banner.setStyleSheet("""
            QFrame {
                background-color: #FFF3CD;
                border: 1px solid #FFD866;
                border-radius: 6px;
            }
        """)
        banner_layout = QHBoxLayout(self._update_banner)
        banner_layout.setContentsMargins(12, 6, 12, 6)
        self._update_banner_label = QLabel("")
        self._update_banner_label.setStyleSheet("color: #664D03; font-size: 13px;")
        banner_layout.addWidget(self._update_banner_label)
        banner_layout.addStretch()
        install_btn = QPushButton("Install Update")
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759; color: white;
                border: none; border-radius: 4px;
                padding: 4px 14px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2DA44E; }
        """)
        install_btn.clicked.connect(self._start_update_download)
        banner_layout.addWidget(install_btn)
        view_btn = QPushButton("View Release")
        view_btn.setStyleSheet("font-size: 12px; color: #664D03; border: none; padding: 4px 8px;")
        view_btn.clicked.connect(self._open_update_page)
        banner_layout.addWidget(view_btn)
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setStyleSheet("font-size: 12px; color: #664D03; border: none; padding: 4px 8px;")
        dismiss_btn.clicked.connect(lambda: self._update_banner.setVisible(False))
        banner_layout.addWidget(dismiss_btn)
        layout.addWidget(self._update_banner)

        # ── Top controls ──────────────────────────────────
        controls_group = QGroupBox("Scan Settings")
        controls_layout = QHBoxLayout(controls_group)

        # Scan mode: Sensitive | Duplicates | Large | String search
        controls_layout.addWidget(QLabel("Mode:"))
        self.scan_mode_combo = QComboBox()
        self.scan_mode_combo.addItems(["Sensitive files", "Duplicates", "Large files", "String search"])
        self.scan_mode_combo.currentIndexChanged.connect(self._on_scan_mode_changed)
        controls_layout.addWidget(self.scan_mode_combo)

        controls_layout.addSpacing(16)

        # Scan path
        controls_layout.addWidget(QLabel("Scan Path:"))
        self.path_input = QLineEdit("/" if os.name != "nt" else "C:\\")
        self.path_input.setMinimumWidth(200)
        controls_layout.addWidget(self.path_input)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_path)
        controls_layout.addWidget(browse_btn)

        controls_layout.addSpacing(20)

        # Size filter (hidden in sensitive mode)
        self.size_filter_label = QLabel("Min Size:")
        controls_layout.addWidget(self.size_filter_label)
        self.size_filter = QComboBox()
        self.size_filter.addItems(["100 MB+", "250 MB+", "500 MB+", "1 GB+", "5 GB+", "50 MB+", "10 MB+"])
        self.size_filter.setCurrentIndex(0)
        controls_layout.addWidget(self.size_filter)

        controls_layout.addSpacing(20)

        # Hidden files toggle
        self.hidden_check = QCheckBox("Include hidden files")
        self.hidden_check.setChecked(False)
        controls_layout.addWidget(self.hidden_check)

        # Duplicate mode: verify content (hash)
        self.verify_content_check = QCheckBox("Verify content (hash)")
        self.verify_content_check.setChecked(True)
        self.verify_content_check.setToolTip("When finding duplicates, compare file content by hash (slower but more accurate).")
        controls_layout.addWidget(self.verify_content_check)
        self.verify_content_check.setVisible(False)

        controls_layout.addStretch()

        # Scan button
        self.scan_btn = QPushButton()
        self._scan_btn_style_start()
        self.scan_btn.clicked.connect(self._toggle_scan)
        controls_layout.addWidget(self.scan_btn)

        layout.addWidget(controls_group)

        # ── Sensitive-only: profiles + excluded dirs ───────
        self.sensitive_options = QFrame()
        self.sensitive_options.setVisible(True)
        sens_layout = QVBoxLayout(self.sensitive_options)
        sens_row1 = QHBoxLayout()
        sens_row1.addWidget(QLabel("Profiles:"))
        self.profile_checks = {}
        for key in ("HUID", "SSN", "EMAIL"):
            if key not in SENSITIVE_PROFILES:
                continue
            cb = QCheckBox(key)
            cb.setChecked(True)
            self.profile_checks[key] = cb
            sens_row1.addWidget(cb)
        sens_row1.addStretch()
        self.skip_app_system_check = QCheckBox("Skip app & system data")
        self.skip_app_system_check.setChecked(True)
        self.skip_app_system_check.setToolTip(
            "Skip browser profiles, app caches, Library internals, and other\n"
            "app-managed directories that produce false positives.\n"
            "Recommended ON for most scans."
        )
        sens_row1.addWidget(self.skip_app_system_check)
        sens_layout.addLayout(sens_row1)
        sens_row2 = QHBoxLayout()
        sens_row2.addWidget(QLabel("Exclude folders:"))
        self.excluded_list = QListWidget()
        self.excluded_list.setMaximumHeight(56)
        self.excluded_list.setMinimumWidth(200)
        sens_row2.addWidget(self.excluded_list)
        add_excl_btn = QPushButton("Add…")
        add_excl_btn.clicked.connect(self._add_excluded_folder)
        sens_row2.addWidget(add_excl_btn)
        rem_excl_btn = QPushButton("Remove")
        rem_excl_btn.clicked.connect(self._remove_excluded_folder)
        sens_row2.addWidget(rem_excl_btn)
        sens_layout.addLayout(sens_row2)
        self._refresh_excluded_list()
        layout.addWidget(self.sensitive_options)

        # ── String search-only: search string + regex ─────
        self.string_search_options = QFrame()
        self.string_search_options.setVisible(False)
        ss_layout = QHBoxLayout(self.string_search_options)
        ss_layout.addWidget(QLabel("Search for:"))
        self.string_search_input = QLineEdit()
        self.string_search_input.setPlaceholderText("e.g. password, API key, hostname…")
        self.string_search_input.setMinimumWidth(280)
        ss_layout.addWidget(self.string_search_input)
        self.string_search_regex_check = QCheckBox("Use regex")
        self.string_search_regex_check.setChecked(False)
        ss_layout.addWidget(self.string_search_regex_check)
        ss_layout.addStretch()
        layout.addWidget(self.string_search_options)

        # ── Progress bar ──────────────────────────────────
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(8)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

        # ── Status / summary bar ──────────────────────────
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready — choose a path and start scanning.")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #333; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.summary_label)

        layout.addLayout(status_layout)

        # ── Filter bar (post-scan) ────────────────────────
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by filename or path…")
        self.search_input.textChanged.connect(self._apply_table_filter)
        filter_layout.addWidget(self.search_input)

        filter_layout.addSpacing(20)

        filter_layout.addWidget(QLabel("Show:"))
        self.display_filter = QComboBox()
        self.display_filter.addItems(["All Results", "100 MB+", "250 MB+", "500 MB+", "1 GB+", "5 GB+"])
        self.display_filter.currentIndexChanged.connect(self._apply_table_filter)
        filter_layout.addWidget(self.display_filter)

        # Sensitive mode: show filter (HIGH/MEDIUM/LOW, profile)
        self.sensitive_show_label = QLabel("Show:")
        self.sensitive_show_filter = QComboBox()
        self.sensitive_show_filter.addItems([
            "All Results", "HIGH Only", "MEDIUM Only", "LOW Only",
            "HUID Only", "SSN Only", "EMAIL Only"
        ])
        self.sensitive_show_filter.currentIndexChanged.connect(self._apply_table_filter)
        filter_layout.addWidget(self.sensitive_show_label)
        filter_layout.addWidget(self.sensitive_show_filter)
        self.sensitive_show_label.setVisible(False)
        self.sensitive_show_filter.setVisible(False)

        filter_layout.addSpacing(20)

        # v4: Not opened since filter (hidden in duplicate and sensitive mode)
        self.opened_filter_label = QLabel("Not opened in:")
        filter_layout.addWidget(self.opened_filter_label)
        self.opened_filter = QComboBox()
        self.opened_filter.addItems([
            "Any time", "3+ months", "6+ months", "1+ year", "2+ years", "Never opened"
        ])
        self.opened_filter.currentIndexChanged.connect(self._apply_table_filter)
        filter_layout.addWidget(self.opened_filter)

        filter_layout.addSpacing(20)

        # v4: Confidence filter (hidden in duplicate and sensitive mode)
        self.confidence_filter_label = QLabel("Rating:")
        filter_layout.addWidget(self.confidence_filter_label)
        self.confidence_filter = QComboBox()
        self.confidence_filter.addItems([
            "All", "🟢 Likely Safe", "🟡 Review", "🔴 Keep"
        ])
        self.confidence_filter.currentIndexChanged.connect(self._apply_table_filter)
        filter_layout.addWidget(self.confidence_filter)

        layout.addLayout(filter_layout)

        # ── Results table ─────────────────────────────────
        self.table = QTableWidget()
        self._set_table_columns_large_files()
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        # Double-click: reveal in Finder (large/sensitive) or show all locations (duplicates)
        self.table.cellDoubleClicked.connect(self._on_row_double_click)
        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_context_menu)

        layout.addWidget(self.table, stretch=1)

        # ── Action buttons ────────────────────────────────
        action_layout = QHBoxLayout()

        # Selection buttons
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        action_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        action_layout.addWidget(self.deselect_all_btn)

        self.invert_btn = QPushButton("Invert Selection")
        self.invert_btn.clicked.connect(self._invert_selection)
        action_layout.addWidget(self.invert_btn)

        action_layout.addSpacing(20)

        # Selection count
        self.selection_label = QLabel("0 files selected (0 B)")
        self.selection_label.setStyleSheet("color: #333; font-size: 12px;")
        action_layout.addWidget(self.selection_label)

        action_layout.addStretch()

        # v3: "Reveal in Finder" removed — double-click any row instead

        # Move to Trash
        self.delete_btn = QPushButton("  Move to Trash  ")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #D63028; }
            QPushButton:disabled { background-color: #999; }
        """)
        self.delete_btn.clicked.connect(self._delete_selected)
        action_layout.addWidget(self.delete_btn)

        layout.addLayout(action_layout)

        # Connect checkbox monitoring
        self.table.cellChanged.connect(self._on_cell_changed)

        # Initial mode: Sensitive (index 0); sync columns and visibility
        self.scan_mode_combo.setCurrentIndex(0)
        self._on_scan_mode_changed()

        # Theme-aware table header and labels (readable in dark mode)
        self._apply_table_theme()

    def _set_table_columns_large_files(self):
        """Set table to large-files view (7 columns)."""
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "✓", "File Name", "Location", "Size", "Modified", "Last Opened", "Safe to Delete?"
        ])
        header = self.table.horizontalHeader()
        for col in range(7):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 350)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 155)
        self.table.setColumnWidth(5, 155)
        self.table.setColumnWidth(6, 130)

    def _set_table_columns_duplicates(self):
        """Set table to duplicate-groups view (4 columns)."""
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Why duplicate", "Size", "# Copies", "Locations"
        ])
        header = self.table.horizontalHeader()
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 400)

    def _set_table_columns_sensitive(self):
        """Set table to sensitive findings view (12 columns): one row per file, HUID/SSN/TAX/EMAIL checkmarks."""
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "✓", "Confidence", "HUID", "SSN", "TAX", "EMAIL", "File Name", "Location", "Hits", "Size", "Modified", "Sample (masked)"
        ])
        header = self.table.horizontalHeader()
        for col in range(12):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 85)
        self.table.setColumnWidth(2, 45)
        self.table.setColumnWidth(3, 45)
        self.table.setColumnHidden(4, True)  # TAX column — hidden until enabled
        self.table.setColumnWidth(5, 50)
        self.table.setColumnWidth(6, 180)
        self.table.setColumnWidth(7, 280)
        self.table.setColumnWidth(8, 50)
        self.table.setColumnWidth(9, 80)
        self.table.setColumnWidth(10, 120)
        self.table.setColumnWidth(11, 180)

    def _set_table_columns_string_search(self):
        """Set table to string search results (4 columns)."""
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File", "Path", "Line #", "Snippet"])
        header = self.table.horizontalHeader()
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 350)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 400)

    def _apply_table_theme(self):
        """Apply theme-aware styles for table header and status/summary so dark mode is readable."""
        palette = self.palette()
        bg = palette.color(QPalette.Window)
        is_dark = bg.lightness() < 128
        if is_dark:
            self.table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #404040;
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 4px;
                }
                QHeaderView::section {
                    background-color: #3d3d3d;
                    color: #e8e8e8;
                    padding: 6px;
                    border: 1px solid #555;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self.status_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
            self.summary_label.setStyleSheet("color: #d0d0d0; font-weight: bold; font-size: 12px;")
            self.selection_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        else:
            self.table.setStyleSheet("""
                QTableWidget {
                    gridline-color: #e0e0e0;
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 4px;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    color: #1a1a1a;
                    padding: 6px;
                    border: 1px solid #ddd;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")
            self.summary_label.setStyleSheet("color: #333; font-weight: bold; font-size: 12px;")
            self.selection_label.setStyleSheet("color: #333; font-size: 12px;")

    def _refresh_excluded_list(self):
        self.excluded_list.clear()
        home_str = str(Path.home())
        for p in self.excluded_dirs_list:
            display = p.replace(home_str, "~") if p.startswith(home_str) else p
            self.excluded_list.addItem(display)

    def _add_excluded_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Exclude folder from scans", self.path_input.text())
        if not path:
            return
        try:
            normalized = os.path.realpath(path)
            if normalized not in self.excluded_dirs_list:
                self.excluded_dirs_list.append(normalized)
                if save_excluded_dirs:
                    save_excluded_dirs(self.excluded_dirs_list)
                self._refresh_excluded_list()
        except OSError:
            pass

    def _exclude_directory_from_menu(self, dirpath: str):
        """Add a directory to the exclude list from the right-click context menu."""
        try:
            normalized = os.path.realpath(dirpath)
            if normalized not in self.excluded_dirs_list:
                self.excluded_dirs_list.append(normalized)
                if save_excluded_dirs:
                    save_excluded_dirs(self.excluded_dirs_list)
                self._refresh_excluded_list()
                short = dirpath.replace(str(Path.home()), "~") if dirpath.startswith(str(Path.home())) else dirpath
                self.status_label.setText(f"Excluded: {short}")
        except OSError:
            pass

    def _remove_excluded_folder(self):
        row = self.excluded_list.currentRow()
        if row < 0:
            return
        self.excluded_dirs_list.pop(row)
        if save_excluded_dirs:
            save_excluded_dirs(self.excluded_dirs_list)
        self._refresh_excluded_list()

    def _on_scan_mode_changed(self):
        """Switch between Sensitive, Duplicates, Large, String search; show/hide options."""
        idx = self.scan_mode_combo.currentIndex()
        self._scan_mode = ["sensitive", "duplicates", "large", "string_search"][idx]
        is_sensitive = self._scan_mode == "sensitive"
        is_dup = self._scan_mode == "duplicates"
        is_large = self._scan_mode == "large"
        is_string_search = self._scan_mode == "string_search"

        self.sensitive_options.setVisible(is_sensitive)
        self.string_search_options.setVisible(is_string_search)
        self.size_filter_label.setVisible(not is_sensitive and not is_string_search)
        self.size_filter.setVisible(not is_sensitive and not is_string_search)
        self.verify_content_check.setVisible(is_dup)
        self.opened_filter_label.setVisible(is_large)
        self.opened_filter.setVisible(is_large)
        self.confidence_filter_label.setVisible(is_large)
        self.confidence_filter.setVisible(is_large)
        self.display_filter.setVisible(is_large or is_dup)
        self.sensitive_show_label.setVisible(is_sensitive)
        self.sensitive_show_filter.setVisible(is_sensitive)

        has_checkboxes = not is_string_search
        self.delete_btn.setEnabled(has_checkboxes)
        self.select_all_btn.setEnabled(has_checkboxes)
        self.deselect_all_btn.setEnabled(has_checkboxes)
        self.invert_btn.setEnabled(has_checkboxes)
        if is_sensitive:
            self.delete_btn.setText("  Secure Delete  ")
        else:
            self.delete_btn.setText("  Move to Trash  ")

        if self._scan_mode == "sensitive":
            self._set_table_columns_sensitive()
        elif self._scan_mode == "duplicates":
            self._set_table_columns_duplicates()
        elif self._scan_mode == "string_search":
            self._set_table_columns_string_search()
        else:
            self._set_table_columns_large_files()
        # Clear table when switching mode
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.all_files.clear()
        self.duplicate_groups.clear()
        self.sensitive_findings.clear()
        self._sensitive_file_aggregate.clear()
        self._sensitive_path_to_row.clear()
        self._sensitive_findings_buffer.clear()
        self.string_search_matches.clear()
        self.summary_label.setText("")
        self.selection_label.setText("0 files selected (0 B)")

    def _on_build_dmg(self):
        """Run build_dmg.sh from project directory and show result."""
        if self.build_dmg_thread and self.build_dmg_thread.isRunning():
            QMessageBox.information(self, "Build in progress", "A DMG build is already running.")
            return
        script = os.path.join(self._script_dir, "build_dmg.sh")
        if not os.path.isfile(script):
            QMessageBox.warning(
                self, "Build DMG",
                f"Build script not found.\n\nRun build_dmg.sh from the project directory:\n{self._script_dir}"
            )
            return
        self.build_dmg_thread = BuildDmgThread(self._script_dir)
        log_lines = []

        def on_log(line):
            log_lines.append(line)

        def on_done(ok, msg):
            self.build_dmg_thread = None
            if ok:
                QMessageBox.information(self, "Build DMG", msg)
            else:
                QMessageBox.warning(self, "Build DMG", msg)

        self.build_dmg_thread.log_line.connect(on_log)
        self.build_dmg_thread.finished_ok.connect(on_done)
        self.build_dmg_thread.start()
        QMessageBox.information(
            self, "Build DMG",
            "DMG build started in the background. You will see a message when it finishes.\n\nYou can keep using the app."
        )

    # ── Scan controls ─────────────────────────────────────

    def _scan_btn_style_start(self):
        """Blue 'Start Scan' button style."""
        self.scan_btn.setText("  Start Scan  ")
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #005ECB; }
            QPushButton:pressed { background-color: #004AAD; }
            QPushButton:disabled { background-color: #999; }
        """)

    def _scan_btn_style_stop(self):
        """Orange 'Stop Scan' button style."""
        self.scan_btn.setText("  Stop Scan  ")
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #CC7700; }
        """)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Scan Directory", self.path_input.text())
        if path:
            self.path_input.setText(path)

    def _toggle_scan(self):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self._stop_scan()
        else:
            self._start_scan()

    def _add_scan_placeholder_row(self):
        """Show a single row in the table: 'Scan in progress. Results will appear here when complete.' with elapsed/rate."""
        self._scan_placeholder_row = 0
        self._scan_files_scanned = 0
        self._scan_findings_count = 0
        self.table.insertRow(0)
        cols = self.table.columnCount()
        self.table.setSpan(0, 0, 1, cols)
        msg_item = QTableWidgetItem("File scan in progress. Results will appear here when complete.  Elapsed: 0:00  |  —")
        msg_item.setFlags(msg_item.flags() & ~Qt.ItemIsEditable)
        # Theme-aware muted text (readable in dark mode)
        is_dark = self.palette().color(QPalette.Window).lightness() < 128
        msg_item.setForeground(QColor("#b0b0b0" if is_dark else "#666"))
        self.table.setItem(0, 0, msg_item)
        if self._scan_placeholder_timer is None:
            self._scan_placeholder_timer = QTimer(self)
            self._scan_placeholder_timer.timeout.connect(self._update_scan_placeholder)
        self._scan_placeholder_timer.start(1000)

    def _remove_scan_placeholder(self):
        """Remove the scan-in-progress placeholder row and stop the timer."""
        if self._scan_placeholder_timer:
            self._scan_placeholder_timer.stop()
        if self._scan_placeholder_row >= 0 and self.table.rowCount() > 0:
            self.table.removeRow(0)
            self._scan_placeholder_row = -1

    def _update_scan_placeholder(self):
        """Refresh the placeholder row text with elapsed time, files scanned, and rate (no time estimate)."""
        if self._scan_placeholder_row < 0 or self.table.rowCount() == 0:
            return
        if not self.scanner_thread or not self.scanner_thread.isRunning():
            self._remove_scan_placeholder()
            return
        elapsed = time.time() - self.scan_start_time
        m, s = int(elapsed) // 60, int(elapsed) % 60
        elapsed_str = f"{m}:{s:02d}"
        if self._scan_mode == "sensitive":
            rate = self._scan_files_scanned / elapsed if elapsed > 0 else 0
            rate_str = f"~{rate:.0f} files/s" if rate else "—"
            msg = (
                f"File scan in progress. Results will appear here when complete.  "
                f"Elapsed: {elapsed_str}  |  Files scanned: {self._scan_files_scanned:,}  |  "
                f"Found: {self._scan_findings_count}  |  Rate: {rate_str}"
            )
        elif self._scan_mode == "duplicates":
            msg = (
                f"File scan in progress. Results will appear here when complete.  "
                f"Elapsed: {elapsed_str}  |  Duplicate candidates so far: {self._scan_files_scanned:,}"
            )
        elif self._scan_mode == "string_search":
            msg = (
                f"File scan in progress. Results will appear here when complete.  "
                f"Elapsed: {elapsed_str}  |  Files scanned: {self._scan_files_scanned:,}  |  "
                f"Matches: {self._scan_findings_count}"
            )
        else:
            msg = (
                f"File scan in progress. Results will appear here when complete.  "
                f"Elapsed: {elapsed_str}  |  Large files found so far: {self._scan_files_scanned:,}"
            )
        item = self.table.item(0, 0)
        if item:
            item.setText(msg)

    def _start_scan(self):
        scan_path = self.path_input.text().strip()
        if not scan_path:
            QMessageBox.warning(self, "Invalid Path", "Enter a scan path.")
            return
        try:
            scan_path = os.path.abspath(os.path.realpath(scan_path))
        except OSError:
            pass
        if not os.path.isdir(scan_path):
            QMessageBox.warning(self, "Invalid Path", f"'{scan_path}' is not a valid directory.")
            return

        # Stop any running flush timer from a previous scan
        if hasattr(self, '_flush_timer') and self._flush_timer and self._flush_timer.isActive():
            self._flush_timer.stop()

        # Stop any running fetcher
        if self.fetcher_thread and self.fetcher_thread.isRunning():
            self.fetcher_thread.request_stop()
            self.fetcher_thread.wait()

        # Clear previous results
        self.all_files.clear()
        self.duplicate_groups.clear()
        self.sensitive_findings.clear()
        self._sensitive_file_aggregate.clear()
        self._sensitive_path_to_row.clear()
        self._sensitive_findings_buffer.clear()
        self.string_search_matches.clear()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.summary_label.setText("")
        self._add_scan_placeholder_row()

        min_size = self.SIZE_FILTERS.get(self.size_filter.currentText(), 100 * 1024 ** 2)

        if self._scan_mode == "string_search":
            search_str = self.string_search_input.text().strip()
            if not search_str:
                QMessageBox.warning(self, "Empty Search", "Enter a string to search for.")
                self._remove_scan_placeholder()
                return
            if self.string_search_regex_check.isChecked():
                try:
                    re.compile(search_str)
                except re.error as e:
                    QMessageBox.warning(self, "Invalid Regex", f"Invalid regex pattern:\n{e}")
                    self._remove_scan_placeholder()
                    return
            self.scanner_thread = StringSearchThread(
                search_string=search_str,
                use_regex=self.string_search_regex_check.isChecked(),
                scan_path=scan_path,
                include_hidden=self.hidden_check.isChecked(),
            )
            self.scanner_thread.matches_found_batch.connect(self._on_string_search_matches_batch)
            self.scanner_thread.scan_progress.connect(self._on_string_search_progress)
            self.scanner_thread.scan_finished.connect(self._on_string_search_finished)
            self.scanner_thread.scan_error.connect(self._on_scan_error)
        elif self._scan_mode == "sensitive":
            active = [k for k, cb in self.profile_checks.items() if cb.isChecked()]
            if not active:
                QMessageBox.warning(self, "No Profiles", "Select at least one scan profile (HUID, SSN, EMAIL).")
                return
            excluded_dirs = list(self.excluded_dirs_list)
            bundle_root = get_app_bundle_root()
            if bundle_root:
                try:
                    excluded_dirs.append(os.path.realpath(bundle_root))
                except OSError:
                    excluded_dirs.append(bundle_root)
            # Add app/system data directories when checkbox is enabled
            if self.skip_app_system_check.isChecked():
                from scan_utils import get_app_system_skip_dirs
                excluded_dirs.extend(get_app_system_skip_dirs())
            self.scanner_thread = SensitiveScannerThread(
                scan_path=scan_path,
                active_profiles=active,
                include_hidden=self.hidden_check.isChecked(),
                excluded_dirs=excluded_dirs,
            )
            self.scanner_thread.finding_batch_ready.connect(self._on_sensitive_finding_batch)
            self.scanner_thread.scan_progress.connect(self._on_sensitive_scan_progress)
            self.scanner_thread.scan_finished.connect(self._on_sensitive_scan_finished)
            self.scanner_thread.scan_error.connect(self._on_scan_error)
        elif self._scan_mode == "duplicates":
            self.scanner_thread = DuplicateScannerThread(
                scan_path=scan_path,
                min_size_bytes=min_size,
                include_hidden=self.hidden_check.isChecked(),
                verify_content=self.verify_content_check.isChecked(),
            )
            self.scanner_thread.group_found.connect(self._on_duplicate_group_found)
            self.scanner_thread.scan_progress.connect(self._on_scan_progress)
            self.scanner_thread.scan_finished.connect(self._on_duplicate_scan_finished)
            self.scanner_thread.scan_error.connect(self._on_scan_error)
        else:
            self.scanner_thread = ScannerThread(
                scan_path=scan_path,
                min_size_bytes=min_size,
                include_hidden=self.hidden_check.isChecked()
            )
            self.scanner_thread.files_found_batch.connect(self._on_files_found_batch)
            self.scanner_thread.scan_progress.connect(self._on_scan_progress)
            self.scanner_thread.scan_finished.connect(self._on_scan_finished)
            self.scanner_thread.scan_error.connect(self._on_scan_error)

        self._scan_btn_style_stop()
        self.progress_bar.setVisible(True)
        self.scan_start_time = time.time()

        self.scanner_thread.start()

    def _stop_scan(self):
        if self.scanner_thread:
            self.scanner_thread.request_stop()
            self.status_label.setText("Stopping scan…")

    def _on_file_found(self, file_info: dict):
        """Legacy single-file handler (kept for compat)."""
        self.all_files.append(file_info)

    def _on_files_found_batch(self, file_list: list):
        """Buffer a batch of files during scan (receives ~100 files per signal, not 1)."""
        self.all_files.extend(file_list)

    def _add_large_file_row(self, file_info: dict, row: int = None):
        """Add one table row for a large file (used when flushing buffer)."""
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)

        # Checkbox
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        chk.setCheckState(Qt.Unchecked)
        self.table.setItem(row, self.COL_CHECK, chk)

        # File name
        name_item = QTableWidgetItem(file_info["name"])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, self.COL_NAME, name_item)

        # Location (directory only)
        dir_path = os.path.dirname(file_info["path"])
        path_item = QTableWidgetItem(dir_path)
        path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
        path_item.setToolTip(file_info["path"])
        self.table.setItem(row, self.COL_PATH, path_item)

        # Size (sortable by raw bytes)
        size_item = SizeTableItem(format_size(file_info["size"]), file_info["size"])
        size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
        size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, self.COL_SIZE, size_item)

        # Modified date (sortable by timestamp) — formatted here, not during scan
        mod_ts = file_info["modified_ts"]
        mod_str = file_info.get("modified") or datetime.fromtimestamp(mod_ts).strftime("%Y-%m-%d %I:%M %p")
        mod_item = SizeTableItem(mod_str, mod_ts)
        mod_item.setFlags(mod_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, self.COL_MODIFIED, mod_item)

        # Last Opened - placeholder until fetcher runs
        opened_item = QTableWidgetItem("⏳ Pending…")
        opened_item.setFlags(opened_item.flags() & ~Qt.ItemIsEditable)
        opened_item.setForeground(QColor("#999"))
        self.table.setItem(row, self.COL_LAST_OPENED, opened_item)

        # v4: Confidence — placeholder until Last Opened is loaded
        conf_item = QTableWidgetItem("⏳ …")
        conf_item.setFlags(conf_item.flags() & ~Qt.ItemIsEditable)
        conf_item.setTextAlignment(Qt.AlignCenter)
        conf_item.setForeground(QColor("#999"))
        self.table.setItem(row, self.COL_CONFIDENCE, conf_item)

    def _on_scan_progress(self, current_dir: str, count: int):
        self._scan_files_scanned = count
        # Throttle UI updates to ~5/sec
        now = time.time()
        if now - self._last_progress_ui_update < 0.2:
            return
        self._last_progress_ui_update = now
        display_dir = current_dir if len(current_dir) <= 80 else "…" + current_dir[-77:]
        elapsed = now - self.scan_start_time
        self.status_label.setText(f"Scanning: {display_dir}  |  {count:,} files found  |  {elapsed:.0f}s elapsed")

    def _on_scan_finished(self, total: int):
        self._remove_scan_placeholder()
        self.table.setSortingEnabled(False)
        count = len(self.all_files)
        self.table.setRowCount(count)
        self._flush_scan_elapsed = time.time() - self.scan_start_time

        # Timer-based incremental flush: populate table in chunks so UI stays responsive
        self._flush_idx = 0
        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_large_files_chunk)
        self._flush_timer.start(0)  # fires on every event loop iteration

    def _flush_large_files_chunk(self):
        """Populate the next chunk of large-file rows, then yield to the event loop."""
        end = min(self._flush_idx + self.FLUSH_CHUNK_SIZE, len(self.all_files))
        self.table.setUpdatesEnabled(False)
        for i in range(self._flush_idx, end):
            self._add_large_file_row(self.all_files[i], row=i)
        self.table.setUpdatesEnabled(True)

        self._flush_idx = end
        filled = self._flush_idx
        total = len(self.all_files)
        self.status_label.setText(f"Loading results… {filled:,} / {total:,}")

        if self._flush_idx >= total:
            self._flush_timer.stop()
            self.progress_bar.setVisible(False)
            self._scan_btn_style_start()
            total_size = sum(f["size"] for f in self.all_files)
            elapsed = self._flush_scan_elapsed
            self.status_label.setText(f"Scan complete — {total} files found in {elapsed:.1f}s")
            self.summary_label.setText(f"Total: {format_size(total_size)}")
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(self.COL_SIZE, Qt.DescendingOrder)
            self._start_fetching_last_opened()

    def _on_scan_error(self, error: str):
        self.status_label.setText(f"Scan error: {error}")

    def _on_sensitive_finding_batch(self, findings: list):
        """Buffer a batch of findings during scan (avoids 10k+ main-thread slot invocations)."""
        for f in findings:
            self._sensitive_findings_buffer.append(dict(f))

    def _process_one_sensitive_finding(self, finding: dict):
        """Aggregate one finding by file and add/update one table row (called when flushing buffer)."""
        filepath = finding["file"]
        key = filepath
        conf_rank = self._CONF_RANK.get(finding["confidence"], 0)
        sample_parts = list(sensitive_mask_value(v, finding["profile"]) for v in finding.get("unique_values", [])[:3])

        if key not in self._sensitive_file_aggregate:
            # New file: create aggregate and add row
            agg = {
                "file": filepath,
                "filename": finding["filename"],
                "size": finding["size"],
                "modified": finding["modified"],
                "profiles": {finding["profile"]},
                "confidence": finding["confidence"],
                "conf_rank": conf_rank,
                "hits": finding["match_count"],
                "samples": sample_parts,
            }
            self._sensitive_file_aggregate[key] = agg
            self.sensitive_findings.append(agg)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._sensitive_path_to_row[key] = row
            dirpath = os.path.dirname(filepath)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            chk.setData(Qt.UserRole, filepath)
            self.table.setItem(row, self.SCOL_CHECK, chk)
            self.table.setItem(row, self.SCOL_CONF, QTableWidgetItem(finding["confidence"]))
            for col, p in enumerate(["HUID", "SSN", "TAX", "EMAIL"], start=self.SCOL_HUID):
                self.table.setItem(row, col, QTableWidgetItem("✓" if p == finding["profile"] else ""))
            self.table.setItem(row, self.SCOL_NAME, QTableWidgetItem(finding["filename"]))
            self.table.setItem(row, self.SCOL_PATH, QTableWidgetItem(dirpath))
            self.table.setItem(row, self.SCOL_HITS, QTableWidgetItem(str(finding["match_count"])))
            size_item = SizeTableItem(format_size(finding["size"]), finding["size"])
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, self.SCOL_SIZE, size_item)
            self.table.setItem(row, self.SCOL_MODIFIED, QTableWidgetItem(finding["modified"]))
            sample_str = "; ".join(sample_parts)
            self.table.setItem(row, self.SCOL_SAMPLE, QTableWidgetItem(sample_str))
        else:
            # Same file, another profile: update aggregate and existing row
            agg = self._sensitive_file_aggregate[key]
            agg["profiles"].add(finding["profile"])
            if conf_rank > agg["conf_rank"]:
                agg["confidence"] = finding["confidence"]
                agg["conf_rank"] = conf_rank
            agg["hits"] += finding["match_count"]
            agg["samples"].extend(sample_parts)
            row = self._sensitive_path_to_row[key]
            self.table.item(row, self.SCOL_CONF).setText(agg["confidence"])
            self.table.item(row, self.SCOL_HUID).setText("✓" if "HUID" in agg["profiles"] else "")
            self.table.item(row, self.SCOL_SSN).setText("✓" if "SSN" in agg["profiles"] else "")
            self.table.item(row, self.SCOL_TAX).setText("✓" if "TAX" in agg["profiles"] else "")
            self.table.item(row, self.SCOL_EMAIL).setText("✓" if "EMAIL" in agg["profiles"] else "")
            self.table.item(row, self.SCOL_HITS).setText(str(agg["hits"]))
            sample_str = "; ".join(agg["samples"][:8])
            if len(agg["samples"]) > 8:
                sample_str += "..."
            self.table.item(row, self.SCOL_SAMPLE).setText(sample_str)

    def _on_sensitive_scan_progress(self, current_dir: str, files_scanned: int, total_findings: int):
        self._scan_files_scanned = files_scanned
        self._scan_findings_count = total_findings
        # Throttle status label updates to ~5/sec so UI stays responsive during long scans
        now = time.time()
        if now - self._last_progress_ui_update < 0.2:
            return
        self._last_progress_ui_update = now
        display_dir = current_dir if len(current_dir) <= 80 else "…" + current_dir[-77:]
        elapsed = now - self.scan_start_time
        self.status_label.setText(
            f"Scanning: {display_dir}  |  {files_scanned:,} files  |  {total_findings} found  |  {elapsed:.0f}s"
        )

    def _on_sensitive_scan_finished(self, total_findings: int):
        self._remove_scan_placeholder()
        self.sensitive_findings.clear()
        self._sensitive_file_aggregate.clear()
        self._sensitive_path_to_row.clear()
        self.table.setSortingEnabled(False)
        self._flush_scan_elapsed = time.time() - self.scan_start_time

        self._flush_idx = 0
        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_sensitive_chunk)
        self._flush_timer.start(0)

    def _flush_sensitive_chunk(self):
        buf = self._sensitive_findings_buffer
        end = min(self._flush_idx + self.FLUSH_CHUNK_SIZE, len(buf))
        self.table.setUpdatesEnabled(False)
        for i in range(self._flush_idx, end):
            self._process_one_sensitive_finding(buf[i])
        self.table.setUpdatesEnabled(True)

        self._flush_idx = end
        total = len(buf)
        self.status_label.setText(f"Loading results… {self._flush_idx:,} / {total:,}")

        if self._flush_idx >= total:
            self._flush_timer.stop()
            self._sensitive_findings_buffer.clear()
            self.progress_bar.setVisible(False)
            self._scan_btn_style_start()
            file_count = len(self.sensitive_findings)
            elapsed = self._flush_scan_elapsed
            self.status_label.setText(f"Sensitive scan complete — {file_count} file(s) with findings in {elapsed:.1f}s")
            self.summary_label.setText(f"{file_count} finding(s)")
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(self.SCOL_CONF, Qt.DescendingOrder)

    def _on_duplicate_group_found(self, group: dict):
        """Buffer during scan; rows are added only when scan finishes (avoids UI freeze)."""
        self.duplicate_groups.append(group)

    def _add_duplicate_group_row(self, group: dict, row: int = None):
        """Add one table row for a duplicate group (used when flushing buffer)."""
        paths = group["paths"]
        size_bytes = group["size"]
        reason = group["reason"]
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)
        # Why duplicate
        reason_item = QTableWidgetItem(reason)
        reason_item.setFlags(reason_item.flags() & ~Qt.ItemIsEditable)
        reason_item.setData(Qt.UserRole, paths)
        self.table.setItem(row, 0, reason_item)
        # Size
        size_item = SizeTableItem(format_size(size_bytes), size_bytes)
        size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
        size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 1, size_item)
        # # Copies
        count_item = QTableWidgetItem(str(len(paths)))
        count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
        count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 2, count_item)
        # Locations: first path + " + N more"; full list in tooltip
        if len(paths) == 1:
            loc_text = paths[0]
        else:
            loc_text = paths[0] + f"  + {len(paths) - 1} more"
        loc_item = QTableWidgetItem(loc_text)
        loc_item.setFlags(loc_item.flags() & ~Qt.ItemIsEditable)
        loc_item.setData(Qt.UserRole, paths)
        loc_item.setToolTip("\n".join(paths))
        self.table.setItem(row, 3, loc_item)

    def _on_duplicate_scan_finished(self, group_count: int):
        self._remove_scan_placeholder()
        self.table.setSortingEnabled(False)
        count = len(self.duplicate_groups)
        self.table.setRowCount(count)
        self._flush_scan_elapsed = time.time() - self.scan_start_time

        self._flush_idx = 0
        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_duplicates_chunk)
        self._flush_timer.start(0)

    def _flush_duplicates_chunk(self):
        end = min(self._flush_idx + self.FLUSH_CHUNK_SIZE, len(self.duplicate_groups))
        self.table.setUpdatesEnabled(False)
        for i in range(self._flush_idx, end):
            self._add_duplicate_group_row(self.duplicate_groups[i], row=i)
        self.table.setUpdatesEnabled(True)

        self._flush_idx = end
        total = len(self.duplicate_groups)
        self.status_label.setText(f"Loading results… {self._flush_idx:,} / {total:,}")

        if self._flush_idx >= total:
            self._flush_timer.stop()
            self.progress_bar.setVisible(False)
            self._scan_btn_style_start()
            total_copies = sum(len(g["paths"]) for g in self.duplicate_groups)
            elapsed = self._flush_scan_elapsed
            self.status_label.setText(
                f"Duplicate scan complete — {total} group(s), {total_copies} files in {elapsed:.1f}s"
            )
            self.summary_label.setText(f"{total} duplicate group(s) — {total_copies} files total")
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(1, Qt.DescendingOrder)

    def _on_string_search_match_found(self, match: dict):
        """Legacy single-match handler (kept for compat)."""
        self.string_search_matches.append(dict(match))

    def _on_string_search_matches_batch(self, matches: list):
        """Buffer a batch of matches during scan (receives ~50 matches per signal, not 1)."""
        self.string_search_matches.extend(matches)

    def _add_string_search_row(self, match: dict, row: int = None):
        """Add one table row for a string search match (used when flushing buffer)."""
        full_path = match.get("full_path")
        if not full_path:
            try:
                full_path = os.path.abspath(os.path.realpath(os.path.join(match["path"], match["file"])))
            except (OSError, TypeError):
                full_path = os.path.join(match.get("path", ""), match.get("file", ""))
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)
        self.table.setItem(row, self.TCOL_FILE, QTableWidgetItem(match["file"]))
        self.table.setItem(row, self.TCOL_PATH, QTableWidgetItem(match["path"]))
        line_item = QTableWidgetItem(str(match["line_num"]))
        line_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, self.TCOL_LINE, line_item)
        self.table.setItem(row, self.TCOL_SNIPPET, QTableWidgetItem(match["snippet"]))
        # Store full absolute path for _get_file_path_for_row and open/reveal
        self.table.item(row, self.TCOL_FILE).setData(Qt.UserRole, full_path)

    def _on_string_search_progress(self, current_dir: str, files_scanned: int, match_count: int):
        self._scan_files_scanned = files_scanned
        self._scan_findings_count = match_count
        now = time.time()
        if now - self._last_progress_ui_update < 0.2:
            return
        self._last_progress_ui_update = now
        display_dir = current_dir if len(current_dir) <= 80 else "…" + current_dir[-77:]
        elapsed = now - self.scan_start_time
        self.status_label.setText(
            f"Scanning: {display_dir}  |  {files_scanned:,} files  |  {match_count} match(es)  |  {elapsed:.0f}s"
        )

    def _on_string_search_finished(self, total_matches: int):
        self._remove_scan_placeholder()
        self.table.setSortingEnabled(False)
        count = len(self.string_search_matches)
        self.table.setRowCount(count)
        self._flush_scan_elapsed = time.time() - self.scan_start_time

        self._flush_idx = 0
        self._flush_timer = QTimer(self)
        self._flush_timer.timeout.connect(self._flush_string_search_chunk)
        self._flush_timer.start(0)

    def _flush_string_search_chunk(self):
        end = min(self._flush_idx + self.FLUSH_CHUNK_SIZE, len(self.string_search_matches))
        self.table.setUpdatesEnabled(False)
        for i in range(self._flush_idx, end):
            self._add_string_search_row(self.string_search_matches[i], row=i)
        self.table.setUpdatesEnabled(True)

        self._flush_idx = end
        total = len(self.string_search_matches)
        self.status_label.setText(f"Loading results… {self._flush_idx:,} / {total:,}")

        if self._flush_idx >= total:
            self._flush_timer.stop()
            elapsed = self._flush_scan_elapsed
        self.progress_bar.setVisible(False)
        self._scan_btn_style_start()
        self.status_label.setText(f"String search complete — {total_matches} match(es) in {elapsed:.1f}s")
        self.summary_label.setText(f"{total_matches} match(es)")
        self.table.setSortingEnabled(True)

    # ── Last Opened fetcher ───────────────────────────────

    def _start_fetching_last_opened(self):
        """Kick off background thread to get kMDItemLastUsedDate for all files."""
        file_paths = []
        for row in range(self.table.rowCount()):
            path_item = self.table.item(row, self.COL_PATH)
            name_item = self.table.item(row, self.COL_NAME)
            if path_item and name_item:
                filepath = os.path.join(path_item.text(), name_item.text())
                file_paths.append((row, filepath))

        if not file_paths:
            return

        self.status_label.setText(
            f"{self.status_label.text()}  |  Fetching 'Last Opened' dates…"
        )

        self.fetcher_thread = LastOpenedFetcher(file_paths)
        self.fetcher_thread.result_ready.connect(self._on_last_opened_ready)
        self.fetcher_thread.fetch_finished.connect(self._on_fetcher_finished)
        self.fetcher_thread.start()

    def _on_last_opened_ready(self, row: int, last_opened: str):
        """Buffer last-opened results and flush in batches to avoid per-cell repaints."""
        if not hasattr(self, '_last_opened_buffer'):
            self._last_opened_buffer = []
        self._last_opened_buffer.append((row, last_opened))
        # Flush every 50 results (or on fetch_finished via _flush_last_opened)
        if len(self._last_opened_buffer) >= 50:
            self._flush_last_opened()

    def _flush_last_opened(self):
        """Apply buffered last-opened results to the table in one batch."""
        buf = getattr(self, '_last_opened_buffer', [])
        if not buf:
            return
        self.table.setUpdatesEnabled(False)
        for row, last_opened in buf:
            if row >= self.table.rowCount():
                continue
            item = self.table.item(row, self.COL_LAST_OPENED)
            if item:
                item.setText(last_opened)
                item.setForeground(QColor("#333") if last_opened not in ("Never / Unknown", "N/A") else QColor("#999"))

            filepath = self._get_file_path_for_row(row)
            size_item = self.table.item(row, self.COL_SIZE)
            size_bytes = size_item._sort_value if isinstance(size_item, SizeTableItem) else 0
            score, label, reason = FileAnalyzer.analyze(filepath, size_bytes, last_opened)

            conf_item = self.table.item(row, self.COL_CONFIDENCE)
            if conf_item:
                conf_item.setText(label)
                conf_item.setToolTip(f"Score: {score}/100\n{reason}")
                if score >= 65:
                    conf_item.setForeground(QColor("#2d9e2d"))
                elif score >= 40:
                    conf_item.setForeground(QColor("#cc8800"))
                else:
                    conf_item.setForeground(QColor("#cc2222"))
        self.table.setUpdatesEnabled(True)
        self._last_opened_buffer.clear()

    def _on_fetcher_finished(self):
        self._flush_last_opened()
        current = self.status_label.text()
        self.status_label.setText(current.replace("  |  Fetching 'Last Opened' dates…", "  |  ✅ Last Opened loaded"))

    # ── Table filtering ───────────────────────────────────

    def _apply_table_filter(self):
        """Filter visible rows by search text, size, last-opened, and confidence (large-files) or by search/size (duplicates) or search/show (sensitive) or search (string search)."""
        search = self.search_input.text().lower().strip()

        if self._scan_mode == "string_search":
            visible_count = 0
            for row in range(self.table.rowCount()):
                file_item = self.table.item(row, self.TCOL_FILE)
                path_item = self.table.item(row, self.TCOL_PATH)
                snippet_item = self.table.item(row, self.TCOL_SNIPPET)
                text_ok = True
                if search:
                    parts = []
                    if file_item:
                        parts.append(file_item.text().lower())
                    if path_item:
                        parts.append(path_item.text().lower())
                    if snippet_item:
                        parts.append(snippet_item.text().lower())
                    text_ok = search in " ".join(parts)
                self.table.setRowHidden(row, not text_ok)
                if text_ok:
                    visible_count += 1
            total = len(self.string_search_matches)
            self.summary_label.setText(f"Showing {visible_count} of {total} match(es)" if total else "")
            return

        if self._scan_mode == "sensitive":
            show_text = self.sensitive_show_filter.currentText()
            visible_count = 0
            for row in range(self.table.rowCount()):
                conf_item = self.table.item(row, self.SCOL_CONF)
                name_item = self.table.item(row, self.SCOL_NAME)
                path_item = self.table.item(row, self.SCOL_PATH)
                huid_item = self.table.item(row, self.SCOL_HUID)
                ssn_item = self.table.item(row, self.SCOL_SSN)
                tax_item = self.table.item(row, self.SCOL_TAX)
                email_item = self.table.item(row, self.SCOL_EMAIL)
                text_ok = True
                if search:
                    text_ok = (
                        (conf_item and search in conf_item.text().lower())
                        or (name_item and search in name_item.text().lower())
                        or (path_item and search in path_item.text().lower())
                        or (huid_item and search in huid_item.text().lower())
                        or (ssn_item and search in ssn_item.text().lower())
                        or (tax_item and search in tax_item.text().lower())
                        or (email_item and search in email_item.text().lower())
                    )
                show_ok = True
                if show_text != "All Results":
                    if show_text == "HIGH Only" and (not conf_item or conf_item.text() != "HIGH"):
                        show_ok = False
                    elif show_text == "MEDIUM Only" and (not conf_item or conf_item.text() != "MEDIUM"):
                        show_ok = False
                    elif show_text == "LOW Only" and (not conf_item or conf_item.text() != "LOW"):
                        show_ok = False
                    elif show_text == "HUID Only" and (not huid_item or huid_item.text() != "✓"):
                        show_ok = False
                    elif show_text == "SSN Only" and (not ssn_item or ssn_item.text() != "✓"):
                        show_ok = False
                    elif show_text == "TAX Only" and (not tax_item or tax_item.text() != "✓"):
                        show_ok = False
                    elif show_text == "EMAIL Only" and (not email_item or email_item.text() != "✓"):
                        show_ok = False
                visible = text_ok and show_ok
                self.table.setRowHidden(row, not visible)
                if visible:
                    visible_count += 1
            self.summary_label.setText(f"Showing {visible_count} of {len(self.sensitive_findings)} finding(s)")
            return

        size_filter_text = self.display_filter.currentText()
        size_thresholds = {
            "All Results": 0, "100 MB+": 100 * 1024 ** 2,
            "250 MB+": 250 * 1024 ** 2, "500 MB+": 500 * 1024 ** 2,
            "1 GB+": 1024 ** 3, "5 GB+": 5 * 1024 ** 3,
        }
        min_size = size_thresholds.get(size_filter_text, 0)

        if self._scan_mode == "duplicates":
            visible_count = 0
            visible_size = 0
            for row in range(self.table.rowCount()):
                reason_item = self.table.item(row, 0)
                size_item = self.table.item(row, 1)
                loc_item = self.table.item(row, 3)
                text_ok = True
                if search and reason_item and loc_item:
                    text_ok = (
                        search in reason_item.text().lower()
                        or search in loc_item.text().lower()
                    )
                size_ok = True
                file_size = 0
                if isinstance(size_item, SizeTableItem):
                    file_size = size_item._sort_value
                    if min_size > 0:
                        size_ok = file_size >= min_size
                visible = text_ok and size_ok
                self.table.setRowHidden(row, not visible)
                if visible:
                    visible_count += 1
                    visible_size += file_size
            total_count = self.table.rowCount()
            if visible_count < total_count:
                self.summary_label.setText(
                    f"Showing {visible_count} of {total_count} groups ({format_size(visible_size)} per file)"
                )
            else:
                self.summary_label.setText(f"{visible_count} duplicate group(s)")
            return

        opened_filter_text = self.opened_filter.currentText()
        confidence_filter_text = self.confidence_filter.currentText()
        opened_thresholds = {
            "Any time": 0, "3+ months": 90, "6+ months": 180,
            "1+ year": 365, "2+ years": 730, "Never opened": -1,
        }
        min_days = opened_thresholds.get(opened_filter_text, 0)

        visible_count = 0
        visible_size = 0

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, self.COL_NAME)
            path_item = self.table.item(row, self.COL_PATH)
            size_item = self.table.item(row, self.COL_SIZE)
            opened_item = self.table.item(row, self.COL_LAST_OPENED)
            conf_item = self.table.item(row, self.COL_CONFIDENCE)

            if not name_item:
                continue

            text_ok = True
            if search:
                name_match = search in name_item.text().lower()
                path_match = search in path_item.text().lower() if path_item else False
                text_ok = name_match or path_match

            size_ok = True
            file_size = 0
            if isinstance(size_item, SizeTableItem):
                file_size = size_item._sort_value
                if min_size > 0:
                    size_ok = file_size >= min_size

            opened_ok = True
            if min_days != 0 and opened_item:
                opened_text = opened_item.text()
                if opened_text in ("⏳ Pending…", "N/A"):
                    opened_ok = True
                elif min_days == -1:
                    opened_ok = (opened_text == "Never / Unknown")
                else:
                    days = FileAnalyzer.parse_last_opened_to_days(opened_text)
                    if days is not None:
                        opened_ok = days >= min_days

            conf_ok = True
            if confidence_filter_text != "All" and conf_item:
                conf_text = conf_item.text()
                if conf_text == "⏳ …":
                    conf_ok = True
                else:
                    conf_ok = confidence_filter_text in conf_text

            visible = text_ok and size_ok and opened_ok and conf_ok
            self.table.setRowHidden(row, not visible)

            if visible:
                visible_count += 1
                visible_size += file_size

        total_count = self.table.rowCount()
        if visible_count < total_count:
            self.summary_label.setText(
                f"Showing {visible_count} of {total_count} files ({format_size(visible_size)})"
            )
        else:
            self.summary_label.setText(f"Total: {visible_count} files ({format_size(visible_size)})")

    # ── Double-click and context menu ───────────────────────

    def _get_duplicate_paths_for_row(self, row: int) -> list:
        """Return list of all paths for a duplicate-group row, or []."""
        if self._scan_mode != "duplicates":
            return []
        item = self.table.item(row, 0)
        if item:
            paths = item.data(Qt.UserRole)
            if paths:
                return list(paths)
        return []

    def _show_all_locations_for_row(self, row: int):
        """Open dialog listing all duplicate locations for this row."""
        paths = self._get_duplicate_paths_for_row(row)
        if not paths:
            return
        dlg = AllLocationsDialog(paths, self)
        dlg.exec_()

    def _on_table_context_menu(self, pos):
        """Right-click menu: Show all locations (duplicates), Reveal in Finder, Open file (string search)."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        menu = QMenu(self)
        if self._scan_mode == "duplicates" and self._get_duplicate_paths_for_row(row):
            menu.addAction("Show all locations", lambda: self._show_all_locations_for_row(row))
        filepath = self._get_file_path_for_row(row)
        if filepath and os.path.exists(filepath):
            menu.addAction("Reveal in Finder" if os.name != "nt" else "Show in Explorer",
                          lambda: self._reveal_in_finder(filepath))
            if self._scan_mode == "string_search":
                menu.addAction("Open file", lambda: self._open_file_default(filepath))
            # "Exclude this directory" — adds parent dir to the exclude list
            dirpath = os.path.dirname(filepath)
            if dirpath:
                short = dirpath.replace(str(Path.home()), "~") if dirpath.startswith(str(Path.home())) else dirpath
                if len(short) > 50:
                    short = "…" + short[-47:]
                menu.addSeparator()
                menu.addAction(f"Exclude folder: {short}", lambda d=dirpath: self._exclude_directory_from_menu(d))
        if menu.actions():
            menu.exec_(self.table.mapToGlobal(pos))

    def _reveal_in_finder(self, filepath: str):
        if not filepath or not str(filepath).strip():
            return
        try:
            filepath = os.path.abspath(os.path.realpath(filepath))
        except (OSError, TypeError):
            return
        if not os.path.exists(filepath):
            return
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(filepath)])
        else:
            subprocess.Popen(["open", "-R", filepath])

    def _open_file_default(self, filepath: str):
        """Open file with the system default application."""
        if not filepath or not str(filepath).strip():
            return
        try:
            filepath = os.path.abspath(os.path.realpath(filepath))
        except (OSError, TypeError):
            return
        if not os.path.exists(filepath):
            return
        try:
            if os.name == "nt":
                os.startfile(filepath)
            else:
                subprocess.Popen(["open", filepath])
        except Exception:
            pass

    def _on_row_double_click(self, row: int, col: int):
        """Double-click: duplicates → show all locations; else reveal in Finder/Explorer."""
        if self._scan_mode == "large" and col == self.COL_CHECK:
            return
        if self._scan_mode == "sensitive" and col == self.SCOL_CHECK:
            return
        if self._scan_mode == "duplicates":
            self._show_all_locations_for_row(row)
            return
        filepath = self._get_file_path_for_row(row)
        if filepath and os.path.exists(filepath):
            self._reveal_in_finder(filepath)

    # ── Selection helpers ─────────────────────────────────

    def _get_checked_rows(self) -> list:
        """Return list of visible, checked row indices."""
        rows = []
        check_col = self.SCOL_CHECK if self._scan_mode == "sensitive" else self.COL_CHECK
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            chk = self.table.item(row, check_col)
            if chk and chk.checkState() == Qt.Checked:
                rows.append(row)
        return rows

    def _get_file_path_for_row(self, row: int) -> str:
        if self._scan_mode == "sensitive":
            chk = self.table.item(row, self.SCOL_CHECK)
            if chk and chk.data(Qt.UserRole):
                return chk.data(Qt.UserRole)
            return ""
        if self._scan_mode == "string_search":
            file_item = self.table.item(row, self.TCOL_FILE)
            if file_item and file_item.data(Qt.UserRole):
                return file_item.data(Qt.UserRole)
            path_item = self.table.item(row, self.TCOL_PATH)
            name_item = self.table.item(row, self.TCOL_FILE)
            if path_item and name_item:
                return os.path.join(path_item.text(), name_item.text())
            return ""
        if self._scan_mode == "duplicates":
            item = self.table.item(row, 0)
            if item:
                paths = item.data(Qt.UserRole)
                if paths:
                    return paths[0]
            return ""
        path_item = self.table.item(row, self.COL_PATH)
        name_item = self.table.item(row, self.COL_NAME)
        if path_item and name_item:
            return os.path.join(path_item.text(), name_item.text())
        return ""

    def _select_all(self):
        check_col = self.SCOL_CHECK if self._scan_mode == "sensitive" else self.COL_CHECK
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                chk = self.table.item(row, check_col)
                if chk:
                    chk.setCheckState(Qt.Checked)
        self.table.blockSignals(False)
        self._update_selection_label()

    def _deselect_all(self):
        check_col = self.SCOL_CHECK if self._scan_mode == "sensitive" else self.COL_CHECK
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            chk = self.table.item(row, check_col)
            if chk:
                chk.setCheckState(Qt.Unchecked)
        self.table.blockSignals(False)
        self._update_selection_label()

    def _invert_selection(self):
        check_col = self.SCOL_CHECK if self._scan_mode == "sensitive" else self.COL_CHECK
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                chk = self.table.item(row, check_col)
                if chk:
                    new_state = Qt.Unchecked if chk.checkState() == Qt.Checked else Qt.Checked
                    chk.setCheckState(new_state)
        self.table.blockSignals(False)
        self._update_selection_label()

    def _on_cell_changed(self, row, col):
        check_col = self.SCOL_CHECK if self._scan_mode == "sensitive" else self.COL_CHECK
        if col == check_col:
            self._update_selection_label()

    def _update_selection_label(self):
        checked = self._get_checked_rows()
        total_size = 0
        if self._scan_mode == "sensitive":
            for row in checked:
                size_item = self.table.item(row, self.SCOL_SIZE)
                if isinstance(size_item, SizeTableItem):
                    total_size += size_item._sort_value
        else:
            for row in checked:
                size_item = self.table.item(row, self.COL_SIZE)
                if isinstance(size_item, SizeTableItem):
                    total_size += size_item._sort_value
        self.selection_label.setText(f"{len(checked)} files selected ({format_size(total_size)})")

    # ── Actions ───────────────────────────────────────────

    def _delete_selected(self):
        checked = self._get_checked_rows()
        if not checked:
            QMessageBox.information(self, "No Selection", "Please check one or more files first.")
            return

        if self._scan_mode == "sensitive":
            if not sensitive_secure_delete_file:
                QMessageBox.warning(self, "Error", "Secure delete is not available.")
                return
            reply = QMessageBox.warning(
                self, "Secure Delete",
                f"Permanently overwrite and delete {len(checked)} file(s)?\n\nThis cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            deleted_rows = []
            errors = []
            for row in checked:
                filepath = self._get_file_path_for_row(row)
                if filepath and os.path.exists(filepath):
                    try:
                        if sensitive_secure_delete_file(filepath, passes=3):
                            deleted_rows.append(row)
                        else:
                            errors.append(os.path.basename(filepath))
                    except Exception as e:
                        errors.append(f"{os.path.basename(filepath)}: {e}")
            self.table.setSortingEnabled(False)
            for row in sorted(deleted_rows, reverse=True):
                self.table.removeRow(row)
            self.table.setSortingEnabled(True)
            self._update_selection_label()
            msg = f"Securely deleted {len(deleted_rows)} file(s)."
            if errors:
                msg += f"\n\n{len(errors)} error(s):\n" + "\n".join(errors[:5])
            QMessageBox.information(self, "Done", msg)
            return

        total_size = 0
        for row in checked:
            size_item = self.table.item(row, self.COL_SIZE)
            if isinstance(size_item, SizeTableItem):
                total_size += size_item._sort_value

        reply = QMessageBox.warning(
            self, "Move to Trash",
            f"Move {len(checked)} file(s) ({format_size(total_size)}) to Trash?\n\n"
            "You can recover them from the Trash if needed.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        deleted_rows = []
        errors = []
        for row in checked:
            filepath = self._get_file_path_for_row(row)
            if filepath and os.path.exists(filepath):
                try:
                    if os.name == "nt":
                        os.unlink(filepath)
                    else:
                        subprocess.run(
                            ["osascript", "-e",
                             f'tell application "Finder" to delete POSIX file "{filepath}"'],
                            capture_output=True, timeout=10
                        )
                    deleted_rows.append(row)
                except Exception as e:
                    errors.append(f"{os.path.basename(filepath)}: {e}")

        self.table.setSortingEnabled(False)
        for row in sorted(deleted_rows, reverse=True):
            self.table.removeRow(row)
        self.table.setSortingEnabled(True)
        self._update_selection_label()
        msg = f"Moved {len(deleted_rows)} file(s) to Trash."
        if errors:
            msg += f"\n\n{len(errors)} error(s):\n" + "\n".join(errors[:5])
        QMessageBox.information(self, "Done", msg)

    # ── Update checker ────────────────────────────────────

    def _auto_check_for_updates(self):
        self._run_update_check(manual=False)

    def _manual_check_for_updates(self):
        self._run_update_check(manual=True)

    def _run_update_check(self, manual: bool = False):
        from update_checker import UpdateCheckerThread
        self._update_check_manual = manual
        self._update_thread = UpdateCheckerThread(self._app_version, parent=self)
        self._update_thread.update_available.connect(self._on_update_available)
        self._update_thread.no_update.connect(self._on_no_update)
        self._update_thread.check_failed.connect(self._on_update_check_failed)
        self._update_thread.start()

    def _on_update_available(self, version: str, url: str, changelog: str, dmg_url: str):
        self._update_release_url = url
        self._update_dmg_url = dmg_url
        self._update_version = version
        self._update_banner_label.setText(f"  Update available: v{version}")
        self._update_banner.setVisible(True)
        if self._update_check_manual:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Update Available")
            dlg.setIcon(QMessageBox.Information)
            dlg.setText(f"Version {version} is available.\n\n{changelog[:500]}")
            if dmg_url:
                install_btn = dlg.addButton("Install Update", QMessageBox.AcceptRole)
            else:
                install_btn = None
            dlg.addButton("View Release", QMessageBox.ActionRole)
            dlg.addButton(QMessageBox.Close)
            dlg.exec_()
            clicked = dlg.clickedButton()
            if clicked == install_btn:
                self._start_update_download()
            elif clicked and clicked.text() == "View Release":
                self._open_update_page()

    def _on_no_update(self):
        if self._update_check_manual:
            QMessageBox.information(
                self, "No Updates",
                f"You are running the latest version (v{self._app_version})."
            )

    def _on_update_check_failed(self, error: str):
        if self._update_check_manual:
            QMessageBox.warning(
                self, "Update Check Failed",
                f"Could not check for updates.\n\n{error}"
            )

    def _open_update_page(self):
        import webbrowser
        if self._update_release_url:
            webbrowser.open(self._update_release_url)

    def _start_update_download(self):
        """Download the DMG and open it for installation."""
        from update_checker import UpdateDownloadThread
        dmg_url = getattr(self, '_update_dmg_url', '')
        if not dmg_url:
            self._open_update_page()
            return
        self._download_thread = UpdateDownloadThread(dmg_url, parent=self)
        self._download_thread.progress.connect(self._on_download_progress)
        self._download_thread.download_finished.connect(self._on_download_finished)
        self._download_thread.download_failed.connect(self._on_download_failed)
        self._download_thread.start()
        # Show progress in the banner
        self._update_banner_label.setText("  Downloading update…")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # indeterminate until we get Content-Length

    def _on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(downloaded)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self._update_banner_label.setText(f"  Downloading update… {mb_down:.1f} / {mb_total:.1f} MB")
        else:
            mb_down = downloaded / (1024 * 1024)
            self._update_banner_label.setText(f"  Downloading update… {mb_down:.1f} MB")

    def _on_download_finished(self, dmg_path: str):
        import subprocess
        self.progress_bar.setVisible(False)
        self._update_banner_label.setText("  Update downloaded — installing…")

        # Determine where the running .app lives
        app_bundle = self._get_running_app_path()
        if not app_bundle:
            # Fallback: open the DMG for manual drag-install
            subprocess.Popen(["open", dmg_path])
            QMessageBox.information(
                self, "Update Ready",
                f"The update (v{self._update_version}) has been downloaded.\n\n"
                "Drag 'my.File Tool' to Applications to install."
            )
            return

        # Confirm with user
        reply = QMessageBox.question(
            self, "Install Update",
            f"Ready to update to v{self._update_version}.\n\n"
            "The app will close briefly and relaunch on the new version.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            self._update_banner_label.setText(
                f"  v{self._update_version} downloaded — click Install Update when ready"
            )
            return

        self._perform_in_place_update(dmg_path, app_bundle)

    def _get_running_app_path(self):
        """Return the path to the running .app bundle, or None if running from source."""
        # In a py2app bundle, sys.executable is inside Contents/MacOS/
        exe = os.path.abspath(sys.executable)
        # Walk up to find the .app bundle
        path = exe
        for _ in range(5):
            if path.endswith(".app"):
                return path
            path = os.path.dirname(path)
        return None

    def _perform_in_place_update(self, dmg_path: str, app_bundle: str):
        """Mount DMG, write updater script, quit, let script swap the .app and relaunch."""
        import subprocess
        import tempfile

        app_name = os.path.basename(app_bundle)  # "my.File Tool.app"
        app_dir = os.path.dirname(app_bundle)     # "/Applications"
        pid = os.getpid()

        # Mount the DMG silently (no Finder window)
        try:
            result = subprocess.run(
                ["hdiutil", "attach", "-nobrowse", "-quiet", "-mountpoint", "/tmp/myh_update_mount", dmg_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            mount_point = "/tmp/myh_update_mount"
        except Exception as e:
            QMessageBox.warning(self, "Update Failed", f"Could not mount update DMG:\n{e}")
            return

        new_app = os.path.join(mount_point, app_name)
        if not os.path.isdir(new_app):
            QMessageBox.warning(self, "Update Failed", f"App not found in DMG at:\n{new_app}")
            subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], capture_output=True)
            return

        # Write the updater script
        updater_script = tempfile.mktemp(suffix=".sh", prefix="myh_updater_")
        script_content = f"""#!/bin/bash
# my.h File Finder in-place updater
# Wait for the old process to exit
while kill -0 {pid} 2>/dev/null; do sleep 0.3; done

# Replace the .app bundle
rm -rf "{app_bundle}"
cp -R "{new_app}" "{app_dir}/"

# Unmount and clean up
hdiutil detach "{mount_point}" -quiet 2>/dev/null
rm -f "{dmg_path}"

# Relaunch
open "{app_bundle}"

# Self-destruct
rm -f "$0"
"""
        with open(updater_script, "w") as f:
            f.write(script_content)
        os.chmod(updater_script, 0o755)

        # Launch the updater and quit
        subprocess.Popen(["/bin/bash", updater_script])
        self._update_banner_label.setText("  Updating… app will relaunch shortly")
        QApplication.processEvents()
        QApplication.instance().quit()

    def _on_download_failed(self, error: str):
        self.progress_bar.setVisible(False)
        self._update_banner_label.setText(f"  Download failed — click View Release to download manually")
        if self._update_check_manual:
            QMessageBox.warning(
                self, "Download Failed",
                f"Could not download the update.\n\n{error}\n\nYou can download it manually from the release page."
            )

    # ── Bug reporting ─────────────────────────────────────

    def _report_bug(self, error_text=None):
        """Open a GitHub Issue with pre-filled system info."""
        import webbrowser
        import urllib.parse

        mac_ver = platform.mac_ver()[0] or "unknown"
        mode_names = {
            "large_files": "Large Files",
            "duplicates": "Duplicates",
            "sensitive": "Sensitive Data",
            "string_search": "String Search",
        }
        current_mode = mode_names.get(self._scan_mode, self._scan_mode)

        body_lines = [
            "## Bug Report — my.h File Finder",
            "",
            f"**App Version:** {self._app_version}",
            f"**macOS:** {mac_ver}",
            f"**Scan Mode:** {current_mode}",
            "",
            "### What happened?",
            "<!-- Describe what went wrong -->",
            "",
            "",
            "### Steps to reproduce",
            "1. ",
            "2. ",
            "3. ",
            "",
        ]
        if error_text:
            body_lines += [
                "### Error details",
                "```",
                error_text[:2000],  # URL length limit safety
                "```",
                "",
            ]

        body = "\n".join(body_lines)
        title = "Bug: "
        params = urllib.parse.urlencode({"title": title, "body": body})
        url = f"https://github.com/madore9/myh_file_finder/issues/new?{params}"
        webbrowser.open(url)

    def _install_exception_handler(self):
        """Install a global exception hook that shows a dialog with a Report button."""
        import traceback as tb_mod

        original_hook = sys.excepthook

        def handler(exc_type, exc_value, exc_tb):
            # Format the traceback
            tb_str = "".join(tb_mod.format_exception(exc_type, exc_value, exc_tb))

            # Show dialog on the main thread
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Unexpected Error")
            dlg.setIcon(QMessageBox.Critical)
            dlg.setText("An unexpected error occurred.")
            dlg.setDetailedText(tb_str)
            report_btn = dlg.addButton("Report This Bug", QMessageBox.ActionRole)
            dlg.addButton(QMessageBox.Close)
            dlg.exec_()

            if dlg.clickedButton() == report_btn:
                self._report_bug(error_text=tb_str)

            # Call the original hook too (for console output)
            original_hook(exc_type, exc_value, exc_tb)

        sys.excepthook = handler

    # ── Cleanup ───────────────────────────────────────────

    def closeEvent(self, event):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.request_stop()
            self.scanner_thread.wait(3000)
        if self.fetcher_thread and self.fetcher_thread.isRunning():
            self.fetcher_thread.request_stop()
            self.fetcher_thread.wait(3000)
        if self._update_thread and self._update_thread.isRunning():
            self._update_thread.wait(2000)
        event.accept()


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(load_app_icon())

    # macOS dark mode compatibility
    if hasattr(app, "styleHints"):
        app.styleHints().setShowShortcutsInContextMenus(True)

    window = MyhFileFinder()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
