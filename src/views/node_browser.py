"""
节点浏览器
显示官方支持的节点类型列表
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                               QLabel, QLineEdit, QPushButton, QHBoxLayout, QSplitter,
                               QAbstractItemView)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QDrag

from src.core.node_base import NodeType


class DraggableListWidget(QListWidget):
    """支持拖拽的列表控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
    
    def startDrag(self, supportedActions):
        """开始拖拽"""
        item = self.currentItem()
        if not item:
            return
        
        node_data = item.data(Qt.UserRole)
        if not node_data:
            return
        
        # 创建拖拽对象
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 设置节点类型数据
        mime_data.setText(node_data['type'].value)
        drag.setMimeData(mime_data)
        
        # 执行拖拽
        drag.exec_(Qt.CopyAction)


class NodeBrowserWidget(QWidget):
    """节点浏览器面板"""
    
    # 信号：节点被选中
    node_selected = Signal(str, dict)  # node_type, node_info
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_nodes()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("节点浏览器")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("padding: 8px; background-color: #2d2d2d; color: #e0e0e0;")
        layout.addWidget(title_label)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索节点...")
        self.search_input.textChanged.connect(self._filter_nodes)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # 节点列表 - 使用自定义可拖拽列表
        self.node_list = DraggableListWidget()
        self.node_list.setStyleSheet("""
            QListWidget {
                background-color: #252525;
                border: 1px solid #3f3f3f;
                color: #e0e0e0;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2d2d2d;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
                color: white;
            }
        """)
        self.node_list.itemClicked.connect(self._on_node_clicked)
        self.node_list.itemDoubleClicked.connect(self._on_node_double_clicked)
        layout.addWidget(self.node_list)
        
        # 说明标签
        help_label = QLabel("双击或拖拽添加节点到画布")
        help_label.setStyleSheet("color: #888888; font-size: 9pt; padding: 5px;")
        help_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(help_label)
    
    def _load_nodes(self):
        """加载节点列表"""
        self.nodes_data = [
            {
                "type": NodeType.VARIABLE_ASSIGN,
                "name": "变量赋值",
                "description": "创建变量并赋值",
                "icon": "📝",
                "color": "#4CAF50",
                "category": "变量操作"
            },
            {
                "type": NodeType.VARIABLE_CALC,
                "name": "变量计算",
                "description": "使用表达式计算变量",
                "icon": "🔢",
                "color": "#2196F3",
                "category": "变量操作"
            },
            {
                "type": NodeType.SQLITE_CONNECT,
                "name": "SQLite连接",
                "description": "连接SQLite数据库",
                "icon": "🔌",
                "color": "#FF9800",
                "category": "数据库"
            },
            {
                "type": NodeType.SQL_STATEMENT,
                "name": "SQL语句",
                "description": "构建SQL查询语句",
                "icon": "📄",
                "color": "#00BCD4",
                "category": "数据库"
            },
            {
                "type": NodeType.SQLITE_EXECUTE,
                "name": "SQLite执行",
                "description": "执行SQL语句",
                "icon": "▶️",
                "color": "#9C27B0",
                "category": "数据库"
            }
        ]
        
        self._populate_list(self.nodes_data)
    
    def _populate_list(self, nodes):
        """填充节点列表"""
        self.node_list.clear()
        
        for node_data in nodes:
            item = QListWidgetItem()
            
            # 设置文本
            text = f"{node_data['icon']}  {node_data['name']}\n   {node_data['description']}"
            item.setText(text)
            
            # 设置数据
            item.setData(Qt.UserRole, node_data)
            
            # 设置颜色标记
            item.setForeground(QColor("#e0e0e0"))
            
            self.node_list.addItem(item)
    
    def _filter_nodes(self, text):
        """过滤节点"""
        if not text:
            self._populate_list(self.nodes_data)
            return
        
        filtered = [
            node for node in self.nodes_data
            if text.lower() in node['name'].lower() or 
               text.lower() in node['description'].lower() or
               text.lower() in node['category'].lower()
        ]
        
        self._populate_list(filtered)
    
    def _on_node_clicked(self, item):
        """节点被点击"""
        node_data = item.data(Qt.UserRole)
        self.node_selected.emit(node_data['type'].value, node_data)
    
    def _on_node_double_clicked(self, item):
        """节点被双击"""
        node_data = item.data(Qt.UserRole)
        print(f"双击节点: {node_data['name']}")
        
        # 通知主窗口添加节点到画布中心
        # 向上查找主窗口
        widget = self.parent()
        while widget:
            if hasattr(widget, 'add_node_to_canvas'):
                widget.add_node_to_canvas(node_data['type'])
                break
            widget = widget.parent() if hasattr(widget, 'parent') else None
