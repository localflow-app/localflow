from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt

class ThemeManager:
    # Modern Dark Theme Palette
    COLORS = {
        "background": "#1e1e1e",
        "surface": "#252526",
        "surface_light": "#2d2d2d",
        "surface_lighter": "#333333",
        "border": "#3f3f3f",
        "text": "#cccccc",
        "text_secondary": "#858585",
        "accent": "#007acc",
        "accent_hover": "#0062a3",
        "accent_pressed": "#004e82",
        "success": "#4ec9b0",
        "warning": "#ce9178",
        "error": "#f48771",
        "selection": "#264f78",
        "white": "#ffffff"
    }

    @staticmethod
    def apply_theme(app):
        """Apply global theme to QApplication"""
        app.setStyle("Fusion")
        
        palette = QPalette()
        
        # Base colors
        palette.setColor(QPalette.Window, QColor(ThemeManager.COLORS["background"]))
        palette.setColor(QPalette.WindowText, QColor(ThemeManager.COLORS["text"]))
        palette.setColor(QPalette.Base, QColor(ThemeManager.COLORS["surface"]))
        palette.setColor(QPalette.AlternateBase, QColor(ThemeManager.COLORS["surface_light"]))
        palette.setColor(QPalette.ToolTipBase, QColor(ThemeManager.COLORS["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(ThemeManager.COLORS["text"]))
        palette.setColor(QPalette.Text, QColor(ThemeManager.COLORS["text"]))
        palette.setColor(QPalette.Button, QColor(ThemeManager.COLORS["surface_light"]))
        palette.setColor(QPalette.ButtonText, QColor(ThemeManager.COLORS["text"]))
        palette.setColor(QPalette.BrightText, QColor(ThemeManager.COLORS["white"]))
        palette.setColor(QPalette.Link, QColor(ThemeManager.COLORS["accent"]))
        palette.setColor(QPalette.Highlight, QColor(ThemeManager.COLORS["selection"]))
        palette.setColor(QPalette.HighlightedText, QColor(ThemeManager.COLORS["white"]))
        
        # Disabled state
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(ThemeManager.COLORS["text_secondary"]))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(ThemeManager.COLORS["text_secondary"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(ThemeManager.COLORS["text_secondary"]))
        
        app.setPalette(palette)
        
        # Global Stylesheet
        app.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 9pt;
            }}
            
            QMainWindow::separator {{
                background-color: {ThemeManager.COLORS['border']};
                width: 1px;
                height: 1px;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {ThemeManager.COLORS['background']};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: #424242;
                min-height: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: #4f4f4f;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background: {ThemeManager.COLORS['background']};
                height: 10px;
                margin: 0px 0px 0px 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: #424242;
                min-width: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: #4f4f4f;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            
            QToolTip {{
                color: {ThemeManager.COLORS['text']};
                background-color: {ThemeManager.COLORS['surface_lighter']};
                border: 1px solid {ThemeManager.COLORS['border']};
            }}
            
            QMenu {{
                background-color: {ThemeManager.COLORS['surface_light']};
                color: {ThemeManager.COLORS['text']};
                border: 1px solid {ThemeManager.COLORS['border']};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {ThemeManager.COLORS['selection']};
                color: {ThemeManager.COLORS['white']};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {ThemeManager.COLORS['border']};
                margin: 4px 10px;
            }}
            
            QMenuBar {{
                background-color: {ThemeManager.COLORS['background']};
                color: {ThemeManager.COLORS['text']};
            }}
            
            QMenuBar::item {{
                padding: 6px 10px;
                background: transparent;
            }}
            
            QMenuBar::item:selected {{
                background: {ThemeManager.COLORS['surface_light']};
            }}
            
            QMessageBox {{
                background-color: {ThemeManager.COLORS['surface']};
            }}
        """)

    @staticmethod
    def get_toolbar_style(border_side="bottom"):
        """Get stylesheet for QToolBar"""
        border_css = f"border-{border_side}: 1px solid {ThemeManager.COLORS['border']};"
        
        return f"""
            QToolBar {{
                background: {ThemeManager.COLORS['surface']};
                border: none;
                {border_css}
                padding: 4px;
                spacing: 4px;
            }}

            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                color: {ThemeManager.COLORS['text']};
            }}

            QToolButton:hover {{
                background: {ThemeManager.COLORS['surface_lighter']};
            }}
            
            QToolButton:pressed {{
                background: {ThemeManager.COLORS['border']};
            }}
            
            QToolButton:checked {{
                background: {ThemeManager.COLORS['selection']};
                color: {ThemeManager.COLORS['white']};
            }}
        """

    @staticmethod
    def get_tab_widget_style():
        return f"""
            QTabWidget::pane {{
                border: none;
                background: {ThemeManager.COLORS['background']};
            }}
            
            QTabWidget::tab-bar {{
                left: 0;
            }}
            
            QTabBar::tab {{
                background: {ThemeManager.COLORS['surface']};
                color: {ThemeManager.COLORS['text_secondary']};
                padding: 8px 16px;
                border: none;
                border-right: 1px solid {ThemeManager.COLORS['background']};
                min-width: 80px;
            }}
            
            QTabBar::tab:hover {{
                background: {ThemeManager.COLORS['surface_light']};
                color: {ThemeManager.COLORS['text']};
            }}
            
            QTabBar::tab:selected {{
                background: {ThemeManager.COLORS['background']};
                color: {ThemeManager.COLORS['accent']};
                border-top: 2px solid {ThemeManager.COLORS['accent']};
            }}
            
            QTabBar::close-button {{
                image: url(close-icon.png); /* Need to handle icons */
                subcontrol-position: right;
            }}
        """

    @staticmethod
    def get_dock_widget_style():
        return f"""
            QDockWidget {{
                color: {ThemeManager.COLORS['text']};
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(undock.png);
            }}
            
            QDockWidget::title {{
                background-color: {ThemeManager.COLORS['surface']};
                padding: 8px;
                border-bottom: 1px solid {ThemeManager.COLORS['border']};
                font-weight: bold;
            }}
        """

    @staticmethod
    def get_button_style(variant="primary"):
        """Get stylesheet for QPushButton
        variant: 'primary', 'secondary', 'danger', 'icon'
        """
        if variant == "primary":
            bg = ThemeManager.COLORS['accent']
            bg_hover = ThemeManager.COLORS['accent_hover']
            bg_pressed = ThemeManager.COLORS['accent_pressed']
            text = ThemeManager.COLORS['white']
            border = "none"
        elif variant == "danger":
            bg = ThemeManager.COLORS['error']
            # Darken error color for hover roughly
            bg_hover = "#d66650"
            bg_pressed = "#b5402a"
            text = ThemeManager.COLORS['white']
            border = "none"
        elif variant == "icon":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ThemeManager.COLORS['text']};
                    border: 1px solid {ThemeManager.COLORS['border']};
                    padding: 4px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.COLORS['surface_lighter']};
                    border-color: {ThemeManager.COLORS['text_secondary']};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeManager.COLORS['border']};
                }}
            """
        else: # secondary/default
            bg = ThemeManager.COLORS['surface_light']
            bg_hover = ThemeManager.COLORS['surface_lighter']
            bg_pressed = ThemeManager.COLORS['border']
            text = ThemeManager.COLORS['text']
            border = f"1px solid {ThemeManager.COLORS['border']}"

        return f"""
            QPushButton {{
                background-color: {bg};
                color: {text};
                border: {border};
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {bg_pressed};
            }}
            QPushButton:disabled {{
                background-color: {ThemeManager.COLORS['surface']};
                color: {ThemeManager.COLORS['text_secondary']};
                border: 1px solid {ThemeManager.COLORS['border']};
            }}
        """

    @staticmethod
    def get_input_style():
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
                background-color: {ThemeManager.COLORS['surface']};
                color: {ThemeManager.COLORS['text']};
                border: 1px solid {ThemeManager.COLORS['border']};
                padding: 6px;
                border-radius: 4px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {ThemeManager.COLORS['accent']};
            }}
            
            QLineEdit:read-only {{
                background-color: {ThemeManager.COLORS['surface_lighter']};
                color: {ThemeManager.COLORS['text_secondary']};
            }}
        """

    @staticmethod
    def get_group_box_style():
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {ThemeManager.COLORS['border']};
                border-radius: 6px;
                margin-top: 20px;
                background-color: transparent;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: {ThemeManager.COLORS['text']};
            }}
        """
