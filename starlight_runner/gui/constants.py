"""
constants.py — Shared styling constants and light/dark theming for all GUI modules.

Widgets that need a themed color should NOT bake it into their own inline
setStyleSheet() string. Instead, set a Qt dynamic property (e.g.
``widget.setProperty("role", "mutedLabel")``) and let the app-wide stylesheet
built by build_stylesheet() color it via a ``[role="..."]`` selector. That way,
switching themes only requires re-applying the top-level stylesheet and
palette (see set_theme() / apply_theme()) — every widget using a role
re-colors automatically.

Other modules should access colors as ``constants.ACCENT`` (via
``from . import constants``) rather than ``from .constants import ACCENT``,
so they see the live value after a theme switch instead of the one captured
at import time.
"""

_LIGHT = dict(
    ACCENT="#2563EB",
    ACCENT_HOVER="#1D4ED8",
    WINDOW_BG="#FFFFFF",
    CARD_BG="#F8FAFC",
    TEXT_COLOR="#0F172A",
    MUTED="#64748B",
    SUBTLE_TEXT="#475569",
    BORDER_COLOR="#CBD5E1",
    SUCCESS_COLOR="#10B981",
    DANGER_COLOR="#EF4444",
    INPUT_BG="#FFFFFF",
    DISABLED_BG="#94A3B8",
    DISABLED_TEXT="#F1F5F9",
    NAV_HOVER_BG="#F1F5F9",
    NAV_HOVER_TEXT="#1E293B",
    NAV_ACTIVE_BG="#EFF6FF",
    NAV_ACTIVE_TEXT="#2563EB",
    HEADER_BG="#F1F5F9",
    HEADER_TEXT="#475569",
    GRIDLINE="#E2E8F0",
    SECONDARY_BTN_BG="#F8FAFC",
    SECONDARY_BTN_TEXT="#334155",
    HELP_BG="#F1F5F9",
    PROGRESS_BG="#F1F5F9",
    SLIDER_TRACK="#E2E8F0",
    SLIDER_HANDLE="#FFFFFF",
)

_DARK = dict(
    ACCENT="#3B82F6",
    ACCENT_HOVER="#60A5FA",
    WINDOW_BG="#0F172A",
    CARD_BG="#1E293B",
    TEXT_COLOR="#E2E8F0",
    MUTED="#94A3B8",
    SUBTLE_TEXT="#CBD5E1",
    BORDER_COLOR="#334155",
    SUCCESS_COLOR="#34D399",
    DANGER_COLOR="#F87171",
    INPUT_BG="#0F172A",
    DISABLED_BG="#334155",
    DISABLED_TEXT="#64748B",
    NAV_HOVER_BG="#334155",
    NAV_HOVER_TEXT="#F1F5F9",
    NAV_ACTIVE_BG="#1E3A8A",
    NAV_ACTIVE_TEXT="#DBEAFE",
    HEADER_BG="#334155",
    HEADER_TEXT="#CBD5E1",
    GRIDLINE="#334155",
    SECONDARY_BTN_BG="#1E293B",
    SECONDARY_BTN_TEXT="#CBD5E1",
    HELP_BG="#0F172A",
    PROGRESS_BG="#334155",
    SLIDER_TRACK="#334155",
    SLIDER_HANDLE="#E2E8F0",
)

# Matplotlib figures always render on a white canvas regardless of the app
# theme, so their hard-coded plot palettes stay put.

_is_dark = True
_colors = dict(_DARK)


def is_dark():
    return _is_dark


def _apply(colors):
    """Publish a palette's colors as module-level attributes (constants.ACCENT, etc.)."""
    globals().update(colors)
    # Backwards-compatible alias (historically the main window background)
    globals()["DARK_BG"] = colors["WINDOW_BG"]


def build_stylesheet():
    """Build the full app stylesheet from the current palette."""
    c = _colors
    return f"""
QMainWindow {{
    background: {c['WINDOW_BG']};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}

QDialog {{
    background: {c['WINDOW_BG']};
}}

QStatusBar {{
    background-color: {c['WINDOW_BG']};
    color: {c['TEXT_COLOR']};
}}

QWidget[role="sidebar"] {{
    background-color: {c['CARD_BG']};
    border-right: 1px solid {c['BORDER_COLOR']};
}}

QGroupBox {{
    background: {c['CARD_BG']};
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 8px;
    margin-top: 18px;
    padding: 16px 12px 12px 12px;
    color: {c['TEXT_COLOR']};
    font-weight: 600;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 2px;
    color: {c['ACCENT']};
    padding: 0 4px;
}}

QLabel {{
    color: {c['TEXT_COLOR']};
    background: transparent;
    font-size: 13px;
}}
QLabel[role="accentLabel"] {{
    color: {c['ACCENT']};
}}
QLabel[role="mutedLabel"] {{
    color: {c['MUTED']};
}}
QLabel[role="subtleLabel"] {{
    color: {c['SUBTLE_TEXT']};
}}
QLabel[role="helpBox"] {{
    color: {c['SUBTLE_TEXT']};
    background: {c['HELP_BG']};
    border-radius: 4px;
}}
QLabel[role="infoBanner"] {{
    background-color: {c['CARD_BG']};
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 6px;
    color: {c['SECONDARY_BTN_TEXT']};
}}

QPushButton {{
    background-color: {c['ACCENT']};
    color: white;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    padding: 8px 16px;
    border: none;
}}
QPushButton:hover {{
    background-color: {c['ACCENT_HOVER']};
}}
QPushButton:disabled {{
    background-color: {c['DISABLED_BG']};
    color: {c['DISABLED_TEXT']};
}}

QPushButton[role="secondaryBtn"] {{
    background-color: {c['SECONDARY_BTN_BG']};
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 6px;
    padding: 6px;
    color: {c['SECONDARY_BTN_TEXT']};
}}
QPushButton[role="secondaryBtn"]:hover {{
    background-color: {c['NAV_HOVER_BG']};
}}

QPushButton#navBtn {{
    background-color: transparent;
    color: {c['MUTED']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#navBtn:hover {{
    background-color: {c['NAV_HOVER_BG']};
    color: {c['NAV_HOVER_TEXT']};
}}
QPushButton#navBtn[active="true"] {{
    background-color: {c['NAV_ACTIVE_BG']};
    color: {c['NAV_ACTIVE_TEXT']};
    border-left: 3px solid {c['ACCENT']};
}}

QToolButton[role="collapsibleHeader"] {{
    border: none;
    font-weight: bold;
    font-size: 13px;
    color: {c['TEXT_COLOR']};
    background-color: transparent;
    padding: 6px;
}}
QToolButton[role="collapsibleHeader"]:hover {{
    color: {c['ACCENT']};
}}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: {c['INPUT_BG']};
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {c['TEXT_COLOR']};
    font-size: 13px;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {c['ACCENT']};
}}
QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {{
    color: {c['MUTED']};
}}
QComboBox QAbstractItemView {{
    background-color: {c['INPUT_BG']};
    color: {c['TEXT_COLOR']};
    selection-background-color: {c['ACCENT']};
    selection-color: white;
}}

QCheckBox, QRadioButton {{
    color: {c['TEXT_COLOR']};
    background: transparent;
    font-size: 13px;
    spacing: 6px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {c['BORDER_COLOR']};
    background-color: {c['INPUT_BG']};
    border-radius: 3px;
}}
QRadioButton::indicator {{
    border-radius: 7px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {c['ACCENT']};
    border-color: {c['ACCENT']};
}}
QCheckBox:disabled, QRadioButton:disabled {{
    color: {c['MUTED']};
}}

QTableWidget {{
    background-color: {c['INPUT_BG']};
    border: 1px solid {c['BORDER_COLOR']};
    gridline-color: {c['GRIDLINE']};
    border-radius: 6px;
    color: {c['TEXT_COLOR']};
}}
QHeaderView::section {{
    background-color: {c['HEADER_BG']};
    padding: 6px;
    border: 1px solid {c['BORDER_COLOR']};
    font-weight: 600;
    color: {c['HEADER_TEXT']};
}}
QTableCornerButton::section {{
    background-color: {c['HEADER_BG']};
    border: 1px solid {c['BORDER_COLOR']};
}}

QTabWidget::pane {{
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {c['CARD_BG']};
    color: {c['MUTED']};
    border: 1px solid {c['BORDER_COLOR']};
    padding: 6px 12px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background: {c['WINDOW_BG']};
    color: {c['ACCENT']};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QProgressBar {{
    border: 1px solid {c['BORDER_COLOR']};
    border-radius: 6px;
    background-color: {c['PROGRESS_BG']};
    text-align: center;
    color: {c['TEXT_COLOR']};
}}
QProgressBar::chunk {{
    background-color: {c['ACCENT']};
    border-radius: 5px;
}}

QToolTip {{
    background-color: {c['CARD_BG']};
    color: {c['TEXT_COLOR']};
    border: 1px solid {c['BORDER_COLOR']};
}}
"""


def build_palette():
    """Build a QPalette matching the current theme (used with the Fusion style)."""
    from PyQt5.QtGui import QPalette, QColor

    c = _colors
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(c['WINDOW_BG']))
    pal.setColor(QPalette.WindowText, QColor(c['TEXT_COLOR']))
    pal.setColor(QPalette.Base, QColor(c['INPUT_BG']))
    pal.setColor(QPalette.AlternateBase, QColor(c['CARD_BG']))
    pal.setColor(QPalette.Text, QColor(c['TEXT_COLOR']))
    pal.setColor(QPalette.Button, QColor(c['CARD_BG']))
    pal.setColor(QPalette.ButtonText, QColor(c['TEXT_COLOR']))
    pal.setColor(QPalette.ToolTipBase, QColor(c['CARD_BG']))
    pal.setColor(QPalette.ToolTipText, QColor(c['TEXT_COLOR']))
    pal.setColor(QPalette.PlaceholderText, QColor(c['MUTED']))
    pal.setColor(QPalette.Highlight, QColor(c['ACCENT']))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.Link, QColor(c['ACCENT']))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor(c['MUTED']))
    return pal


def set_theme(dark):
    """Switch the active palette and return the freshly built stylesheet."""
    global _is_dark, _colors
    _is_dark = bool(dark)
    _colors = dict(_DARK if _is_dark else _LIGHT)
    _apply(_colors)
    globals()["STYLESHEET"] = build_stylesheet()
    return STYLESHEET


def apply_theme(app, dark=None):
    """Apply the current (or requested) theme to a QApplication: palette + stylesheet."""
    if dark is not None:
        set_theme(dark)
    app.setPalette(build_palette())
    app.setStyleSheet(STYLESHEET)
    # Custom-painted widgets (e.g. DoubleSlider) read constants at paint time
    for w in app.allWidgets():
        w.update()


_apply(_colors)
STYLESHEET = build_stylesheet()
