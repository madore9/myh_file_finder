# UI Redesign Handoff

## Start Here

You are implementing a UI redesign of the my.h File Finder macOS desktop app. The app is a PyQt5 desktop application at `/Users/crm990/AI/macApps/LargeFileFinder/`.

## Context

- **Repo:** https://github.com/madore9/myh_file_finder
- **Current version:** See `VERSION` file
- **Main file:** `large_file_finder.py` (~2900 lines, contains the `MyhFileFinder(QMainWindow)` class)
- **Design spec:** `docs/design/UI_REDESIGN_SPEC.md` — READ THIS FIRST. It has the complete layout, QSS, widget specs, color palette, typography, spacing, and phased implementation plan.
- **Mockup gallery:** `docs/design/option_c_plus_gallery.png` — the visual target from Google Gemini

## What Exists Today

Single-panel layout with:
- Mode dropdown at top (Large files / Duplicates / Sensitive / String search)
- QGroupBox "Scan Settings" with mode-specific controls
- Centered blue Start/Stop Scan button
- QProgressBar
- Status label
- Filter bar (search + "Show:" dropdown)
- QTableWidget results table (columns vary by mode)
- Bottom bar with summary + action buttons (Open, Reveal, Delete)

Key architecture points:
- `_scan_mode` attribute tracks current mode ("large_files", "duplicates", "sensitive", "string_search")
- `_set_table_columns_*()` methods configure table per mode
- Scanner threads emit batched signals (250ms intervals) to avoid UI freeze
- Dark/light mode detection already exists in `_apply_table_theme()`
- Right-click context menu already implemented

## What We're Building

**Option C+ (Native macOS Refined):** Sidebar navigation, compact settings bar, summary strip, severity pills, empty state, thin progress bar. See the spec for full details.

## Implementation Plan

Follow this order. Each phase should be a separate commit. Test after each phase — the app should remain fully functional throughout.

### Phase 1: Sidebar + Layout Restructure
Replace the mode dropdown with a QListWidget sidebar. Use QHBoxLayout to split the window into sidebar (180px fixed) + content area. Move all mode-switching logic from dropdown `.currentIndexChanged` to sidebar `.currentItemChanged`. Every existing feature must still work after this phase.

### Phase 2: Summary Strip + Compact Settings
Add a summary strip QFrame between settings and table. Populate it with mode-specific stats in `_on_scan_finished` / `_on_sensitive_scan_finished` / etc. Compact the settings area — remove QGroupBox chrome, use a flat QFrame. Move Start/Stop button to the right side of the settings bar. Replace the progress bar with a 2px Safari-style bar.

### Phase 3: Severity Pills + Table Styling
Create a `PillDelegate(QStyledItemDelegate)` for the Confidence column. Apply alternating row colors. Style headers. Ensure dark/light mode both look good. The delegate should paint colored rounded rects with white text.

### Phase 4: Empty State + Polish
Add a centered "Welcome to my.h File Finder" empty state in the table area. Refine the update banner to a thin, subtle bar. Add count badges to sidebar items after scan. Final QSS pass.

## Rules

- **Always rebuild and test** after each phase: `rm -rf build/ dist/ && python3 setup.py py2app && bash build_dmg.sh`
- **Bump VERSION** on each commit (patch: 1.1.3, 1.1.4, etc.)
- **Don't break functionality** — every scan mode must work throughout the refactor
- **Dark mode and light mode** must both work
- **The app title bar** should say "my.h File Finder" (not "my.File Tool")
- **Commit and push** after each phase with descriptive messages
- **Tag and release** after Phase 4 is complete
