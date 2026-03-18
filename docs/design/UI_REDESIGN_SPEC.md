# my.h File Finder — UI Redesign Spec (Option C+)

## Design Direction

**"Native macOS Refined"** — Looks like a first-party Apple app with cherry-picked elements from Clean Minimal and Dashboard Pro designs. Generated via Google Gemini, March 2026.

Mockup gallery image: `docs/design/option_c_plus_gallery.png`

---

## Core Layout (replaces current single-panel design)

```
┌──────────────────────────────────────────────────────────┐
│  my.h File Finder                              [toolbar] │
├────────────┬─────────────────────────────────────────────┤
│            │  [Mode] [Scan Path] [Browse] [Settings] [▶]│
│  SIDEBAR   │─────────────────────────────────────────────│
│            │  ═══ thin progress bar (Safari-style) ═══   │
│ 🔍 Large   │─────────────────────────────────────────────│
│    Files   │  Summary Strip: "1,247 files | 84.3 GB..." │
│   (1,247)  │─────────────────────────────────────────────│
│            │                                             │
│ 🛡 Sensitive│  ┌──────────────────────────────────────┐   │
│    Files   │  │        RESULTS TABLE                 │   │
│    (16)    │  │   (dominates the view)               │   │
│            │  │   alternating row backgrounds         │   │
│ 👥 Dupli-  │  │   severity pills in cells            │   │
│   cates    │  │   right-click context menu            │   │
│    (89)    │  │                                       │   │
│            │  └──────────────────────────────────────┘   │
│ 🔎 String  │─────────────────────────────────────────────│
│   Search   │  [Summary] [Selection]    [Open][Reveal][🗑]│
│   (342)    │                                             │
└────────────┴─────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Sidebar Navigation

**Widget:** `QListWidget` with custom styling
**Behavior:** Clicking a mode switches the main content area (like Finder sidebar)

- Translucent dark background (fake vibrancy via QSS: semi-transparent + slight blur)
- Each item: icon (SF Symbols style) + text label + optional count badge
- Count badges appear after scan completes (e.g., "Large Files (1,247)")
- Active item has highlight background
- Width: ~180px fixed

**QSS approach:**
```css
QListWidget {
    background-color: rgba(30, 30, 30, 200);  /* dark mode */
    /* background-color: rgba(240, 240, 240, 200);  light mode */
    border-right: 1px solid rgba(255,255,255,0.1);
    font-size: 13px;
}
QListWidget::item {
    padding: 10px 16px;
    border-radius: 6px;
    margin: 2px 8px;
}
QListWidget::item:selected {
    background-color: rgba(0, 122, 255, 0.3);
}
```

### 2. Compact Settings Bar

**Replaces:** Current chunky QGroupBox "Scan Settings"
**Widget:** QFrame with QHBoxLayout

- Mode dropdown (if not using sidebar — but sidebar replaces this)
- Scan Path QLineEdit + Browse QPushButton
- Mode-specific controls (compact, inline):
  - Large files: Size filter dropdown
  - Sensitive: Profile checkboxes (HUID/SSN/TAX/EMAIL) inline
  - String search: Search input + regex checkbox
  - Duplicates: Verify content checkbox
- **Start/Stop Scan button**: right-aligned, blue (#007AFF), becomes red "Stop" with spinner during scan
- Height: ~44px, single row

### 3. Progress Indicator

**Replaces:** Current chunky QProgressBar
**Widget:** QProgressBar with 2px height, styled to look like Safari's loading bar

```css
QProgressBar {
    border: none;
    background: transparent;
    height: 2px;
    max-height: 2px;
}
QProgressBar::chunk {
    background-color: #007AFF;
    border-radius: 1px;
}
```

### 4. Summary Strip

**New component** — appears between settings bar and results table after scan completes
**Widget:** QFrame with QHBoxLayout of QLabels

Content per mode:
- **Large Files:** `"1,247 files found | 84.3 GB total | Largest: 12.1 GB"`
- **Sensitive:** `"3 files with SSN | 12 with HUID | 1 with TAX ID | 47 with EMAIL"`
- **Duplicates:** `"89 duplicate groups | 23.1 GB wasted space"`
- **String Search:** `"342 matches across 91 files"`

**Style:** Subtle background, small font, key numbers in bold

```css
QFrame#summary_strip {
    background-color: rgba(0, 122, 255, 0.08);
    border-radius: 6px;
    padding: 6px 12px;
    margin: 4px 0;
}
```

### 5. Results Table

**Widget:** QTableView + QAbstractTableModel (migrate from QTableWidget for performance)
**Or:** Keep QTableWidget but add custom delegate for pills

Key styling:
- Alternating row colors: `table.setAlternatingRowColors(True)`
- Grid lines: subtle or none
- Header: bold, slightly darker background
- Right-click context menu: Open, Reveal in Finder, Copy Path, Delete

```css
QTableView {
    alternate-background-color: rgba(255, 255, 255, 0.03);  /* dark */
    gridline-color: rgba(255, 255, 255, 0.05);
    font-size: 12px;
    selection-background-color: rgba(0, 122, 255, 0.3);
}
QHeaderView::section {
    background-color: rgba(255, 255, 255, 0.05);
    font-weight: bold;
    font-size: 12px;
    padding: 6px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

### 6. Severity Pills (Custom Delegate)

**Used in:** Confidence column (Large Files), Sensitivity column (Sensitive)
**Widget:** `QStyledItemDelegate` subclass

Paint rounded pill badges:
- Green pill (#34C759): "Safe to Delete", "Low"
- Orange pill (#FF9500): "Caution", "Medium"
- Red pill (#FF3B30): "Keep", "High Priority"

```python
class PillDelegate(QStyledItemDelegate):
    COLORS = {
        "Safe to Delete": "#34C759",
        "Caution": "#FF9500",
        "Keep": "#FF3B30",
    }

    def paint(self, painter, option, index):
        text = index.data()
        color = self.COLORS.get(text, "#888")
        # Draw rounded rect background
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, rect.height()//2, rect.height()//2)
        # Draw text centered
        painter.setPen(QColor("white"))
        painter.drawText(rect, Qt.AlignCenter, text)
```

### 7. Empty/Welcome State

**Shown:** When no scan has been run (table area is empty)
**Widget:** QLabel stack centered in the table area

- Magnifying glass or folder icon (64x64, gray)
- "Welcome to my.h File Finder" (18px, bold)
- "Select a mode and path, then start scanning" (13px, gray)
- Disappears when first scan starts

### 8. Update Banner

**Replaces:** Current yellow QFrame banner
**Widget:** Thin QFrame bar at very top of window

- Height: ~32px
- Background: subtle blue tint
- Text: "Update available: v1.2.0" + "Install Update" link + "View Release" link
- Dismiss: small X button on right

### 9. Bottom Action Bar

**Widget:** QFrame with QHBoxLayout, sticky at bottom
**Contents:**
- Left: Summary label + Selection count
- Right: Action buttons (Open, Reveal in Finder, Secure Delete)
- Buttons use standard macOS blue/red styling

---

## Color Palette

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| Primary | #007AFF | #0A84FF | Buttons, links, selection |
| Success | #34C759 | #30D158 | Safe/low severity pills |
| Warning | #FF9500 | #FF9F0A | Medium severity pills |
| Danger | #FF3B30 | #FF453A | High severity pills, delete |
| Background | system | system | Window background |
| Sidebar BG | rgba(240,240,240,0.9) | rgba(30,30,30,0.9) | Sidebar |
| Table Alt | rgba(0,0,0,0.02) | rgba(255,255,255,0.03) | Alternating rows |
| Border | rgba(0,0,0,0.1) | rgba(255,255,255,0.1) | Dividers |

## Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Window title | System | 13px | Bold |
| Sidebar items | System | 13px | Regular |
| Sidebar badges | System | 11px | Medium |
| Settings bar | System | 12px | Regular |
| Summary strip | System | 12px | Regular (numbers bold) |
| Table header | System | 12px | Bold |
| Table cells | System | 12px | Regular |
| Pill badges | System | 11px | Medium |
| Status text | System | 11px | Regular |
| Empty state title | System | 18px | Bold |
| Empty state subtitle | System | 13px | Regular |

## Spacing

| Element | Value |
|---------|-------|
| Sidebar width | 180px |
| Sidebar item padding | 10px 16px |
| Sidebar item margin | 2px 8px |
| Settings bar height | 44px |
| Settings bar padding | 8px 12px |
| Summary strip padding | 6px 12px |
| Table row height | 28px |
| Bottom bar height | 44px |
| Bottom bar padding | 8px 12px |
| General margin | 8px (standard), 4px (compact) |

---

## Implementation Phases

### Phase 1: Sidebar + Layout Restructure
- Replace mode dropdown with QListWidget sidebar
- Use QSplitter or QHBoxLayout for sidebar + content
- Move mode-switching logic from dropdown to sidebar selection
- Wire up all existing functionality to new layout

### Phase 2: Summary Strip + Compact Settings
- Create summary strip QFrame (hidden until scan completes)
- Populate with mode-specific stats after each scan
- Compact the settings bar (remove QGroupBox, use flat QFrame)
- Move Start/Stop button to right side of settings bar
- Replace QProgressBar with 2px Safari-style bar

### Phase 3: Severity Pills + Table Styling
- Create PillDelegate for confidence/severity columns
- Apply alternating row colors via QSS
- Style table headers
- Ensure dark/light mode QSS works

### Phase 4: Empty State + Polish
- Create centered empty state widget (icon + text)
- Show/hide based on scan state
- Refine update banner (thin bar, not yellow box)
- Add sidebar count badges after scan
- Final QSS polish pass for both light and dark mode
