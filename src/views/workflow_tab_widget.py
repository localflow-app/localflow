from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from .workflow_canvas import WorkflowCanvas, WorkflowGraphicsScene

class WorkflowTabWidget(QWidget):
    def __init__(self, workflow_name="新工作流", parent=None):
        super().__init__(parent)
        self.workflow_name = workflow_name
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create a new scene
        scene = WorkflowGraphicsScene(self)
        self.canvas = WorkflowCanvas(scene, self)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def get_workflow_name(self):
        return self.workflow_name