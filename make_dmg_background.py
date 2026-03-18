#!/usr/bin/env python3
"""
Generate dmg_background.png for the DMG installer.
Creates a modern drag-to-Applications layout inspired by apps like Granola:
  - Muted cream/warm gray background with subtle geometric curves
  - "To install, drag my.File Tool to Applications" text
  - Two dashed placeholder boxes with labels
  - A curved arrow pointing from app to Applications

Uses PyQt5 (same dep as the app). Run from the project dir:
  python3 make_dmg_background.py
"""
import sys
from pathlib import Path

# Match window bounds in build_dmg.sh AppleScript
W, H = 660, 440

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt, QRect, QPointF
    from PyQt5.QtGui import (
        QPainter, QImage, QLinearGradient, QColor, QPen, QBrush,
        QFont, QPainterPath,
    )
except ImportError:
    print("PyQt5 required. Run: pip3 install PyQt5", file=sys.stderr)
    sys.exit(1)


def main():
    app = QApplication(sys.argv)
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setRenderHint(QPainter.TextAntialiasing)

    # ── Background: warm cream/beige gradient ──
    grad = QLinearGradient(0, 0, W, H)
    grad.setColorAt(0, QColor("#F5F0E8"))
    grad.setColorAt(0.5, QColor("#EDE8DE"))
    grad.setColorAt(1, QColor("#F0EBE1"))
    p.fillRect(0, 0, W, H, grad)

    # ── Subtle decorative curves (like Granola) ──
    curve_pen = QPen(QColor(200, 195, 185, 60), 1.5)
    p.setPen(curve_pen)
    p.setBrush(Qt.NoBrush)

    # Large arc from bottom-left to upper-right
    arc1 = QPainterPath()
    arc1.moveTo(-100, H + 50)
    arc1.cubicTo(W * 0.3, H * 0.2, W * 0.6, H * 0.8, W + 100, -50)
    p.drawPath(arc1)

    # Second arc
    arc2 = QPainterPath()
    arc2.moveTo(-50, H * 0.6)
    arc2.cubicTo(W * 0.4, H * 0.1, W * 0.7, H * 0.5, W + 50, H * 0.3)
    p.drawPath(arc2)

    # Third arc
    arc3 = QPainterPath()
    arc3.moveTo(W * 0.2, H + 30)
    arc3.cubicTo(W * 0.5, H * 0.4, W * 0.8, H * 0.9, W + 80, H * 0.5)
    p.drawPath(arc3)

    # ── Title text (clean sans-serif, no italic/shadow) ──
    p.setPen(QColor("#3D3830"))
    title_font = QFont("Helvetica Neue", 20)
    title_font.setWeight(QFont.Light)
    p.setFont(title_font)
    p.drawText(QRect(0, 40, W, 36), Qt.AlignHCenter | Qt.AlignTop,
               "To install, drag")

    # Bold app name
    title_bold = QFont("Helvetica Neue", 22)
    title_bold.setWeight(QFont.DemiBold)
    p.setFont(title_bold)
    p.drawText(QRect(0, 76, W, 36), Qt.AlignHCenter | Qt.AlignTop,
               "my.File Tool")

    # "to Applications"
    p.setFont(title_font)
    p.drawText(QRect(0, 112, W, 36), Qt.AlignHCenter | Qt.AlignTop,
               "to Applications")

    # ── Dashed boxes ──
    # Icon positions must match build_dmg.sh AppleScript
    # App icon at (190, 260), Applications at (470, 260), icon size 100
    left_cx, left_cy = 190, 280    # center of app icon area
    right_cx, right_cy = 470, 280  # center of Applications area
    box_w, box_h = 130, 130

    box_pen = QPen(QColor(180, 175, 165, 120), 2, Qt.DashLine)
    box_pen.setDashPattern([6, 5])
    p.setPen(box_pen)
    p.setBrush(Qt.NoBrush)

    left_rect = QRect(left_cx - box_w // 2, left_cy - box_h // 2, box_w, box_h)
    p.drawRoundedRect(left_rect, 14, 14)

    right_rect = QRect(right_cx - box_w // 2, right_cy - box_h // 2, box_w, box_h)
    p.drawRoundedRect(right_rect, 14, 14)

    # No labels under boxes — Finder provides icon labels automatically

    # ── Curved arrow from left box to right box ──
    arrow_start_x = left_cx + box_w // 2 + 15
    arrow_end_x = right_cx - box_w // 2 - 15
    arrow_y = left_cy - 20  # slightly above center

    arrow_pen = QPen(QColor("#6B665C"), 3)
    arrow_pen.setCapStyle(Qt.RoundCap)
    p.setPen(arrow_pen)
    p.setBrush(Qt.NoBrush)

    # Curved arrow path
    arrow_path = QPainterPath()
    arrow_path.moveTo(arrow_start_x, arrow_y + 10)
    ctrl_y = arrow_y - 50  # curve upward
    arrow_path.cubicTo(
        arrow_start_x + 40, ctrl_y,
        arrow_end_x - 40, ctrl_y,
        arrow_end_x, arrow_y + 10,
    )
    p.drawPath(arrow_path)

    # Arrowhead at the end
    p.setBrush(QColor("#6B665C"))
    head = QPainterPath()
    tip_x, tip_y = arrow_end_x, arrow_y + 10
    head.moveTo(tip_x, tip_y)
    head.lineTo(tip_x - 14, tip_y - 8)
    head.lineTo(tip_x - 10, tip_y + 6)
    head.closeSubpath()
    p.drawPath(head)

    p.end()

    out = Path(__file__).parent / "dmg_background.png"
    img.save(str(out))
    print(f"Saved {out} ({W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
