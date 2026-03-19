# UI Redesign Handoff

## Start Here

You are implementing a UI redesign of the my.h File Finder macOS desktop app. The app is a PyQt5 desktop application at `/Users/crm990/AI/macApps/LargeFileFinder/`.

**Open the prototype first** to see the target design:
```bash
open docs/design/prototype.html
```
This is the interactive reference — click through all 4 sidebar modes (Sensitive, Large Files, Duplicates, String Search) and toggle dark/light mode. Your job is to make the PyQt5 app look and behave like this prototype.

## Key Files

| File | Purpose |
|------|---------|
| `large_file_finder.py` | Main app (~3000 lines), class `MyhFileFinder(QMainWindow)` — this is what you're modifying |
| `docs/design/prototype.html` | Interactive HTML prototype — THE visual target |
| `docs/design/UI_REDESIGN_SPEC.md` | Detailed specs (colors, typography, spacing, widget mapping) |
| `scan_utils.py` | Shared scanning utilities |
| `sensitive_scanner.py` | Sensitive data scan engine |
| `update_checker.py` | Auto-update system |
| `VERSION` | Current version (bump on each commit) |

## Harvard Color Palette

```python
CRIMSON      = '#A51C30'  # Primary accent, buttons, active states
CRIMSON_DARK = '#8C1515'  # Hover states
CRIMSON_LIGHT= '#C63D3D'  # Light mode pill text
BLACK        = '#1E1E1E'  # Dark mode base
PARCHMENT    = '#F3F0EB'  # Light mode background
MORTAR       = '#8C8179'  # Secondary text
IVY          = '#52854C'  # Safe/Low severity pills
GOLD         = '#C4953A'  # Caution/Medium severity pills
BLUEBONNET   = '#4E84C4'  # Info accent (optional)
```

## Design Decisions (from prototype)

1. **Sidebar first, not dropdown**: QListWidget on the left (200px) replaces the mode dropdown. Sensitive Data is the FIRST item.
2. **Compact settings**: No QGroupBox. Flat rows with inline controls per mode.
3. **Summary strip**: Horizontal stats bar after scan completes (crimson accent).
4. **Severity pills**: Colored rounded badges in table cells via QStyledItemDelegate.
5. **Exclude folders as tags**: Removable pill-shaped tags, not a QListWidget.
6. **Harvard crimson scan button**: Right-aligned in settings bar, not centered.
7. **Progress bar**: 2px thin bar with crimson gradient, not the chunky default.
8. **Light mode default**: App starts in light mode. Detects system preference.
9. **Bottom action bar**: Select All / Deselect All on left, Open / Reveal / Delete on right.
10. **Mode-specific Show filter**: Sensitive gets HIGH/MEDIUM/LOW/HUID/SSN/EMAIL; Large gets Safe/Caution/Keep.

## What Currently Exists

The current UI is a single-panel layout with:
- Mode dropdown at top (needs to become sidebar)
- QGroupBox "Scan Settings" with mode-specific controls (needs to become flat compact bar)
- Centered blue Start/Stop Scan button (needs to move right, become crimson)
- QProgressBar (needs to become 2px thin bar)
- QTableWidget results (needs alternating rows, severity pills, sticky header)
- Bottom bar with summary + action buttons (needs Harvard styling)

Key architecture points you must preserve:
- `_scan_mode` attribute tracks current mode ("large_files", "duplicates", "sensitive", "string_search")
- `_set_table_columns_*()` methods configure table per mode
- Scanner threads emit batched signals (250ms intervals)
- Dark/light mode detection in `_apply_table_theme()`
- Right-click context menu with "Exclude folder" option
- All existing scan functionality MUST still work

## Implementation Plan

Do this in a **worktree** to avoid breaking the working app on main.

### Phase 1: Sidebar + Layout Restructure
- Replace mode dropdown with QListWidget sidebar (200px, left)
- Use QHBoxLayout: sidebar | QVBoxLayout(settings + table + bottom)
- Order: Sensitive Data, Large Files, Duplicates, String Search
- Wire sidebar `.currentItemChanged` to mode switching (replace dropdown logic)
- Add count badges to sidebar items (update after scan completes)
- Test: all 4 modes must work, all scans must complete

### Phase 2: Compact Settings + Harvard Styling
- Remove QGroupBox, use flat QFrame rows
- Row 1: Scan Path + Browse + mode-agnostic options + crimson Scan button (right)
- Row 2: Mode-specific controls (profiles, exclude tags, size filter, search input, etc.)
- Replace QProgressBar with 2px crimson gradient bar
- Apply Harvard color palette via QSS
- Test: all settings must persist and affect scans correctly

### Phase 3: Summary Strip + Table Styling
- Add summary QFrame between settings and table
- Populate with mode-specific stats in `_on_*_scan_finished` handlers
- Add alternating row colors via QSS
- Create PillDelegate for severity/confidence columns
- Apply crimson accent to headers, selection, etc.
- Test: pills render correctly in all modes, sort still works

### Phase 4: Polish + Empty State
- Add empty state widget (icon + text) when no scan has run
- Refine update banner (thin crimson bar)
- Style bottom action bar (Select All/Deselect on left, actions on right)
- Mode-specific Show filter dropdown
- Final QSS pass for light AND dark mode
- Test: both themes look correct, all interactions work

## Rules

- **Bump VERSION** on each commit (patch: 1.3.3, 1.3.4, etc.)
- **Don't break functionality** — every scan mode must work throughout
- **Dark AND light mode** must both work (test both after each phase)
- **Always rebuild and test**: `rm -rf build/ dist/ && python3 setup.py py2app && bash build_dmg.sh`
- **Commit after each phase** with descriptive messages
- **The prototype is the source of truth** — if something looks different from `prototype.html`, fix it to match
