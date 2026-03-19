#!/usr/bin/env python3
"""
Shared scanning utilities for my.File Tool.

Provides:
  - Unified directory-skip logic (used by all scanner threads)
  - fast_scandir(): an os.scandir-based walk that preserves DirEntry stat cache,
    eliminating redundant stat() / lstat() syscalls.  On a typical macOS disk
    this saves ~100K syscalls compared to os.walk() + os.stat().
"""

import os
import platform
import stat as stat_mod

IS_MAC = platform.system() == "Darwin"

# ─────────────────────────────────────────────────────────────
# Directories to always skip (by basename)
# ─────────────────────────────────────────────────────────────

SKIP_DIR_NAMES = {
    # Version control
    ".git", ".svn", ".hg",
    # Package managers / build caches
    "node_modules", "__pycache__", ".venv", "venv",
    ".gradle", ".m2", ".cargo", ".rustup",
    "DerivedData",  # Xcode build cache (can be 50-100GB)
    # macOS system/index directories
    ".Spotlight-V100", ".fseventsd", ".DocumentRevisions-V100",
    ".Trashes", ".TemporaryItems", ".MobileSync",
    # Time Machine
    "Backups.backupdb", ".tmbackup",
    # Cloud sync caches
    ".dropbox", ".dropbox.cache",
    # macOS app data that's huge and uninteresting for scanning
    "Photos Library.photoslibrary",
    "Saved Application State",
    # Trash
    ".Trash",
    # Other large caches
    "Caches",
    ".cache", ".npm", ".local",
}

# Suffixes that mark macOS package directories (treated as opaque bundles)
# These contain thousands of internal framework/resource files that are
# never user data.
SKIP_DIR_SUFFIXES = (
    ".app", ".framework", ".plugin", ".kext",
    ".bundle", ".xpc", ".appex", ".qlgenerator",
)

# Full paths to skip when scanning from root on macOS
# These contain OS frameworks, binaries, and system data — never user-relevant
SKIP_ROOT_PATHS_MAC = {
    "/System",
    "/Library",
    "/bin",
    "/sbin",
    "/usr",
    "/dev",
    "/etc",
    "/opt",
    "/private",
    "/tmp",
    "/var",
    "/cores",
    "/nix",
}

# Volume paths to skip (Time Machine mounts, etc.)
SKIP_VOLUME_PREFIXES_MAC = (
    "/Volumes/Time Machine Backups",
    "/Volumes/com.apple.TimeMachine",
)

# ~/Library subdirectories containing app-internal data (not user files).
# Used by "Skip app & system data" checkbox. These produce massive false
# positives in sensitive scans (Firefox profiles, Chrome data, Mail, etc.)
def get_app_system_skip_dirs():
    """Return a set of absolute paths to skip when 'Skip app & system data' is enabled."""
    home = os.path.expanduser("~")
    lib = os.path.join(home, "Library")
    return {
        # Browser data (Firefox, Chrome, Safari, Edge, Brave, Arc)
        os.path.join(lib, "Application Support", "Firefox"),
        os.path.join(lib, "Application Support", "Google"),
        os.path.join(lib, "Application Support", "BraveSoftware"),
        os.path.join(lib, "Application Support", "Arc"),
        os.path.join(lib, "Application Support", "Microsoft Edge"),
        os.path.join(lib, "Safari"),
        os.path.join(lib, "WebKit"),
        os.path.join(lib, "Cookies"),
        # Communication apps
        os.path.join(lib, "Application Support", "Slack"),
        os.path.join(lib, "Application Support", "zoom.us"),
        os.path.join(lib, "Application Support", "Microsoft", "Teams"),
        os.path.join(lib, "Messages"),
        os.path.join(lib, "Mail"),
        # App internals
        os.path.join(lib, "Containers"),
        os.path.join(lib, "Group Containers"),
        os.path.join(lib, "Saved Application State"),
        os.path.join(lib, "Logs"),
        os.path.join(lib, "Preferences"),
        os.path.join(lib, "Accounts"),
        os.path.join(lib, "Keychains"),
        os.path.join(lib, "Metadata"),
        os.path.join(lib, "HTTPStorages"),
        # Development tools
        os.path.join(lib, "Developer"),
        os.path.join(lib, "Application Support", "Code"),  # VS Code
        os.path.join(lib, "Application Support", "Cursor"),
        os.path.join(lib, "Application Support", "JetBrains"),
        # Cloud sync internals
        os.path.join(lib, "Application Support", "CloudDocs"),
        os.path.join(lib, "Mobile Documents"),  # iCloud Drive internals
        os.path.join(lib, "Application Support", "iCloud"),
        # Apple app data
        os.path.join(lib, "Application Support", "AddressBook"),
        os.path.join(lib, "Application Support", "CallHistoryDB"),
        os.path.join(lib, "Calendars"),
        os.path.join(lib, "HomeKit"),
        os.path.join(lib, "Suggestions"),
        os.path.join(lib, "IdentityServices"),
        os.path.join(lib, "Assistant"),  # Siri
        os.path.join(lib, "Sharing"),
        # More apps
        os.path.join(lib, "Application Support", "Spotify"),
        os.path.join(lib, "Application Support", "Discord"),
        os.path.join(lib, "Application Support", "1Password"),
        os.path.join(lib, "Application Support", "com.apple.sharedfilelist"),
        os.path.join(lib, "Application Support", "CrashReporter"),
        os.path.join(lib, "Application Support", "Adobe"),
        os.path.join(lib, "Application Support", "Dropbox"),
        os.path.join(lib, "Application Support", "OneDrive"),
        os.path.join(lib, "Application Support", "Box"),
        # System
        os.path.join(lib, "Caches"),
        os.path.join(lib, "LaunchAgents"),
        os.path.join(lib, "Fonts"),
        os.path.join(lib, "ColorSync"),
        os.path.join(lib, "Input Methods"),
        os.path.join(lib, "Spelling"),
        os.path.join(lib, "Sounds"),
        os.path.join(lib, "Screen Savers"),
        # Other common app/dev data dirs in home
        os.path.join(home, ".docker"),
        os.path.join(home, ".npm"),
        os.path.join(home, ".local"),
        os.path.join(home, ".cache"),
        os.path.join(home, ".config"),
        os.path.join(home, ".ssh"),
        os.path.join(home, ".gnupg"),
        os.path.join(home, ".ollama"),
        os.path.join(home, ".rustup"),
        os.path.join(home, ".cargo"),
        os.path.join(home, ".gradle"),
        os.path.join(home, ".m2"),
        os.path.join(home, ".bun"),
        os.path.join(home, ".pyenv"),
        os.path.join(home, ".rbenv"),
        os.path.join(home, ".nvm"),
    }


def should_skip_dir(
    dirname: str,
    full_path: str = "",
    include_hidden: bool = False,
    excluded_dirs: set = None,
) -> bool:
    """Unified skip-directory check used by all scanners.

    Args:
        dirname: The directory basename (e.g., '.git')
        full_path: The full absolute path to the directory
        include_hidden: If False, skip all dot-directories
        excluded_dirs: Optional set of absolute paths to exclude
    """
    # Always skip known problematic directories
    if dirname in SKIP_DIR_NAMES:
        return True

    # Skip hidden directories unless explicitly requested
    if not include_hidden and dirname.startswith("."):
        return True

    # Skip macOS package bundles (.app, .framework, etc.)
    if IS_MAC:
        dn_lower = dirname.lower()
        for suffix in SKIP_DIR_SUFFIXES:
            if dn_lower.endswith(suffix):
                return True

    # macOS root-level system paths
    if IS_MAC and full_path:
        if full_path in SKIP_ROOT_PATHS_MAC:
            return True
        for prefix in SKIP_VOLUME_PREFIXES_MAC:
            if full_path.startswith(prefix):
                return True

    # User-configured excluded directories (only resolves realpath when
    # the caller actually provides excluded_dirs — avoids the syscall
    # on the vast majority of calls)
    if excluded_dirs and full_path:
        try:
            normalized = os.path.realpath(full_path)
            if normalized in excluded_dirs:
                return True
            for ex in excluded_dirs:
                if normalized.startswith(ex + os.sep):
                    return True
        except OSError:
            pass

    return False


# ─────────────────────────────────────────────────────────────
# High-performance scandir walk
# ─────────────────────────────────────────────────────────────

def fast_scandir(top, include_hidden=False, excluded_dirs=None):
    """Walk a directory tree using os.scandir(), preserving DirEntry objects.

    Unlike os.walk(), this yields DirEntry objects for files so that callers
    can use ``entry.stat()`` which is backed by the readdir cache on most
    platforms — avoiding an extra stat() syscall per file.

    Yields:
        (dirpath: str, dir_entries: list[DirEntry], file_entries: list[DirEntry])

    Performance vs os.walk() + os.stat():
        - Saves 1-2 syscalls per file (lstat + stat → cached DirEntry.stat)
        - Saves 1 syscall per directory (no os.path.islink)
        - On 50K files: ~100-150K fewer syscalls
    """
    try:
        scandir_it = os.scandir(top)
    except (PermissionError, OSError):
        return

    dirs = []
    files = []
    try:
        for entry in scandir_it:
            try:
                name = entry.name
                if entry.is_dir(follow_symlinks=False):
                    if not should_skip_dir(name, entry.path,
                                           include_hidden=include_hidden,
                                           excluded_dirs=excluded_dirs):
                        dirs.append(entry)
                elif entry.is_file(follow_symlinks=False):
                    if include_hidden or not name.startswith("."):
                        files.append(entry)
            except OSError:
                continue
    finally:
        scandir_it.close()

    yield top, dirs, files

    for d in dirs:
        yield from fast_scandir(d.path,
                                include_hidden=include_hidden,
                                excluded_dirs=excluded_dirs)
