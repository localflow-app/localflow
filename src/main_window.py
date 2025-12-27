from PySide6.QtGui import QIcon, QAction
from pathlib import Path
import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QToolBar, QTabWidget, QStatusBar, QSizePolicy, QDockWidget
from PySide6.QtCore import Qt, QSize

from src.views.overview_widget import OverviewWidget
from src.views.workflow_tab_widget import WorkflowTabWidget
from src.dialogs.settings_dialog import SettingsDialog
from src.views.node_browser import NodeBrowserWidget
from src.views.node_properties import NodePropertiesWidget
from src.core.config_manager import ConfigManager

from src.core.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalFlow")
        self.setGeometry(300, 150, 785, 603)
        self.setWindowIcon(QIcon(self._get_resource_path("assets/localflow_64.png")))
        self.workflow_count = 0
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        self._setup_layout()
        self._restore_window_state()

    def _setup_layout(self):

        # Left Toolbar
        toolbar = QToolBar("LeftToolbar", self)
        toolbar.setOrientation(Qt.Vertical)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setIconSize(QSize(24, 24))
        # Use ThemeManager for toolbar style
        toolbar.setStyleSheet(ThemeManager.get_toolbar_style("right"))
        
        # 节点浏览器按钮
        action_node_browser = toolbar.addAction(QIcon(self._get_resource_path("assets/icons/node.png")), "节点浏览器")
        action_node_browser.triggered.connect(self._toggle_node_browser)
        
        # Add spacer to push settings button to bottom
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # Add settings button at bottom
        action_settings = toolbar.addAction(QIcon(self._get_resource_path("assets/icons/settings.png")), "Settings")
        action_settings.triggered.connect(self._open_settings)

        # Center Area - Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)  # 启用关闭按钮
        self.tabs.setMovable(True)  # 允许拖动标签
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self._show_tab_context_menu)
        # Use ThemeManager for tab style
        self.tabs.setStyleSheet(ThemeManager.get_tab_widget_style())
        self.setCentralWidget(self.tabs)
        
        # Create Overview Tab
        overview_widget = OverviewWidget(self)
        self.tabs.addTab(overview_widget, "Overview")

        # Right Toolbar
        toolbar_right = QToolBar("RightToolbar", self)
        toolbar_right.setOrientation(Qt.Vertical)
        toolbar_right.setMovable(False)
        toolbar_right.setFloatable(False)
        toolbar_right.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar_right.setIconSize(QSize(24, 24))
        # Use ThemeManager for toolbar style
        toolbar_right.setStyleSheet(ThemeManager.get_toolbar_style("left"))
        
        # 节点属性按钮
        action_node_props = toolbar_right.addAction(QIcon(self._get_resource_path("assets/icons/detail.png")), "节点属性")
        action_node_props.triggered.connect(self._toggle_node_properties)

        # Status Bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        self.addToolBar(Qt.RightToolBarArea, toolbar_right)
        
        # 左侧停靠窗口 - 节点浏览器
        self.node_browser_dock = QDockWidget("节点浏览器", self)
        self.node_browser_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.node_browser = NodeBrowserWidget(self)
        self.node_browser_dock.setWidget(self.node_browser)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.node_browser_dock)
        self.node_browser_dock.hide()  # 默认隐藏
        
        # 右侧停靠窗口 - 节点属性
        self.node_properties_dock = QDockWidget("节点属性", self)
        self.node_properties_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.node_properties = NodePropertiesWidget(self)
        self.node_properties_dock.setWidget(self.node_properties)
        self.addDockWidget(Qt.RightDockWidgetArea, self.node_properties_dock)
        self.node_properties_dock.hide()  # 默认隐藏
        
        # 连接信号
        self.node_properties.properties_updated.connect(self._on_node_properties_updated)
        
        # 连接节点浏览器信号
        self.node_browser.open_workflow_requested.connect(self._on_open_workflow_from_browser)
        self.node_browser.highlight_nodes_requested.connect(self._on_highlight_nodes_requested)
        
        # 切换Tab时更新节点浏览器统计
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # 应用停靠窗口样式
        dock_style = ThemeManager.get_dock_widget_style()
        self.node_browser_dock.setStyleSheet(dock_style)
        self.node_properties_dock.setStyleSheet(dock_style)
        
        # 恢复dock窗口状态
        self._restore_dock_states()
        
        # 安装事件过滤器来监听dock窗口大小变化
        self.node_browser_dock.installEventFilter(self)
        self.node_properties_dock.installEventFilter(self)
    
    def _toggle_node_browser(self):
        """切换节点浏览器显示"""
        if self.node_browser_dock.isVisible():
            self.node_browser_dock.hide()
        else:
            self.node_browser_dock.show()
    
    def _toggle_node_properties(self):
        """切换节点属性显示"""
        if self.node_properties_dock.isVisible():
            self.node_properties_dock.hide()
        else:
            self.node_properties_dock.show()
    
    def _on_node_properties_updated(self, node_id: str, config: dict):
        """节点属性已更新"""
        # 获取当前工作流标签页
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, WorkflowTabWidget):
            current_widget.update_node_config(node_id, config)
    
    def _on_open_workflow_from_browser(self, workflow_name: str, workflow_path: str, node_type: str):
        """从节点浏览器请求打开工作流"""
        # 检查工作流是否已经打开
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, WorkflowTabWidget) and widget.workflow_name == workflow_name:
                # 已经打开，切换到该标签并高亮节点
                self.tabs.setCurrentIndex(i)
                widget.canvas.highlight_nodes_by_type(node_type)
                return
        
        # 需要打开工作流，复用OverviewWidget的逻辑
        overview_widget = self.tabs.widget(0)
        if hasattr(overview_widget, '_on_open_workflow'):
            overview_widget._on_open_workflow(workflow_name, workflow_path)
            
            # 等待工作流打开后高亮节点
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._highlight_after_open(node_type))
    
    def _highlight_after_open(self, node_type: str):
        """工作流打开后高亮节点"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, WorkflowTabWidget):
            current_widget.canvas.highlight_nodes_by_type(node_type)
    
    def _on_highlight_nodes_requested(self, node_type: str):
        """处理高亮节点请求"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, WorkflowTabWidget):
            current_widget.canvas.highlight_nodes_by_type(node_type)
    
    def _on_tab_changed(self, index: int):
        """Tab切换时更新节点浏览器统计"""
        widget = self.tabs.widget(index)
        if isinstance(widget, WorkflowTabWidget):
            # 获取工作流中的节点数据
            nodes_data = widget.canvas.get_all_nodes()
            self.node_browser.update_workflow_stats(widget.workflow_name, nodes_data)
        else:
            # 非工作流标签（如Overview）
            self.node_browser.update_workflow_stats(None)

    def add_workflow_tab(self):
        """Add a new workflow tab"""
        self.workflow_count += 1
        workflow_name = f"工作流 {self.workflow_count}"
        workflow_widget = WorkflowTabWidget(workflow_name, self)
        
        # 连接工作流的修改信号
        workflow_widget.modified_changed.connect(self._on_workflow_modified)
        
        # Add the new workflow tab
        index = self.tabs.addTab(workflow_widget, workflow_name)
        
        # Change the current tab to the new one
        self.tabs.setCurrentIndex(index)
    
    def _close_tab(self, index):
        """关闭指定标签页"""
        # 不允许关闭Overview标签（第0个）
        if index == 0:
            return
        
        widget = self.tabs.widget(index)
        if isinstance(widget, WorkflowTabWidget):
            if not self._check_save_before_close(widget):
                return  # 用户取消关闭
        
        self.tabs.removeTab(index)
        widget.deleteLater()
    
    def _show_tab_context_menu(self, pos):
        """显示标签页右键菜单"""
        # 获取点击的标签索引
        tab_bar = self.tabs.tabBar()
        index = tab_bar.tabAt(pos)
        
        if index < 0 or index == 0:  # 无效索引或Overview标签
            return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3f3f3f;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
        """)
        
        close_action = menu.addAction("关闭当前")
        rename_action = menu.addAction("重命名")
        close_others_action = menu.addAction("关闭其他")
        close_all_action = menu.addAction("关闭所有")
        
        action = menu.exec_(tab_bar.mapToGlobal(pos))
        
        if action == close_action:
            self._close_tab(index)
        elif action == rename_action:
            self._rename_tab(index)
        elif action == close_others_action:
            self._close_other_tabs(index)
        elif action == close_all_action:
            self._close_all_tabs()
    
    def _close_other_tabs(self, keep_index):
        """关闭除指定标签外的其他标签"""
        # 从后向前关闭，避免索引变化
        for i in range(self.tabs.count() - 1, 0, -1):
            if i != keep_index:
                self._close_tab(i)
    
    def _close_all_tabs(self):
        """关闭所有工作流标签（除了Overview）"""
        # 从后向前关闭
        for i in range(self.tabs.count() - 1, 0, -1):
            self._close_tab(i)
    
    def _check_save_before_close(self, workflow_widget):
        """关闭前检查是否需要保存
        
        Returns:
            bool: True表示可以继续关闭，False表示用户取消关闭
        """
        if not workflow_widget.is_modified():
            return True
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "保存工作流",
            f"工作流 '{workflow_widget.workflow_name}' 有未保存的更改。\n是否保存？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            workflow_widget._save_workflow()
            return True
        elif reply == QMessageBox.Discard:
            return True
        else:  # Cancel
            return False
    
    def _on_workflow_modified(self, is_modified):
        """工作流修改状态改变"""
        sender_widget = self.sender()
        if not sender_widget:
            return
        
        # 找到对应的标签索引
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == sender_widget:
                workflow_name = sender_widget.workflow_name
                if is_modified:
                    self.tabs.setTabText(i, f"{workflow_name} *")
                else:
                    self.tabs.setTabText(i, workflow_name)
                break
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查所有工作流是否有未保存的更改
        for i in range(1, self.tabs.count()):  # 跳过Overview
            widget = self.tabs.widget(i)
            if isinstance(widget, WorkflowTabWidget):
                if not self._check_save_before_close(widget):
                    event.ignore()
                    return
        
        # 保存窗口和dock状态
        geometry = self.geometry()
        self.config_manager.set_window_geometry(
            geometry.x(), geometry.y(), 
            geometry.width(), geometry.height()
        )
        
        self._save_dock_states()
        self.config_manager.save_config()
        
        event.accept()
    
    def eventFilter(self, obj, event):
        """事件过滤器，监听dock窗口的大小变化"""
        from PySide6.QtCore import QEvent
        
        # 监听dock窗口的Resize事件
        if event.type() == QEvent.Resize:
            if obj in [self.node_browser_dock, self.node_properties_dock]:
                # 使用定时器延迟保存，避免频繁保存
                if not hasattr(self, '_dock_save_timer'):
                    from PySide6.QtCore import QTimer
                    self._dock_save_timer = QTimer(self)
                    self._dock_save_timer.setSingleShot(True)
                    self._dock_save_timer.timeout.connect(self._save_dock_states)
                
                self._dock_save_timer.start(500)  # 500ms后保存
        
        return super().eventFilter(obj, event)
    
    def add_node_to_canvas(self, node_type):
        """添加节点到当前画布的中心位置"""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, WorkflowTabWidget):
            from src.views.node_graphics import NodeGraphicsItem
            import time
            
            from src.core.node_base import NodeType
            node_title_map = {
                NodeType.VARIABLE_ASSIGN: "变量赋值",
                NodeType.VARIABLE_CALC: "变量计算",
                NodeType.SQLITE_CONNECT: "SQLite连接",
                NodeType.SQLITE_EXECUTE: "SQLite执行",
                NodeType.SQL_STATEMENT: "SQL语句",
            }
            
            node_title = node_title_map.get(node_type, node_type.value)
            
            # 生成唯一ID
            node_id = f"node_{int(time.time() * 1000)}"
            
            # 创建节点
            node_item = NodeGraphicsItem(node_id, node_type, node_title)
            
            # 获取画布中心位置（场景坐标）
            canvas = current_widget.canvas
            view_center = canvas.viewport().rect().center()
            scene_center = canvas.mapToScene(view_center)
            
            # 设置节点位置（考虑节点大小，使其居中）
            node_item.setPos(scene_center.x() - node_item.width / 2, 
                           scene_center.y() - node_item.height / 2)
            
            # 添加到场景
            canvas._scene.addItem(node_item)
            
            # 触发节点添加信号（这会触发修改标识）
            canvas.node_added.emit(node_item)
            
            print(f"添加节点到画布中心: {node_title} ({node_id})")
    
    def _rename_tab(self, index):
        """重命名指定标签页"""
        if index <= 0:  # 不允许重命名Overview标签
            return
        
        widget = self.tabs.widget(index)
        if isinstance(widget, WorkflowTabWidget):
            widget.rename_workflow()
    
    def update_tab_name(self, workflow_widget, new_name):
        """更新标签页名称
        
        Args:
            workflow_widget: WorkflowTabWidget实例
            new_name: 新的工作流名称
        """
        # 找到对应的标签索引
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == workflow_widget:
                # 更新标签文本，考虑修改状态
                current_text = self.tabs.tabText(i)
                if current_text.endswith(" *"):
                    self.tabs.setTabText(i, f"{new_name} *")
                else:
                    self.tabs.setTabText(i, new_name)
                break
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        geometry = self.config_manager.get_window_geometry()
        if geometry:
            x, y, width, height = geometry.get("x", 300), geometry.get("y", 150), \
                                    geometry.get("width", 785), geometry.get("height", 603)
            self.setGeometry(x, y, width, height)
    
    def _restore_dock_states(self):
        """恢复dock窗口状态"""
        # 恢复节点浏览器dock状态
        self.config_manager.apply_dock_state(self.node_browser_dock, "node_browser")
        
        # 恢复节点属性dock状态
        self.config_manager.apply_dock_state(self.node_properties_dock, "node_properties")
    
    def _save_dock_states(self):
        """保存dock窗口状态"""
        # 保存节点浏览器dock状态
        self.config_manager.save_dock_state(self.node_browser_dock, "node_browser")
        
        # 保存节点属性dock状态
        self.config_manager.save_dock_state(self.node_properties_dock, "node_properties")
    
    def _toggle_node_browser(self):
        """切换节点浏览器显示"""
        if self.node_browser_dock.isVisible():
            self.node_browser_dock.hide()
        else:
            self.node_browser_dock.show()
        
        # 实时保存状态
        self._save_dock_states()
    
    def _toggle_node_properties(self):
        """切换节点属性显示"""
        if self.node_properties_dock.isVisible():
            self.node_properties_dock.hide()
        else:
            self.node_properties_dock.show()
        
        # 实时保存状态
        self._save_dock_states()
    
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
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()