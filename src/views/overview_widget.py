from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                               QScrollArea, QGridLayout, QFrame, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont
import os
import json
import shutil
import sys
from pathlib import Path


class WorkflowCard(QFrame):
    """工作流卡片"""
    
    open_clicked = Signal(str, str)  # workflow_name, workflow_path
    delete_clicked = Signal(str)  # workflow_name
    
    def __init__(self, workflow_name: str, workflow_path: str, parent=None):
        super().__init__(parent)
        self.workflow_name = workflow_name
        self.workflow_path = workflow_path
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(220, 180)
        self.setStyleSheet("""
            WorkflowCard {
                background-color: #2d2d2d;
                border: 1px solid #3f3f3f;
                border-radius: 8px;
            }
            WorkflowCard:hover {
                border: 1px solid #0e639c;
                background-color: #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 图标
        icon_label = QLabel("📊")
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 工作流名称
        name_label = QLabel(self.workflow_name)
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #e0e0e0;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # 打开按钮
        open_btn = QPushButton("打开")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        open_btn.clicked.connect(lambda: self.open_clicked.emit(self.workflow_name, self.workflow_path))
        button_layout.addWidget(open_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.workflow_name))
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()


class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
        self._load_workflows()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 头部区域
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(10)
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(self._get_resource_path("assets/localflow_64.png"))
        logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("欢迎使用 LocalFlow")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        main_layout.addWidget(header_widget)
        
        # 工作流列表标题和按钮
        list_header = QWidget()
        list_header_layout = QHBoxLayout(list_header)
        list_header_layout.setContentsMargins(0, 0, 0, 0)
        
        workflows_title = QLabel("我的工作流")
        workflows_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e0e0e0;
            }
        """)
        list_header_layout.addWidget(workflows_title)
        
        list_header_layout.addStretch()
        
        # Add Workflow Button
        add_workflow_btn = QPushButton("+ 新建工作流")
        add_workflow_btn.setFixedHeight(40)
        add_workflow_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        add_workflow_btn.clicked.connect(self._on_add_workflow_clicked)
        list_header_layout.addWidget(add_workflow_btn)
        
        main_layout.addWidget(list_header)
        
        # 工作流卡片滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 工作流卡片容器
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # 空状态提示
        self.empty_label = QLabel("暂无工作流\n点击上方按钮创建新工作流")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #888888;
                padding: 40px;
            }
        """)
        self.cards_layout.addWidget(self.empty_label, 0, 0, Qt.AlignCenter)
        
        scroll.setWidget(self.cards_widget)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
    
    def _get_resource_path(self, relative_path):
        """获取资源文件的绝对路径，支持开发和打包环境"""
        # 开发环境
        dev_path = Path(relative_path)
        if dev_path.exists():
            return str(dev_path)
        
        # 打包环境（PyInstaller）
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
            resource_path = base_path / relative_path
        else:
            # 如果是其他情况，尝试相对于可执行文件
            base_path = Path(sys.executable).parent
            resource_path = base_path / relative_path
            
            # 如果在_internal目录中，需要调整路径
            if not resource_path.exists():
                internal_path = base_path.parent / "_internal" / relative_path
                if internal_path.exists():
                    resource_path = internal_path
        
        # 如果资源文件存在，返回路径
        if resource_path.exists():
            return str(resource_path)
        
        # 最后的备选方案
        return relative_path
    
    def _load_workflows(self):
        """加载已保存的工作流"""
        workflows_dir = Path("workflows")
        
        if not workflows_dir.exists():
            return
        
        workflow_list = []
        
        # 遍历workflows目录
        for item in workflows_dir.iterdir():
            if item.is_dir():
                workflow_json = item / "workflow.json"
                if workflow_json.exists() and workflow_json.is_file():
                    # 验证文件是否可读且包含有效的工作流数据
                    try:
                        with open(workflow_json, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict) and 'workflow_name' in data:
                                workflow_list.append({
                                    "name": item.name,
                                    "path": str(workflow_json)
                                })
                    except (json.JSONDecodeError, IOError) as e:
                        print(f"跳过损坏的工作流文件: {workflow_json} - {e}")
        
        # 安全地清空现有卡片
        # 先收集所有需要删除的widget（除了empty_label）
        widgets_to_remove = []
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and widget != self.empty_label:
                    widgets_to_remove.append(widget)
        
        # 从布局中移除并删除
        for widget in widgets_to_remove:
            self.cards_layout.removeWidget(widget)
            widget.deleteLater()
        
        # 如果有工作流，显示卡片
        if workflow_list:
            # 确保empty_label从布局中移除并隐藏
            if self.empty_label in [self.cards_layout.itemAt(i).widget() 
                                     for i in range(self.cards_layout.count()) 
                                     if self.cards_layout.itemAt(i) and self.cards_layout.itemAt(i).widget()]:
                self.cards_layout.removeWidget(self.empty_label)
            self.empty_label.hide()
            
            # 创建工作流卡片（每行4个）
            for i, workflow in enumerate(workflow_list):
                card = WorkflowCard(workflow["name"], workflow["path"], self)
                card.open_clicked.connect(self._on_open_workflow)
                card.delete_clicked.connect(self._on_delete_workflow)
                
                row = i // 4
                col = i % 4
                self.cards_layout.addWidget(card, row, col)
        else:
            # 显示空状态
            # 检查empty_label是否已经在布局中
            if self.empty_label not in [self.cards_layout.itemAt(i).widget() 
                                         for i in range(self.cards_layout.count()) 
                                         if self.cards_layout.itemAt(i) and self.cards_layout.itemAt(i).widget()]:
                self.cards_layout.addWidget(self.empty_label, 0, 0, Qt.AlignCenter)
            self.empty_label.show()
    
    def _on_open_workflow(self, workflow_name: str, workflow_path: str):
        """打开工作流"""
        print(f"打开工作流: {workflow_name} - {workflow_path}")
        
        # 检查文件是否存在，如果不存在则刷新列表并提示用户
        if not os.path.exists(workflow_path):
            print(f"工作流文件不存在: {workflow_path}")
            self._load_workflows()  # 刷新列表
            QMessageBox.warning(self, "文件不存在", 
                              f"工作流 '{workflow_name}' 的文件不存在。\n\n可能已被重命名或删除。\n工作流列表已刷新。")
            return
        
        if self.parent:
            # 创建新的工作流标签页
            from src.views.workflow_tab_widget import WorkflowTabWidget
            from src.core.workflow_executor import WorkflowExecutor
            from src.core.uv_manager import UVManager
            
            # 加载工作流数据
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                # 创建工作流标签页
                workflow_widget = WorkflowTabWidget(workflow_name, self.parent)
                
                # 加载节点到画布
                from src.views.node_graphics import NodeGraphicsItem
                from src.core.node_base import NodeType
                
                # 节点类型映射
                node_type_map = {
                    "variable_assign": NodeType.VARIABLE_ASSIGN,
                    "variable_calc": NodeType.VARIABLE_CALC,
                    "sqlite_connect": NodeType.SQLITE_CONNECT,
                    "sqlite_execute": NodeType.SQLITE_EXECUTE,
                    "sql_statement": NodeType.SQL_STATEMENT,
                }
                
                # 添加节点
                for node_data in workflow_data.get("nodes", []):
                    node_id = node_data["node_id"]
                    node_type_str = node_data["node_type"]
                    node_type = node_type_map.get(node_type_str)
                    
                    if node_type:
                        node_item = NodeGraphicsItem(node_id, node_type, node_type.value)
                        node_item.config = node_data.get("config", {})
                        
                        # 设置位置（如果有的话）
                        pos = node_data.get("position", {"x": 0, "y": 0})
                        node_item.setPos(pos.get("x", 0), pos.get("y", 0))
                        
                        # 添加到场景
                        workflow_widget.canvas._scene.addItem(node_item)
                        workflow_widget.nodes[node_id] = node_item
                
                # 添加连接
                for from_id, to_id in workflow_data.get("edges", []):
                    workflow_widget.connections.append((from_id, to_id))
                    
                    # 创建可视化连接线
                    if from_id in workflow_widget.nodes and to_id in workflow_widget.nodes:
                        from_node = workflow_widget.nodes[from_id]
                        to_node = workflow_widget.nodes[to_id]
                        
                        if from_node.output_ports and to_node.input_ports:
                            from src.views.node_graphics import ConnectionGraphicsItem
                            connection = ConnectionGraphicsItem(
                                from_node.output_ports[0],
                                to_node.input_ports[0]
                            )
                            workflow_widget.canvas._scene.addItem(connection)
                
                # 添加标签页
                index = self.parent.tabs.addTab(workflow_widget, workflow_name)
                self.parent.tabs.setCurrentIndex(index)
                
                print(f"工作流已加载: {len(workflow_data.get('nodes', []))} 个节点")
                
            except Exception as e:
                print(f"加载工作流失败: {e}")
                import traceback
                traceback.print_exc()
                
                QMessageBox.critical(self, "加载失败", f"无法加载工作流:\n{str(e)}")
    
    def _on_delete_workflow(self, workflow_name: str):
        """删除工作流"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除工作流 '{workflow_name}' 吗？\n此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                workflow_dir = Path("workflows") / workflow_name
                if workflow_dir.exists():
                    shutil.rmtree(workflow_dir)
                    print(f"工作流已删除: {workflow_name}")
                    
                    QMessageBox.information(self, "删除成功", f"工作流 '{workflow_name}' 已删除")
                else:
                    QMessageBox.warning(self, "删除失败", f"工作流 '{workflow_name}' 不存在")
                    
            except Exception as e:
                print(f"删除失败: {e}")
                QMessageBox.critical(self, "删除失败", f"无法删除工作流:\n{str(e)}")
            finally:
                # 无论成功与否，都刷新列表
                self._load_workflows()
    
    def refresh_workflows(self):
        """刷新工作流列表"""
        self._load_workflows()
    
    def _on_add_workflow_clicked(self):
        # Notify the parent to add a new workflow tab
        if self.parent:
            self.parent.add_workflow_tab()
