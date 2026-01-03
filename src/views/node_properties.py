"""
节点属性面板
用于编辑选中节点的属性
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QComboBox, QTextEdit, QPushButton,
                               QScrollArea, QGroupBox, QHBoxLayout, QApplication,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from src.core.node_base import NodeType
from src.core.theme_manager import ThemeManager
from src.core.node_registry import get_registry, NODE_SOURCE_INFO, NodeSource


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
        # 强制停止计时器
        self._load_timer.stop()
        
        # 确保布局中的所有控件都被移除并销毁
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                # 清除子布局
                self._clear_layout(item.layout())
    
    def _clear_layout(self, layout):
        """递归清除布局"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def clear_properties(self):
        """清空属性面板"""
        self._clear_content_immediately()
        
        # 显示空提示
        self.empty_label = QLabel("请选择一个节点")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 11pt; padding: 20px;")
        self.content_layout.addWidget(self.empty_label)
        self.content_layout.addStretch()
        
        self.current_node_id = None
        self.current_node_type = None
        self.config_widgets = {}
    
    def load_node_properties(self, node_id: str, node_type: NodeType, config: dict):
        """加载节点属性（优化响应速度）"""
        # 停止之前的计时器
        self._load_timer.stop()
        
        # 保存待加载的数据
        self._pending_load = (node_id, node_type, config)
        
        # 极短延迟（10ms）用于防抖，减少肉眼可察觉的延迟
        self._load_timer.start(10)
    
    def _do_load_node_properties(self):
        """实际执行加载节点属性"""
        if not self._pending_load:
            return
        
        node_id, node_type, config = self._pending_load
        self._pending_load = None
        
        # 强制清除所有现有内容
        self._clear_content_immediately()
        
        self.current_node_id = node_id
        self.current_node_type = node_type
        
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
        
        # 节点来源
        registry = get_registry()
        node_info = registry.get_node_info(node_type.value)
        source_info = node_info.get('source_info', NODE_SOURCE_INFO[NodeSource.OFFICIAL])
        source_label = QLabel(source_info['name'])
        source_label.setStyleSheet(f"color: {source_info['color']}; font-weight: bold;")
        info_layout.addRow("来源:", source_label)
        
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
        
        apply_btn = QPushButton("应用配置")
        apply_btn.clicked.connect(self._apply_changes)
        button_layout.addWidget(apply_btn)
        
        # 针对自定义节点的额外操作
        registry = get_registry()
        node_def = registry.get_node(node_type.value)
        if node_def and node_def.source == NodeSource.CUSTOM:
            export_btn = QPushButton("📦 导出节点")
            export_btn.setStyleSheet(ThemeManager.get_button_style("secondary"))
            export_btn.clicked.connect(self._export_custom_node)
            button_layout.addWidget(export_btn)
            
            delete_btn = QPushButton("🗑️ 删除节点")
            delete_btn.setStyleSheet(ThemeManager.get_button_style("danger") if hasattr(ThemeManager, "get_button_style") else "")
            delete_btn.clicked.connect(self._delete_custom_node)
            button_layout.addWidget(delete_btn)
        
        self.content_layout.addLayout(button_layout)
        
        # 源代码区域（可折叠）
        self._create_source_code_section(node_type.value)
        
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
    
    def _create_source_code_section(self, node_type: str):
        """创建源代码展示区域"""
        from PySide6.QtWidgets import QPlainTextEdit
        
        # 可折叠的源代码组
        source_group = QGroupBox("📝 源代码 (点击展开)")
        source_group.setCheckable(True)
        source_group.setChecked(False)  # 默认折叠
        source_layout = QVBoxLayout(source_group)
        
        # 源代码编辑器
        self.source_code_edit = QPlainTextEdit()
        self.source_code_edit.setReadOnly(True)  # 默认只读
        self.source_code_edit.setMinimumHeight(150)
        self.source_code_edit.setMaximumHeight(300)
        self.source_code_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {ThemeManager.COLORS['background']};
                color: {ThemeManager.COLORS['text']};
                border: 1px solid {ThemeManager.COLORS['border']};
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10pt;
                padding: 8px;
            }}
        """)
        
        # 加载源代码
        registry = get_registry()
        source_code = registry.get_source_code(node_type)
        self.source_code_edit.setPlainText(source_code)
        self._current_node_type_for_source = node_type
        
        source_layout.addWidget(self.source_code_edit)
        
        # 按钮行
        source_btn_layout = QHBoxLayout()
        
        # 复制按钮
        copy_btn = QPushButton("📋 复制")
        copy_btn.setStyleSheet(ThemeManager.get_button_style("secondary"))
        copy_btn.clicked.connect(self._copy_source_code)
        source_btn_layout.addWidget(copy_btn)
        
        # 编辑/保存按钮
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.setStyleSheet(ThemeManager.get_button_style("secondary"))
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        source_btn_layout.addWidget(self.edit_btn)
        
        # 重置按钮
        reset_btn = QPushButton("↩️ 重置")
        reset_btn.setStyleSheet(ThemeManager.get_button_style("secondary"))
        reset_btn.clicked.connect(self._reset_source_code)
        source_btn_layout.addWidget(reset_btn)
        
        source_btn_layout.addStretch()
        
        # 保存按钮
        self.save_source_btn = QPushButton("💾 保存修改")
        self.save_source_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.save_source_btn.clicked.connect(self._save_source_code)
        self.save_source_btn.setEnabled(False)  # 默认禁用
        source_btn_layout.addWidget(self.save_source_btn)
        
        source_layout.addLayout(source_btn_layout)
        
        # 连接折叠状态
        source_group.toggled.connect(lambda checked: self.source_code_edit.setVisible(checked))
        self.source_code_edit.setVisible(False)  # 初始隐藏
        
        self.content_layout.addWidget(source_group)
        self._source_group = source_group
    
    def _copy_source_code(self):
        """复制源代码到剪贴板"""
        source_code = self.source_code_edit.toPlainText()
        QApplication.clipboard().setText(source_code)
        print("源代码已复制到剪贴板")
    
    def _toggle_edit_mode(self):
        """切换编辑模式"""
        if self.source_code_edit.isReadOnly():
            # 进入编辑模式
            self.source_code_edit.setReadOnly(False)
            self.edit_btn.setText("🔒 锁定")
            self.save_source_btn.setEnabled(True)
            self.source_code_edit.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: #1a1a2e;
                    color: {ThemeManager.COLORS['text']};
                    border: 2px solid {ThemeManager.COLORS['accent']};
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 10pt;
                    padding: 8px;
                }}
            """)
        else:
            # 退出编辑模式
            self.source_code_edit.setReadOnly(True)
            self.edit_btn.setText("✏️ 编辑")
            self.save_source_btn.setEnabled(False)
            self.source_code_edit.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {ThemeManager.COLORS['background']};
                    color: {ThemeManager.COLORS['text']};
                    border: 1px solid {ThemeManager.COLORS['border']};
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 10pt;
                    padding: 8px;
                }}
            """)
    
    def _reset_source_code(self):
        """重置源代码"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要重置源代码到原始版本吗？\n\n您的修改将会丢失。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            registry = get_registry()
            registry.reset_to_original(self._current_node_type_for_source)
            
            # 重新加载
            source_code = registry.get_source_code(self._current_node_type_for_source)
            self.source_code_edit.setPlainText(source_code)
            
            print(f"源代码已重置: {self._current_node_type_for_source}")
    
    def _save_source_code(self):
        """保存修改的源代码"""
        source_code = self.source_code_edit.toPlainText()
        registry = get_registry()
        
        # 验证代码
        from src.core.custom_node_manager import CustomNodeManager
        manager = CustomNodeManager(registry._user_data_dir)
        is_valid, error_msg = manager.validate_node(source_code)
        
        if not is_valid:
            QMessageBox.warning(self, "代码验证失败", f"无法保存，代码存在错误：\n\n{error_msg}")
            return

        if registry.save_modified_source(self._current_node_type_for_source, source_code):
            QMessageBox.information(self, "保存成功", "源代码已保存！\n\n节点将在下次使用时应用新代码。")
            self._toggle_edit_mode()  # 退出编辑模式
        else:
            QMessageBox.warning(self, "保存失败", "无法保存源代码，请重试。")

    def _export_custom_node(self):
        """导出自定义节点"""
        if not self._current_node_type_for_source:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出节点", f"{self._current_node_type_for_source}.zip", "ZIP 压缩包 (*.zip)"
        )
        
        if file_path:
            from src.core.custom_node_manager import CustomNodeManager
            registry = get_registry()
            manager = CustomNodeManager(registry._user_data_dir)
            
            if manager.export_node(self._current_node_type_for_source, file_path):
                QMessageBox.information(self, "导出成功", f"节点已成功导出到：\n{file_path}")
            else:
                QMessageBox.critical(self, "导出失败", "导出节点过程中发生错误。")

    def _delete_custom_node(self):
        """删除自定义节点"""
        if not self._current_node_type_for_source:
            return
            
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要永久删除自定义节点 '{self._current_node_type_for_source}' 吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from src.core.custom_node_manager import CustomNodeManager
            registry = get_registry()
            manager = CustomNodeManager(registry._user_data_dir)
            
            if manager.delete_node(self._current_node_type_for_source):
                registry.unregister_node(self._current_node_type_for_source)
                QMessageBox.information(self, "删除成功", "节点已成功删除。")
                self.clear_properties()
                
                # 尝试通知节点浏览器刷新
                # 向上寻找主窗口并尝试触发刷新
                widget = self.parent()
                while widget:
                    if hasattr(widget, 'node_browser'):
                        widget.node_browser._load_nodes()
                        break
                    widget = widget.parent() if hasattr(widget, 'parent') else None
            else:
                QMessageBox.critical(self, "删除失败", "无法删除节点目录。")

