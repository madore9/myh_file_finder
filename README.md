# my.h File Finder
<p align="center">
  <img src="https://raw.githubusercontent.com/madore9/myh_file_finder/main/docs/images/hero_banner.png" alt="my.h File Finder Hero Banner" width="100%">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.3-blue.svg" alt="Version 1.0.3">
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS Supported">
  <img src="https://img.shields.io/badge/language-Python-yellow.svg" alt="Python Powered">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
</p>

<p align="center">
  <a href="https://github.com/madore9/myh_file_finder/releases/latest/download/MyFileTool-latest.dmg">
    <img src="https://img.shields.io/badge/%E2%AC%87%EF%B8%8F_Download_Now-macOS-0078D4?style=for-the-badge&logo=apple&logoColor=white" alt="Download Now — macOS" height="48">
  </a>
</p>

## Elevator Pitch

**my.h File Finder** is a specialized macOS desktop utility designed for IT staff and power users, particularly within institutional environments like Harvard University. It provides a fast, signature-based, and highly configurable toolkit to reclaim disk space and identify non-compliant data. Whether you are hunting down multi-gigabyte virtual machines, purging exact duplicates, or auditing for exposed sensitive institutional data, my.h File Finder scans your entire drive in minutes, not hours.

---

## Key Features

my.h File Finder operates in four primary specialized modes:

### 📦 **Large Files**
Finds files exceeding a configurable size threshold (e.g., >1GB). The results view displays the file's last-opened date (helping identify archived vs. active data) and provides a unique "safe to delete" confidence rating (0-100), assisting in quick cleanup decisions.

### 👥 **Duplicates**
Identifies exact duplicate files using a robust, performance-optimized two-tier hashing architecture. It performs an initial, lightning-fast 4KB hash of the file header to quickly rule out unique files, followed by a full SHA-256 hash of confirmed candidates to guarantee byte-for-byte identity.

### 🛡️ **Sensitive Data (Institutional Compliance)**
A powerful audit tool designed for data cleanup and institutional compliance. It utilizes optimized regular expressions to scan files for patterns matching:
* Harvard University IDs (HUID)
* Social Security Numbers (SSN)
* Harvard University email addresses (`@harvard.edu`, etc.)

### 🔍 **String Search**
A versatile, `grep`-like search engine. Perform advanced scans across your entire file system for any specific text string or complex regex pattern.

---

## How It Works: Architecture & Performance

my.h File Finder is engineered for speed and responsiveness on modern macOS systems.

* **PyQt5 GUI:** A modern, native macOS desktop experience built on Python 3 and PyQt5.
* **Non-Blocking UI (QThread):** All file scanning and heavy processing are offloaded to background threads using `QThread`.
* **Batched Signal Architecture:** The backend emitter uses a strict 250ms interval for batching UI updates. This prevents signal saturation and ensures the interface remains fully responsive even during high-throughput scanning.
* **`os.scandir`-Based Fast Walk:** We utilize Python's advanced `os.scandir` iterator for directory traversal. By retrieving file attributes during the initial directory listing, we eliminate redundant `stat()` syscalls, significantly boosting traversal speed.
* **Smart Skip Lists:** The scanner automatically respects built-in skip lists for known system directories, `.app` bundles, Time Machine backups, and local cloud drive caches (like Dropbox/OneDrive local copies), focusing the scan where it matters most.

---

## Installation

The easiest way to install **my.h File Finder** is to download the latest packed application.

1.  Navigate to the [Releases](https://github.com/madore9/myh_file_finder/releases) page.
2.  Download the latest `.dmg` file.
3.  Open the DMG and drag the **my.File Tool** app icon to your `Applications` folder.

---

## Auto-Update

The application includes an automated update check.

On every launch, the app queries the GitHub Releases API. If a newer version is detected, the UI will notify you with a banner. You can trigger a one-click download and installation directly from the update prompt — no need to manually visit GitHub.

---

## Development

To set up a local development environment:

1.  Clone the repository:
    ```bash
    git clone https://github.com/madore9/myh_file_finder.git
    cd myh_file_finder
    ```

2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Run the application from source:
    ```bash
    python3 large_file_finder.py
    ```

### Built With

* [Python 3](https://www.python.org/)
* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI Framework
* [py2app](https://github.com/ronaldoussoren/py2app) - macOS Deployment Tool

---

## Contributing

We welcome contributions to my.h File Finder! Please open an issue or submit a pull request on [GitHub](https://github.com/madore9/myh_file_finder).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
