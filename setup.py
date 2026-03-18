"""
setup.py for py2app bundling of my.File Tool
Run via: python setup.py py2app
Or use build_dmg.sh.
"""
import os
from setuptools import setup


def _read_version():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'VERSION')) as f:
        return f.read().strip()


VERSION = _read_version()

APP = ['large_file_finder.py']
APP_NAME = 'my.File Tool'

# Include modules and version file so the app can import them when bundled
DATA_FILES = [('', ['sensitive_scanner.py', 'scan_utils.py', 'update_checker.py', 'VERSION'])]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'MyhFileFinder.icns',
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': 'com.local.myfiletool',
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': '.'.join(VERSION.split('.')[:2]),
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,  # Show in Dock
        'NSHumanReadableCopyright': 'my.File Tool © 2026',
    },
    'packages': ['PyQt5', 'certifi'],
}

setup(
    app=APP,
    name=APP_NAME,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
