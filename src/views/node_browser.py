"""
节点浏览器
显示官方支持的节点类型列表，并支持查看节点使用情况和工作流节点统计
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                               QLabel, QLineEdit, QPushButton, QHBoxLayout, QSplitter,
                               QAbstractItemView, QTabWidget, QFrame, QComboBox)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QDrag

from src.core.node_base import NodeType
from src.core.theme_manager import ThemeManager
from src.core.workflow_scanner import WorkflowScanner
from src.core.node_registry import NodeRegistry, NodeSource, NODE_SOURCE_INFO, get_registry


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
    # 信号：请求打开工作流并高亮节点
    open_workflow_requested = Signal(str, str, str)  # workflow_name, workflow_path, node_type
    # 信号：请求高亮当前工作流中的节点
    highlight_nodes_requested = Signal(str)  # node_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanner = WorkflowScanner()
        self._current_workflow_name = None
        self._setup_ui()
        self._load_nodes()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        title_label = QLabel("节点浏览器")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"padding: 8px; background-color: {ThemeManager.COLORS['surface_light']}; color: {ThemeManager.COLORS['text']};")
        layout.addWidget(title_label)
        
        # Tab切换
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {ThemeManager.COLORS['surface']};
            }}
            QTabBar::tab {{
                background-color: {ThemeManager.COLORS['surface_light']};
                color: {ThemeManager.COLORS['text_secondary']};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeManager.COLORS['text']};
                border-bottom: 2px solid {ThemeManager.COLORS['accent']};
            }}
            QTabBar::tab:hover {{
                color: {ThemeManager.COLORS['text']};
                background-color: {ThemeManager.COLORS['surface']};
            }}
        """)
        layout.addWidget(self.tab_widget)
        
        # Tab 1: 节点列表
        self._setup_node_list_tab()
        
        # Tab 2: 使用统计
        self._setup_usage_stats_tab()
    
    def _setup_node_list_tab(self):
        """设置节点列表Tab"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)
        
        # 工具栏：添加节点按钮 + 来源筛选
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加节点按钮
        self.add_node_btn = QPushButton("➕ 添加节点")
        self.add_node_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.add_node_btn.clicked.connect(self._on_add_node_clicked)
        toolbar_layout.addWidget(self.add_node_btn)
        
        toolbar_layout.addStretch()
        
        # 来源筛选下拉框
        self.source_filter = QComboBox()
        self.source_filter.addItems(["全部", "🏛️ 官方", "🐙 GitHub", "🏢 内网", "👤 自定义"])
        self.source_filter.setStyleSheet(ThemeManager.get_input_style())
        self.source_filter.setMinimumWidth(100)
        self.source_filter.currentIndexChanged.connect(self._on_source_filter_changed)
        toolbar_layout.addWidget(self.source_filter)
        
        tab_layout.addLayout(toolbar_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 0, 5, 5)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索节点...")
        self.search_input.textChanged.connect(self._filter_nodes)
        self.search_input.setStyleSheet(ThemeManager.get_input_style())
        search_layout.addWidget(self.search_input)
        
        tab_layout.addLayout(search_layout)
        
        # 使用Splitter分割节点列表和使用详情
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {ThemeManager.COLORS['border']};
                height: 2px;
            }}
        """)
        
        # 节点列表 - 使用自定义可拖拽列表
        self.node_list = DraggableListWidget()
        self.node_list.setStyleSheet(self._get_list_style())
        self.node_list.itemClicked.connect(self._on_node_clicked)
        self.node_list.itemDoubleClicked.connect(self._on_node_double_clicked)
        splitter.addWidget(self.node_list)
        
        # 节点使用详情区域
        usage_container = QWidget()
        usage_layout = QVBoxLayout(usage_container)
        usage_layout.setContentsMargins(5, 5, 5, 5)
        usage_layout.setSpacing(5)
        
        usage_title = QLabel("📋 节点使用情况")
        usage_title.setStyleSheet(f"color: {ThemeManager.COLORS['text']}; font-weight: bold; padding: 5px 0;")
        usage_layout.addWidget(usage_title)
        
        self.usage_list = QListWidget()
        self.usage_list.setStyleSheet(self._get_list_style())
        self.usage_list.itemDoubleClicked.connect(self._on_workflow_double_clicked)
        self.usage_list.setMinimumHeight(80)
        usage_layout.addWidget(self.usage_list)
        
        self.usage_hint = QLabel("点击上方节点查看使用情况\n双击工作流可打开并高亮节点")
        self.usage_hint.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt; padding: 5px;")
        self.usage_hint.setAlignment(Qt.AlignCenter)
        usage_layout.addWidget(self.usage_hint)
        
        splitter.addWidget(usage_container)
        
        # 设置Splitter初始比例
        splitter.setSizes([300, 150])
        
        tab_layout.addWidget(splitter)
        
        # 说明标签
        help_label = QLabel("双击或拖拽添加节点到画布")
        help_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt; padding: 5px;")
        help_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(help_label)
        
        self.tab_widget.addTab(tab_widget, "节点列表")
    
    def _setup_usage_stats_tab(self):
        """设置使用统计Tab"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)
        
        # 当前工作流标题
        self.workflow_title = QLabel("当前工作流: 无")
        self.workflow_title.setStyleSheet(f"color: {ThemeManager.COLORS['text']}; font-weight: bold; padding: 10px;")
        tab_layout.addWidget(self.workflow_title)
        
        # 节点使用统计列表
        self.stats_list = QListWidget()
        self.stats_list.setStyleSheet(self._get_list_style())
        self.stats_list.itemClicked.connect(self._on_stats_item_clicked)
        self.stats_list.itemDoubleClicked.connect(self._on_stats_item_double_clicked)
        tab_layout.addWidget(self.stats_list)
        
        # 空状态提示
        self.stats_empty_label = QLabel("打开一个工作流后，\n这里会显示节点使用统计")
        self.stats_empty_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 10pt; padding: 20px;")
        self.stats_empty_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(self.stats_empty_label)
        
        # 提示
        stats_hint = QLabel("点击查看详情，双击高亮节点")
        stats_hint.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt; padding: 5px;")
        stats_hint.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(stats_hint)
        
        self.tab_widget.addTab(tab_widget, "使用统计")
    
    def _get_list_style(self) -> str:
        """获取列表控件样式"""
        return f"""
            QListWidget {{
                background-color: {ThemeManager.COLORS['surface']};
                border: 1px solid {ThemeManager.COLORS['border']};
                color: {ThemeManager.COLORS['text']};
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {ThemeManager.COLORS['surface_light']};
            }}
            QListWidget::item:hover {{
                background-color: {ThemeManager.COLORS['surface_light']};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeManager.COLORS['selection']};
                color: {ThemeManager.COLORS['white']};
            }}
        """
    
    def _load_nodes(self):
        """加载节点列表"""
        # 从节点注册表加载节点
        self._registry = get_registry()
        self.nodes_data = self._registry.get_all_nodes()
        self._current_source_filter = None
        self._populate_list(self.nodes_data)
    
    def _populate_list(self, nodes):
        """填充节点列表"""
        self.node_list.clear()
        
        for node_data in nodes:
            item = QListWidgetItem()
            
            # 获取来源信息
            source = node_data.get('source', NodeSource.OFFICIAL)
            source_info = NODE_SOURCE_INFO.get(source, NODE_SOURCE_INFO[NodeSource.OFFICIAL])
            
            # 是否已修改
            is_modified = node_data.get('modified', False)
            modified_marker = " ⚡已修改" if is_modified else ""
            
            # 设置文本：来源标签 + 名称 + 修改标记 (不使用图标)
            source_tag = f"[{source_info['name']}]"
            text = f"{source_tag} {node_data['name']}{modified_marker}\n{node_data.get('description', '')}"
            item.setText(text)
            
            # 设置数据
            item.setData(Qt.UserRole, node_data)
            
            # 根据来源设置颜色
            if is_modified:
                item.setForeground(QColor("#FFC107"))  # 修改过的用黄色
            else:
                item.setForeground(QColor(source_info['color']))
            
            self.node_list.addItem(item)
    
    def _on_source_filter_changed(self, index):
        """来源筛选变化"""
        source_map = {
            0: None,  # 全部
            1: NodeSource.OFFICIAL,
            2: NodeSource.GITHUB,
            3: NodeSource.ENTERPRISE,
            4: NodeSource.CUSTOM,
        }
        self._current_source_filter = source_map.get(index)
        self._apply_filters()
    
    def _on_add_node_clicked(self):
        """添加节点按钮点击"""
        from src.dialogs.add_node_dialog import AddNodeDialog
        dialog = AddNodeDialog(self)
        if dialog.exec():
            # 刷新节点列表
            self._load_nodes()
    
    def _apply_filters(self):
        """应用筛选条件"""
        search_text = self.search_input.text().lower()
        
        filtered = []
        for node in self.nodes_data:
            # 来源筛选
            if self._current_source_filter is not None:
                if node.get('source') != self._current_source_filter:
                    continue
            
            # 搜索筛选
            if search_text:
                if (search_text not in node['name'].lower() and 
                    search_text not in node['description'].lower() and
                    search_text not in node['category'].lower()):
                    continue
            
            filtered.append(node)
        
        self._populate_list(filtered)
    
    def _filter_nodes(self, text):
        """过滤节点"""
        self._apply_filters()
    
    def _on_node_clicked(self, item):
        """节点被点击"""
        node_data = item.data(Qt.UserRole)
        # 获取节点类型字符串
        node_type_str = node_data.get('type_str', '')
        if node_data.get('type'):
            node_type_str = node_data['type'].value
        
        self.node_selected.emit(node_type_str, node_data)
        
        # 更新使用情况列表
        self._update_usage_list(node_type_str)
    
    def _update_usage_list(self, node_type: str):
        """更新节点使用情况列表"""
        self.usage_list.clear()
        
        workflows = self._scanner.get_workflows_using_node(node_type)
        
        if not workflows:
            self.usage_hint.setText("该节点暂未被任何工作流使用")
            self.usage_hint.show()
            return
        
        self.usage_hint.setText(f"被 {len(workflows)} 个工作流使用\n双击打开工作流")
        
        for wf_info in workflows:
            item = QListWidgetItem()
            item.setText(f"📁 {wf_info.workflow_name}  ({wf_info.count}次)")
            item.setData(Qt.UserRole, {
                "workflow_name": wf_info.workflow_name,
                "workflow_path": wf_info.workflow_path,
                "node_type": node_type,
                "node_ids": wf_info.node_ids
            })
            item.setForeground(QColor("#e0e0e0"))
            self.usage_list.addItem(item)
    
    def _on_workflow_double_clicked(self, item):
        """使用情况中的工作流被双击"""
        data = item.data(Qt.UserRole)
        if data:
            self.open_workflow_requested.emit(
                data["workflow_name"],
                data["workflow_path"],
                data["node_type"]
            )
    
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
    
    def _on_stats_item_clicked(self, item):
        """统计列表项被点击"""
        data = item.data(Qt.UserRole)
        if data:
            # 发送高亮请求
            self.highlight_nodes_requested.emit(data["node_type"])
    
    def _on_stats_item_double_clicked(self, item):
        """统计列表项被双击 - 高亮节点"""
        data = item.data(Qt.UserRole)
        if data:
            self.highlight_nodes_requested.emit(data["node_type"])
    
    def update_workflow_stats(self, workflow_name: str, nodes_data: list = None):
        """
        更新当前工作流的节点统计
        
        Args:
            workflow_name: 工作流名称，None表示无活跃工作流
            nodes_data: 可选的节点数据列表（如果提供则直接使用，否则从扫描器获取）
        """
        self._current_workflow_name = workflow_name
        self.stats_list.clear()
        
        if not workflow_name:
            self.workflow_title.setText("当前工作流: 无")
            self.stats_empty_label.show()
            self.stats_list.hide()
            return
        
        self.workflow_title.setText(f"当前工作流: {workflow_name}")
        
        # 获取节点统计
        if nodes_data is not None:
            # 从提供的数据构建统计
            usage_stats = self._build_stats_from_nodes(nodes_data)
        else:
            # 从扫描器获取
            usage_stats = self._scanner.get_nodes_in_workflow(workflow_name)
        
        if not usage_stats:
            self.stats_empty_label.setText("该工作流中暂无节点")
            self.stats_empty_label.show()
            self.stats_list.hide()
            return
        
        self.stats_empty_label.hide()
        self.stats_list.show()
        
        for usage_info in usage_stats:
            item = QListWidgetItem()
            count_text = f"×{usage_info.count}" if usage_info.count > 1 else ""
            item.setText(f"{usage_info.node_icon}  {usage_info.node_name}  {count_text}")
            item.setData(Qt.UserRole, {
                "node_type": usage_info.node_type,
                "node_ids": usage_info.node_ids
            })
            item.setForeground(QColor("#e0e0e0"))
            self.stats_list.addItem(item)
    
    def _build_stats_from_nodes(self, nodes_data: list) -> list:
        """从节点数据构建统计信息"""
        from src.core.workflow_scanner import NodeUsageInfo
        
        seen_types = {}
        usage_list = []
        
        for node in nodes_data:
            node_type = node.get('node_type', '')
            node_id = node.get('node_id', '')
            
            if node_type and node_id:
                if node_type in seen_types:
                    seen_types[node_type].count += 1
                    seen_types[node_type].node_ids.append(node_id)
                else:
                    info = self._scanner.get_node_info(node_type)
                    usage_info = NodeUsageInfo(
                        node_type=node_type,
                        node_name=info["name"],
                        node_icon=info["icon"],
                        count=1,
                        node_ids=[node_id]
                    )
                    seen_types[node_type] = usage_info
                    usage_list.append(usage_info)
        
        return usage_list
    
    def refresh_node_usage(self):
        """刷新节点使用情况（重新扫描工作流目录）"""
        self._scanner.scan_all_workflows()
        
        # 如果当前有选中的节点，刷新使用列表
        current_item = self.node_list.currentItem()
        if current_item:
            node_data = current_item.data(Qt.UserRole)
            if node_data:
                self._update_usage_list(node_data['type'].value)
        
        # 刷新当前工作流统计
        if self._current_workflow_name:
            self.update_workflow_stats(self._current_workflow_name)
