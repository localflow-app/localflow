import sys

from PySide6.QtWidgets import QApplication

from src.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply global theme
    from src.core.theme_manager import ThemeManager
    ThemeManager.apply_theme(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())