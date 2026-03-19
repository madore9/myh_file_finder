# UI Redesign Prompts — One Per Tool

Attach a screenshot of the current app alongside each prompt.

---

## Prompt 1: ChatGPT / GPT-4o with DALL-E

```
[Attach current app screenshot here]

Redesign the macOS desktop app shown in the attached screenshot. The app is called "my.h File Finder" — a file scanning utility with 4 modes: Large Files, Duplicates, Sensitive Data, and String Search.

Generate a HIGH-FIDELITY, PHOTOREALISTIC macOS UI screenshot mockup — NOT a wireframe, NOT a sketch. The output should look like a real macOS app screenshot at 1440x900px resolution. Flat, straight-on view — NO 3D perspective, NO device frames, NO tilted angles.

Design target: native macOS polish at the level of macOS System Settings or Finder.

Required UI elements:
1. TRANSLUCENT SIDEBAR (left, ~180px wide): Mode navigation with SF Symbol-style icons, text labels, and count badges (e.g., "Large Files (1,247)"). Use macOS vibrancy/frosted glass material.
2. COMPACT SETTINGS BAR (top of content area): Contextual settings for the selected mode (path input, filters) with an integrated blue "Scan" button on the right.
3. THIN PROGRESS BAR: Safari-style 2px progress bar at the very top of the content area.
4. SUMMARY STRIP: Horizontal bar below settings showing scan stats (e.g., "1,247 files | 84.3 GB total | Largest: 12.1 GB").
5. RESULTS TABLE: Alternating-row table with color-coded severity pills — green (#34C759) for "Safe", orange (#FF9500) for "Caution", red (#FF3B30) for "High Priority". SF Pro font, 12px.
6. STICKY BOTTOM ACTION BAR: Persistent bar with action buttons (Open, Reveal in Finder, Delete).
7. EMPTY/WELCOME STATE (for one mockup): Centered magnifying glass icon + "Welcome to my.h File Finder" + "Select a mode and path, then start scanning".

Color palette: Primary #007AFF, Success #34C759, Warning #FF9500, Danger #FF3B30. SF Pro font throughout. Rounded corners, subtle shadows, system accent colors.

Generate this as a DARK MODE version showing the "Large Files" scan mode with results populated.

Style keywords: Dribbble-quality, photorealistic macOS UI, 8K resolution, flat screenshot render, professional desktop application, clean minimal interface.
```

---

## Prompt 2: v0.dev by Vercel

```
[Attach current app screenshot here]

Build a React + Tailwind CSS redesign of the macOS desktop app shown in the screenshot. The app is "my.h File Finder" — a file scanning utility with 4 modes.

Create a single self-contained component using shadcn/ui and Lucide icons with this layout:

LEFT SIDEBAR (~180px, fixed):
- Use backdrop-blur-xl and bg-black/60 (dark) or bg-white/80 (light) for translucency
- 4 navigation items with Lucide icons + labels + count badges:
  - HardDrive icon → "Large Files" (1,247)
  - Copy icon → "Duplicates" (89)
  - Shield icon → "Sensitive Data" (16)
  - Search icon → "String Search" (342)
- Active item has blue highlight bg

MAIN CONTENT AREA:
- Top: Compact settings bar with Input (scan path), Button (Browse), mode-specific controls, and a blue "Start Scan" Button right-aligned
- Below settings: 2px blue progress bar (like Safari loading bar)
- Summary strip: subtle blue-tinted card showing stats like "1,247 files found | 84.3 GB total | Largest: 12.1 GB"
- Results table using shadcn Table component with alternating rows. Include a "Confidence" column with colored Badge components: green "Safe", orange "Caution", red "High Priority"
- Sticky bottom bar with action buttons: "Open", "Reveal in Finder", "Delete Selected"

STATES:
- Include a working dark/light mode toggle (Moon/Sun icon in top-right)
- Clicking sidebar items switches the main content (use React state)
- Include an empty/welcome state: centered SearchIcon (64px, gray) + "Welcome to my.h File Finder" heading + "Select a mode and path, then start scanning" subtext

Target: 1440x900px macOS window. Use SF Pro-like system font stack. Rounded corners (8px), subtle borders, macOS system colors.

Populate the Large Files table with 8-10 realistic sample rows (file names like "project_backup.zip", "virtual_machine.vmdk", sizes like "4.2 GB", "1.8 GB").
```

---

## Prompt 3: Figma AI / Magician Plugin

```
[Attach current app screenshot here]

Create a Figma design system and high-fidelity mockups for a macOS desktop app redesign. The app is "my.h File Finder" — a file scanning utility with 4 modes: Large Files, Duplicates, Sensitive Data, and String Search.

DESIGN SYSTEM SETUP:
- Design tokens consistent with Apple Human Interface Guidelines
- Typography: SF Pro Display (headings), SF Pro Text (body) — sizes 11, 12, 13, 15, 18, 22px
- Color tokens: Primary #007AFF, Success #34C759, Warning #FF9500, Danger #FF3B30, plus semantic background/surface/border tokens for both light and dark themes
- Spacing scale: 4, 8, 12, 16, 24, 32px
- Corner radius: 6px (small), 8px (medium), 12px (large)

COMPONENT LIBRARY:
Create reusable components with variants:
1. SidebarItem — states: default, hover, active. Props: icon, label, badge count
2. SettingsBar — variants per scan mode (Large Files, Duplicates, Sensitive, String Search)
3. SeverityPill — variants: Safe (green), Caution (orange), High Priority (red), Info (blue)
4. TableRow — alternating background, with pill component for confidence column
5. ActionBar — sticky bottom bar with button group
6. EmptyState — centered illustration + heading + subtext

MOCKUP SCREENS (1440x900px, auto-layout frames):
Create 10 screens total:
1-4: Each scan mode with populated results (dark mode)
5: Empty/welcome state (dark mode)
6-10: Same 5 screens in light mode

LAYOUT:
- Translucent sidebar (180px) with vibrancy effect on left
- Compact settings bar at top of content area with integrated scan button
- 2px Safari-style progress bar
- Summary strip with scan statistics
- Results table with alternating rows and severity pills
- Sticky bottom action bar

Use organized, cleanly named layers. Group by screen. Use auto-layout throughout. Export-ready at 2x.
```

---

## Prompt 4: Claude with Artifacts

```
[Attach current app screenshot here]

Create a single interactive React artifact that redesigns the macOS app shown in the screenshot. The app is "my.h File Finder" — a file scanning utility.

Build a complete, self-contained React component using Tailwind CSS and Lucide React icons. The artifact should be fully interactive in Claude's preview window.

LAYOUT (1440x900px macOS window):

LEFT SIDEBAR (180px, fixed):
- Semi-transparent background: dark mode bg-gray-900/80 backdrop-blur-xl, light mode bg-gray-100/80 backdrop-blur-xl
- Border-right separator
- 4 nav items, each with: Lucide icon (HardDrive, Copy, ShieldCheck, Search), label, count badge
- onClick switches the active mode via React useState
- Active item: bg-blue-500/20 with blue text

MAIN CONTENT:
- Top settings bar: text input for scan path, "Browse" button, mode-specific inline controls, blue "Start Scan" button right-aligned
- 2px blue progress bar below settings (w-3/4 for demo)
- Summary strip: rounded card with blue-50 bg showing "1,247 files found | 84.3 GB total | Largest: 12.1 GB"
- Data table with alternating row backgrounds (gray-50/gray-900 alternating). Columns: checkbox, File Name, Location, Size, Modified, Confidence
- Confidence column uses colored pill badges: green-500 bg "Safe to Delete", orange-500 bg "Caution", red-500 bg "Keep"
- Bottom action bar: sticky, border-top, buttons for "Open", "Reveal in Finder", "Delete Selected"

STATES TO IMPLEMENT:
- useState for activeMode (switches sidebar highlight + main content)
- useState for darkMode (toggle via Moon/Sun button in top-right corner)
- Each mode shows different sample data and column headers
- When activeMode has no data yet, show empty state: centered Search icon (64px, text-gray-400) + "Welcome to my.h File Finder" (text-lg font-semibold) + "Select a mode and path, then start scanning" (text-sm text-gray-500)

SAMPLE DATA:
Populate Large Files mode with 8 rows of realistic macOS files (e.g., "Xcode_15.2.xip" 12.1 GB, "Windows11.vmdk" 8.4 GB, etc.). Populate Sensitive mode with sample findings. Make it look like a real, populated app.

Style: macOS native feel. Use system font stack (-apple-system, SF Pro). Rounded corners. Subtle shadows. Clean, professional, minimal.
```
