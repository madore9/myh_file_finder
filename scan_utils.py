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
