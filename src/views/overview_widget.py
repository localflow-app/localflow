from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel("欢迎使用 LocalFlow")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 20px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add Workflow Button
        add_workflow_btn = QPushButton("添加工作流")
        add_workflow_btn.setFixedSize(200, 50)
        add_workflow_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        add_workflow_btn.clicked.connect(self._on_add_workflow_clicked)
        layout.addWidget(add_workflow_btn, alignment=Qt.AlignCenter)
        
        # Description
        info_label = QLabel("点击按钮创建新的工作流")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
                margin-top: 10px;
            }
        """)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def _on_add_workflow_clicked(self):
        # Notify the parent to add a new workflow tab
        if self.parent:
            self.parent.add_workflow_tab()