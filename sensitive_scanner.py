#!/usr/bin/env python3
"""
Sensitive data scan engine for my.h File Finder.
Extracted from SensitiveDataScanner GUI — profiles, scan_file, secure_delete.
No GUI dependencies; used by the my.h File Finder PyQt5 app.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------
import platform
PLATFORM = platform.system()
IS_MAC = PLATFORM == 'Darwin'
IS_WINDOWS = PLATFORM == 'Windows'
HOME = Path.home()

# ---------------------------------------------------------------------------
# Scan Profiles (HUID, SSN, TAX, EMAIL)
# ---------------------------------------------------------------------------
PROFILES = {
    'HUID': {
        'name': 'Harvard ID (HUID)',
        'risk': 'FERPA / Student Data',
        'patterns': [
            ('HUID', re.compile(r'(?<![0-9A-Za-z])[1-9]\d{7}(?![0-9A-Za-z])'), False),
        ],
        'context_keywords': [
            'huid', 'harvard', 'student', 'emplid', 'person_id', 'campus',
            'enrollment', 'registrar', 'advising', 'financial aid', 'transcript',
            'my.harvard', 'peoplesoft', 'grade', 'gpa', 'academic',
        ],
        'filename_keywords': [
            'student', 'roster', 'grade', 'enrollment', 'huid', 'extract',
            'report', 'export', 'advising', 'finaid', 'transcript', 'admit',
        ],
    },
    'SSN': {
        'name': 'Social Security Number',
        'risk': 'PII / Identity',
        'patterns': [
            ('SSN (dashed)', re.compile(r'(?<![0-9A-Za-z])(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?![0-9A-Za-z])'), False),
            ('SSN (spaces)', re.compile(r'(?<![0-9A-Za-z])(?!000|666|9\d\d)\d{3}\s(?!00)\d{2}\s(?!0000)\d{4}(?![0-9A-Za-z])'), False),
            ('SSN (plain)', re.compile(r'(?<![0-9A-Za-z])(?!000|666|9\d\d)\d{3}(?!00)\d{2}(?!0000)\d{4}(?![0-9A-Za-z])'), True),
        ],
        'context_keywords': [
            'ssn', 'social security', 'tax id', 'tin', 'taxpayer',
            'w-2', 'w2', '1099', '1040', 'i-9', 'w-4',
            'wage', 'withholding', 'dependent', 'filing',
        ],
        'filename_keywords': [
            'ssn', 'social', 'tax', 'w2', 'w-2', '1099', '1040',
            'payroll', 'wage', 'earning',
        ],
    },
    'TAX': {
        'name': 'Tax Documents',
        'risk': 'Financial / Tax',
        'patterns': [
            ('SSN in tax', re.compile(r'(?<![0-9A-Za-z])(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?![0-9A-Za-z])'), False),
            ('EIN', re.compile(r'(?<!\d)\d{2}-\d{7}(?!\d)'), False),
        ],
        'context_keywords': [
            'w-2', 'w2', '1099', '1040', '1098', '1095',
            'wages', 'salary', 'compensation', 'gross income',
            'withholding', 'federal tax', 'tax return', 'refund',
            'turbotax', 'h&r block', '1099-misc', '1099-nec',
        ],
        'filename_keywords': [
            'tax', 'w2', 'w-2', '1099', '1040', '1098', 'return',
            'irs', 'payroll', 'paycheck', 'paystub', 'earning',
        ],
    },
    'EMAIL': {
        'name': 'Harvard Email Addresses',
        'risk': 'Directory / PII',
        'patterns': [
            ('Harvard Email', re.compile(
                r'[a-zA-Z0-9._%+\-]+@(?:[a-zA-Z0-9\-]+\.)*harvard\.edu\b',
                re.IGNORECASE
            ), False),
        ],
        'context_keywords': [
            'harvard', 'student', 'faculty', 'staff', 'professor',
            'email', 'contact', 'directory', 'roster', 'list',
            'recipient', 'cc', 'bcc', 'from', 'to',
        ],
        'filename_keywords': [
            'email', 'contact', 'directory', 'roster', 'list',
            'student', 'faculty', 'staff', 'member', 'address',
            'mailing', 'distribution', 'export', 'dump',
        ],
    },
}

SKIP_DIRS = {
    '.git', '.svn', 'node_modules', '__pycache__', '.venv', 'venv',
    '.Trash', '.Spotlight-V100', '.fseventsd', '.TemporaryItems',
    'Photos Library.photoslibrary', 'Music', 'Movies', 'Snagit',
    '$RECYCLE.BIN', 'System Volume Information', 'ProgramData',
    'Recovery', 'PerfLogs',
    '.local', '.cache', '.npm', '.cargo', '.rustup', 'Library',
    'Caches',  # ~/Library/Caches and similar
}

SKIP_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.lib', '.sys',
    '.zip', '.gz', '.tar', '.bz2', '.7z', '.rar', '.xz', '.cab', '.msi',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.heic', '.heif', '.tiff', '.raw', '.cr2', '.nef',
    '.snagx',
    '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.wav', '.flac', '.aac',
    '.m4a', '.m4v', '.wmv', '.wma',
    '.woff', '.woff2', '.ttf', '.otf', '.eot',
    '.iso', '.dmg', '.img', '.vmdk', '.vhd', '.vhdx',
    '.pyc', '.pyo', '.class', '.jar', '.war',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
    '.ds_store',
}

SKIP_ROOT_MAC = {'/System', '/Library', '/private', '/usr', '/bin', '/sbin', '/var', '/dev', '/etc', '/opt', '/tmp', '/cores', '/nix'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB — files larger than this are almost never text with sensitive data

EXCLUDES_FILE = Path.home() / '.sensitive_scanner_excludes.json'


def load_excluded_dirs():
    try:
        if EXCLUDES_FILE.exists():
            data = json.loads(EXCLUDES_FILE.read_text())
            return [str(Path(p).expanduser().resolve()) for p in data.get('excluded_dirs', [])]
    except Exception:
        pass
    return []


def save_excluded_dirs(paths):
    try:
        EXCLUDES_FILE.write_text(json.dumps({'excluded_dirs': list(paths)}, indent=2))
    except Exception:
        pass


def should_skip_dir(dirname, full_path='', excluded_dirs=None, include_hidden=False):
    if dirname in SKIP_DIRS:
        return True
    if not include_hidden and dirname.startswith('.'):
        return True
    if IS_MAC and full_path in SKIP_ROOT_MAC:
        return True
    if IS_WINDOWS:
        lp = os.path.normpath(full_path).lower().replace('/', os.sep)
        if any(lp.startswith(p) for p in [
            'c:\\windows', 'c:\\program files', 'c:\\program files (x86)',
            'c:\\programdata', 'c:\\recovery', 'c:\\$',
        ]):
            return True
        if dirname.startswith('$'):
            return True
    if excluded_dirs:
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


def compute_confidence(profile_key, filename_lower, content_lower, match_count, ext):
    profile = PROFILES[profile_key]
    score = 0
    for kw in profile.get('filename_keywords', []):
        if kw in filename_lower:
            score += 3
    ctx_prefix = content_lower[:5000]
    ctx_hits = sum(1 for kw in profile.get('context_keywords', []) if kw in ctx_prefix)
    if ctx_hits >= 5:
        score += 5
    elif ctx_hits >= 2:
        score += 3
    elif ctx_hits >= 1:
        score += 1
    if match_count >= 10:
        score += 3
    elif match_count >= 3:
        score += 2
    elif match_count >= 1:
        score += 1
    if ext in ('.csv', '.tsv', '.xlsx', '.xls') and match_count >= 5:
        score += 4
    if score >= 6:
        return 'HIGH'
    if score >= 3:
        return 'MEDIUM'
    return 'LOW'


def mask_value(value, profile_key):
    if profile_key == 'SSN':
        if '-' in value and len(value) == 11:
            return f'***-**-{value[-4:]}'
        if len(value) == 9:
            return f'*****{value[-4:]}'
    elif profile_key == 'HUID':
        if len(value) == 8:
            return f'{value[:2]}****{value[-2:]}'
    elif profile_key == 'TAX':
        if len(value) == 10 and value[2] == '-':
            return f'{value[:2]}-*****{value[-2:]}'
        if '-' in value and len(value) == 11:
            return f'***-**-{value[-4:]}'
    elif profile_key == 'EMAIL':
        if '@' in value:
            local, domain = value.split('@', 1)
            if len(local) > 3:
                masked_local = local[:2] + '****'
            else:
                masked_local = local[0] + '****'
            return f'{masked_local}@{domain}'
    return '****'


def scan_file(filepath, active_profiles):
    """Scan a single file. Returns list of result dicts (one per matching profile)."""
    results = []
    try:
        # Single read with errors='replace' — avoids double-read with encoding fallback
        content = Path(filepath).read_text(encoding='utf-8', errors='replace')
        if not content:
            return results

        file_stat = os.stat(filepath)
        fname = os.path.basename(filepath)
        ext = os.path.splitext(filepath)[1].lower()
        fname_lower = fname.lower()
        # Lowercase only the prefix needed for context keyword matching
        content_lower_prefix = content[:5000].lower()

        for pkey in active_profiles:
            if pkey not in PROFILES:
                continue
            profile = PROFILES[pkey]
            all_matches = []
            for pat_name, regex, requires_ctx in profile['patterns']:
                if requires_ctx:
                    # Early exit: check context keywords before running regex on full content
                    if not any(kw in content_lower_prefix for kw in profile.get('context_keywords', [])):
                        continue
                matches = regex.findall(content)
                if not matches:
                    continue
                for m in matches:
                    val = m if isinstance(m, str) else m
                    if pkey == 'HUID' and len(val) == 8 and len(set(val)) == 1:
                        continue
                    all_matches.append(val)
            if not all_matches:
                continue

            unique_vals = list(set(all_matches))[:10]
            confidence = compute_confidence(pkey, fname_lower, content_lower_prefix, len(all_matches), ext)
            results.append({
                'file': filepath,
                'filename': fname,
                'ext': ext,
                'size': file_stat.st_size,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'profile': pkey,
                'confidence': confidence,
                'match_count': len(all_matches),
                'unique_values': unique_vals,
            })
    except (PermissionError, OSError):
        pass
    return results


def secure_delete_file(filepath, passes=3):
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            os.unlink(filepath)
            return True
        for p in range(passes):
            with open(filepath, 'r+b') as f:
                if p % 3 == 0:
                    pattern = b'\x00'
                elif p % 3 == 1:
                    pattern = b'\xFF'
                else:
                    pattern = None
                written = 0
                while written < size:
                    chunk = min(65536, size - written)
                    f.write(os.urandom(chunk) if pattern is None else pattern * chunk)
                    written += chunk
                f.flush()
                os.fsync(f.fileno())
        rand = Path(filepath).parent / f"_DEL_{os.urandom(8).hex()}"
        os.rename(filepath, rand)
        os.unlink(rand)
        return True
    except Exception:
        try:
            os.unlink(filepath)
            return True
        except Exception:
            return False
