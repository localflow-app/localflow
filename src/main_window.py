from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QToolBar, QTabWidget, QStatusBar, QSizePolicy
from PySide6.QtCore import Qt, QSize

from src.views.overview_widget import OverviewWidget
from src.views.workflow_tab_widget import WorkflowTabWidget
from src.dialogs.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalFlow")
        self.setGeometry(300, 150, 785, 603)
        self.setWindowIcon(QIcon("assets/localflow_64.png"))
        self.workflow_count = 0

        self._setup_layout()

    def _setup_layout(self):

        # Left Area
        toolbar = QToolBar("LeftToolbar", self)
        toolbar.setOrientation(Qt.Vertical)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        # ToolButtonIconOnly means only show icon, no text
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("padding: 5px; margin: 0px;")
        self.setToolbarStyle(toolbar, "LeftToolbar")

        action_note = toolbar.addAction(QIcon("assets/icons/node.png"), "Node")
        
        # Add spacer to push settings button to bottom
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Add settings button at bottom
        action_settings = toolbar.addAction(QIcon("assets/icons/settings.png"), "Settings")
        action_settings.triggered.connect(self._open_settings)

        # Center Area
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create Overview Tab
        overview_widget = OverviewWidget(self)
        self.tabs.addTab(overview_widget, "Overview")

        # Right Area
        # Left Area
        toolbar_right = QToolBar("LeftToolbar", self)
        toolbar_right.setOrientation(Qt.Vertical)
        toolbar_right.setMovable(False)
        toolbar_right.setFloatable(False)
        # ToolButtonIconOnly means only show icon, no text
        toolbar_right.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar_right.setIconSize(QSize(24, 24))
        toolbar_right.setStyleSheet("padding: 5px; margin: 0px;")
        self.setToolbarStyle(toolbar_right, "RightToolbar")

        # Button Area
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        action_note = toolbar_right.addAction(QIcon("assets/icons/detail.png"), "Detail")

        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        self.addToolBar(Qt.RightToolBarArea, toolbar_right)

    def setToolbarStyle(self, toolbar, param):
        if param == "LeftToolbar":
            toolbar.setStyleSheet("""
            QToolBar {
                border: none;
                border-right: 1px solid #111111;
                background: transparent;
                padding: 6px;
            }

            QToolBar::handle {
                image: none;
            }

            QToolBar::separator {
                background: none;
                width: 0px;
                height: 0px;
            }

            QToolButton {
                border: none;
                padding: 6px;
            }

            QToolButton:hover {
                background: rgba(0, 0, 0, 0.06);
                border-radius: 6px;
            }
            """)
        elif param == "RightToolbar":
            toolbar.setStyleSheet("""
            QToolBar {
                border: none;
                border-left: 1px solid #111111;
                background: transparent;
                padding: 6px;
            }

            QToolBar::handle {
                image: none;
            }

            QToolBar::separator {
                background: none;
                width: 0px;
                height: 0px;
            }

            QToolButton {
                border: none;
                padding: 6px;
            }

            QToolButton:hover {
                background: rgba(0, 0, 0, 0.06);
                border-radius: 6px;
            }
            """)
    
    def add_workflow_tab(self):
        """Add a new workflow tab"""
        self.workflow_count += 1
        workflow_name = f"工作流 {self.workflow_count}"
        workflow_widget = WorkflowTabWidget(workflow_name, self)
        
        # Add the new workflow tab
        index = self.tabs.addTab(workflow_widget, workflow_name)
        
        # Change the current tab to the new one
        self.tabs.setCurrentIndex(index)
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()