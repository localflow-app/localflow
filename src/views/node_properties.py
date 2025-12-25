"""
节点属性面板
用于编辑选中节点的属性
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QComboBox, QTextEdit, QPushButton,
                               QScrollArea, QGroupBox, QHBoxLayout, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from src.core.node_base import NodeType
from src.core.theme_manager import ThemeManager


class NodePropertiesWidget(QWidget):
    """节点属性面板"""
    
    # 信号：属性已更新
    properties_updated = Signal(str, dict)  # node_id, config
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_node_id = None
        self.current_node_type = None
        self._pending_load = None  # 待加载的节点数据
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._do_load_node_properties)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        title_label = QLabel("节点属性")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"padding: 8px; background-color: {ThemeManager.COLORS['surface_light']}; color: {ThemeManager.COLORS['text']};")
        layout.addWidget(title_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {ThemeManager.COLORS['background']};
            }}
        """)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        
        # 默认提示
        self.empty_label = QLabel("请选择一个节点")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 11pt; padding: 20px;")
        self.content_layout.addWidget(self.empty_label)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # 应用通用样式
        combined_style = (
            ThemeManager.get_input_style() + "\n" +
            ThemeManager.get_button_style("primary") + "\n" +
            ThemeManager.get_group_box_style()
        )
        # Add label color
        combined_style += f"\nQLabel {{ color: {ThemeManager.COLORS['text']}; }}"
        
        self.setStyleSheet(combined_style)
    
    def _clear_content_immediately(self):
        """立即清空内容区域的所有控件"""
        # 获取所有子控件并立即删除
        children = self.content_widget.findChildren(QWidget)
        for child in children:
            child.setParent(None)
            child.deleteLater()
        
        # 强制处理事件队列
        QApplication.processEvents()
        
        # 确保布局也是空的
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
    
    def clear_properties(self):
        """清空属性面板"""
        # 清除所有子部件（立即删除）
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)  # 立即从父控件移除
                widget.deleteLater()
        
        # 显示空提示
        self.empty_label = QLabel("请选择一个节点")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 11pt; padding: 20px;")
        self.content_layout.addWidget(self.empty_label)
        self.content_layout.addStretch()
        
        self.current_node_id = None
        self.current_node_type = None
        self.config_widgets = {}  # 清空配置控件字典
    
    def load_node_properties(self, node_id: str, node_type: NodeType, config: dict):
        """加载节点属性（使用延迟加载优化快速切换）"""
        # 停止之前的定时器
        self._load_timer.stop()
        
        # 保存待加载的数据
        self._pending_load = (node_id, node_type, config)
        
        # 设置短暂延迟（50ms），如果快速切换会被取消
        self._load_timer.start(50)
    
    def _do_load_node_properties(self):
        """实际执行加载节点属性"""
        if not self._pending_load:
            return
        
        node_id, node_type, config = self._pending_load
        self._pending_load = None
        
        # 如果节点未改变，不重新加载
        if self.current_node_id == node_id:
            return
        
        self.current_node_id = node_id
        self.current_node_type = node_type
        
        # 强制清除所有现有内容（防止重叠）
        self._clear_content_immediately()
        
        # 清空配置控件字典
        self.config_widgets = {}
        
        # 节点信息组
        info_group = QGroupBox("节点信息")
        info_layout = QFormLayout()
        
        # 节点ID
        id_label = QLabel(node_id)
        id_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']};")
        info_layout.addRow("节点ID:", id_label)
        
        # 节点类型
        type_label = QLabel(node_type.value)
        type_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']};")
        info_layout.addRow("节点类型:", type_label)
        
        info_group.setLayout(info_layout)
        self.content_layout.addWidget(info_group)
        
        # 根据节点类型创建配置表单
        config_group = QGroupBox("节点配置")
        config_layout = QFormLayout()
        
        self.config_widgets = {}
        
        if node_type == NodeType.VARIABLE_ASSIGN:
            self._create_variable_assign_form(config_layout, config)
        elif node_type == NodeType.VARIABLE_CALC:
            self._create_variable_calc_form(config_layout, config)
        elif node_type == NodeType.SQLITE_CONNECT:
            self._create_sqlite_connect_form(config_layout, config)
        elif node_type == NodeType.SQL_STATEMENT:
            self._create_sql_statement_form(config_layout, config)
        elif node_type == NodeType.SQLITE_EXECUTE:
            self._create_sqlite_execute_form(config_layout, config)
        
        config_group.setLayout(config_layout)
        self.content_layout.addWidget(config_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_changes)
        button_layout.addWidget(apply_btn)
        
        self.content_layout.addLayout(button_layout)
        self.content_layout.addStretch()
    
    def _create_variable_assign_form(self, layout, config):
        """创建变量赋值节点表单"""
        # 变量名
        var_name = QLineEdit(config.get('variable_name', ''))
        var_name.setPlaceholderText("例如: x")
        self.config_widgets['variable_name'] = var_name
        layout.addRow("变量名:", var_name)
        
        # 值
        value = QLineEdit(config.get('value', ''))
        value.setPlaceholderText("例如: 100")
        self.config_widgets['value'] = value
        layout.addRow("值:", value)
        
        # 值类型
        value_type = QComboBox()
        value_type.addItems(['str', 'int', 'float', 'bool', 'json'])
        value_type.setCurrentText(config.get('value_type', 'str'))
        self.config_widgets['value_type'] = value_type
        layout.addRow("类型:", value_type)
    
    def _create_variable_calc_form(self, layout, config):
        """创建变量计算节点表单"""
        # 表达式
        expression = QLineEdit(config.get('expression', ''))
        expression.setPlaceholderText("例如: x + y * 2")
        self.config_widgets['expression'] = expression
        layout.addRow("表达式:", expression)
        
        # 输出变量
        output_var = QLineEdit(config.get('output_var', 'result'))
        output_var.setPlaceholderText("例如: result")
        self.config_widgets['output_var'] = output_var
        layout.addRow("输出变量:", output_var)
    
    def _create_sqlite_connect_form(self, layout, config):
        """创建SQLite连接节点表单"""
        # 数据库路径
        db_path = QLineEdit(config.get('db_path', './data.db'))
        db_path.setPlaceholderText("例如: ./data.db")
        self.config_widgets['db_path'] = db_path
        layout.addRow("数据库路径:", db_path)
        
        # 连接名称
        conn_name = QLineEdit(config.get('connection_name', 'db_conn'))
        conn_name.setPlaceholderText("例如: db_conn")
        self.config_widgets['connection_name'] = conn_name
        layout.addRow("连接名称:", conn_name)
    
    def _create_sql_statement_form(self, layout, config):
        """创建SQL语句节点表单"""
        # SQL语句
        sql = QTextEdit(config.get('sql', ''))
        sql.setPlaceholderText("例如: SELECT * FROM users WHERE id = {user_id}")
        sql.setMaximumHeight(100)
        self.config_widgets['sql'] = sql
        layout.addRow("SQL语句:", sql)
        
        # 输出变量
        output_var = QLineEdit(config.get('output_var', 'sql'))
        output_var.setPlaceholderText("例如: sql")
        self.config_widgets['output_var'] = output_var
        layout.addRow("输出变量:", output_var)
    
    def _create_sqlite_execute_form(self, layout, config):
        """创建SQLite执行节点表单"""
        # 连接名称
        conn_name = QLineEdit(config.get('connection_name', 'db_conn'))
        conn_name.setPlaceholderText("例如: db_conn")
        self.config_widgets['connection_name'] = conn_name
        layout.addRow("连接名称:", conn_name)
        
        # SQL变量名
        sql_var = QLineEdit(config.get('sql_var', 'sql'))
        sql_var.setPlaceholderText("例如: sql")
        self.config_widgets['sql_var'] = sql_var
        layout.addRow("SQL变量:", sql_var)
        
        # 输出变量
        output_var = QLineEdit(config.get('output_var', 'query_result'))
        output_var.setPlaceholderText("例如: query_result")
        self.config_widgets['output_var'] = output_var
        layout.addRow("输出变量:", output_var)
    
    def _apply_changes(self):
        """应用更改"""
        if not self.current_node_id:
            return
        
        config = {}
        
        for key, widget in self.config_widgets.items():
            if isinstance(widget, QLineEdit):
                config[key] = widget.text()
            elif isinstance(widget, QTextEdit):
                config[key] = widget.toPlainText()
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
        
        # 发送更新信号
        self.properties_updated.emit(self.current_node_id, config)
        
        print(f"节点 {self.current_node_id} 配置已更新: {config}")
