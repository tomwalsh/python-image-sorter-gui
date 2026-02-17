import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


_COLORS = {
    "dark": {
        "accent": "#4fc3f7",
        "accent_hover": "#81d4fa",
        "accent_pressed": "#29b6f6",
        "border": "#555555",
        "surface": "#383838",
        "danger": "#ef5350",
        "danger_hover": "#e57373",
    },
    "light": {
        "accent": "#1976d2",
        "accent_hover": "#1565c0",
        "accent_pressed": "#0d47a1",
        "border": "#cccccc",
        "surface": "#f5f5f5",
        "danger": "#d32f2f",
        "danger_hover": "#c62828",
    },
}


class ThemeManager:
    def __init__(self, app: QApplication):
        self._app = app
        self._qss_template = self._load_template()

    def _load_template(self) -> str:
        qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()

    def current_scheme(self) -> str:
        hints = self._app.styleHints()
        scheme = hints.colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
        elif scheme == Qt.ColorScheme.Light:
            return "light"
        # Qt.ColorScheme.Unknown — check Windows registry directly
        return self._detect_windows_scheme()

    @staticmethod
    def _detect_windows_scheme() -> str:
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "light" if value else "dark"
            except OSError:
                pass
        return "light"

    def apply_theme(self, scheme: str | None = None):
        if scheme is None:
            scheme = self.current_scheme()

        # Set the palette for dark/light mode
        self._set_palette(scheme)

        # Apply the QSS stylesheet with theme colors
        colors = dict(_COLORS[scheme])
        arrow_svg = os.path.join(
            os.path.dirname(__file__), f"down-arrow-{scheme}.svg"
        )
        colors["arrow_path"] = arrow_svg.replace("\\", "/")
        qss = self._qss_template.format(**colors)
        self._app.setStyleSheet(qss)

    def _set_palette(self, scheme: str):
        """Set the application palette to match the theme scheme"""
        palette = QPalette()

        if scheme == "dark":
            # Dark mode palette with proper colors
            dark_bg = QColor(53, 53, 53)          # Main background
            darker_bg = QColor(35, 35, 35)        # Input fields background
            text_color = QColor(255, 255, 255)    # White text
            disabled_text = QColor(127, 127, 127) # Gray text
            highlight = QColor(79, 195, 247)      # Accent color (same as QSS)

            palette.setColor(QPalette.ColorRole.Window, dark_bg)
            palette.setColor(QPalette.ColorRole.WindowText, text_color)
            palette.setColor(QPalette.ColorRole.Base, darker_bg)
            palette.setColor(QPalette.ColorRole.AlternateBase, dark_bg)
            palette.setColor(QPalette.ColorRole.ToolTipBase, darker_bg)
            palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
            palette.setColor(QPalette.ColorRole.Text, text_color)
            palette.setColor(QPalette.ColorRole.Button, dark_bg)
            palette.setColor(QPalette.ColorRole.ButtonText, text_color)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, highlight)
            palette.setColor(QPalette.ColorRole.Highlight, highlight)
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

            # Disabled colors
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
        else:
            # Light mode — reset to default Fusion palette
            palette.setColor(QPalette.ColorRole.Window, QColor(239, 239, 239))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(239, 239, 239))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(239, 239, 239))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(48, 140, 198))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self._app.setPalette(palette)

    def follow_system(self):
        self.apply_theme()
        self._app.styleHints().colorSchemeChanged.connect(self._on_scheme_changed)

    def _on_scheme_changed(self, scheme):
        if scheme == Qt.ColorScheme.Dark:
            self.apply_theme("dark")
        elif scheme == Qt.ColorScheme.Light:
            self.apply_theme("light")
        else:
            self.apply_theme()
