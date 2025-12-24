from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from .workflow_canvas import WorkflowCanvas, WorkflowGraphicsScene
from src.core.workflow_executor import WorkflowExecutor
from src.core.uv_manager import UVManager
from src.core.node_base import NodeType
import time
import os
import shutil


class WorkflowTabWidget(QWidget):
    # 信号：工作流修改状态改变
    modified_changed = Signal(bool)  # is_modified
    
    def __init__(self, workflow_name="新工作流", parent=None):
        super().__init__(parent)
        self.workflow_name = workflow_name
        self.main_window = parent
        
        # 修改状态标记
        self._is_modified = False
        
        # 创建工作流执行器
        self.uv_manager = UVManager()
        self.executor = WorkflowExecutor(workflow_name, self.uv_manager)
        
        # 节点数据字典 {node_id: node_graphics_item}
        self.nodes = {}
        # 连接数据 [(from_port, to_port)]
        self.connections = []
        
        # UI组件引用
        self.name_label = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3f3f3f;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 工作流名称和重命名按钮
        name_widget = QWidget()
        name_layout = QHBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(5)
        
        self.name_label = QLabel(self.workflow_name)
        name_font = QFont()
        name_font.setPointSize(10)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet("color: #e0e0e0;")
        name_layout.addWidget(self.name_label)
        
        # 重命名按钮
        rename_btn = QPushButton("✏️")
        rename_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555;
                border-color: #777;
            }
        """)
        rename_btn.setToolTip("重命名工作流")
        rename_btn.clicked.connect(self.rename_workflow)
        name_layout.addWidget(rename_btn)
        
        toolbar_layout.addWidget(name_widget)
        
        toolbar_layout.addStretch()
        
        # 执行按钮
        self.run_btn = QPushButton("▶ 执行工作流")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.run_btn.clicked.connect(self._execute_workflow)
        toolbar_layout.addWidget(self.run_btn)
        
        # 保存按钮
        save_btn = QPushButton("💾 保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        save_btn.clicked.connect(self._save_workflow)
        toolbar_layout.addWidget(save_btn)
        
        layout.addWidget(toolbar)
        
        # Create a new scene
        scene = WorkflowGraphicsScene(self)
        self.canvas = WorkflowCanvas(scene, self)
        self.canvas.node_added.connect(self._on_node_added)
        self.canvas.node_selected.connect(self._on_node_selected)
        self.canvas.node_deleted.connect(self._on_node_deleted)
        self.canvas.connection_created.connect(self._on_connection_created)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def _on_node_added(self, node_item):
        """节点被添加到画布"""
        self.nodes[node_item.node_id] = node_item
        print(f"节点已添加: {node_item.node_id} ({node_item.node_type.value})")
        self._set_modified(True)
    
    def _on_node_selected(self, node_item):
        """节点被选中"""
        if self.main_window and hasattr(self.main_window, 'node_properties'):
            # 加载节点属性到属性面板
            self.main_window.node_properties.load_node_properties(
                node_item.node_id,
                node_item.node_type,
                node_item.config
            )
            # 显示属性面板
            if not self.main_window.node_properties_dock.isVisible():
                self.main_window.node_properties_dock.show()
    
    def _on_node_deleted(self, node_id: str):
        """节点被删除"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            print(f"节点已删除: {node_id}")
            
            # 删除相关连接
            self.connections = [(from_id, to_id) for from_id, to_id in self.connections 
                               if from_id != node_id and to_id != node_id]
            
            # 清空属性面板（如果删除的是当前选中的节点）
            if self.main_window and hasattr(self.main_window, 'node_properties'):
                if self.main_window.node_properties.current_node_id == node_id:
                    self.main_window.node_properties.clear_properties()
            
            self._set_modified(True)
    
    def _on_connection_created(self, from_node_id, to_node_id):
        """连接被创建"""
        self.connections.append((from_node_id, to_node_id))
        print(f"连接已创建: {from_node_id} -> {to_node_id}")
        self._set_modified(True)
    
    def update_node_config(self, node_id: str, config: dict):
        """更新节点配置"""
        if node_id in self.nodes:
            node_item = self.nodes[node_id]
            node_item.config = config
            print(f"节点配置已更新: {node_id}")
            self._set_modified(True)
    
    def _set_modified(self, modified: bool):
        """设置修改状态"""
        if self._is_modified != modified:
            self._is_modified = modified
            self.modified_changed.emit(modified)
    
    def is_modified(self):
        """获取修改状态"""
        return self._is_modified
    
    def _execute_workflow(self):
        """执行工作流"""
        if not self.nodes:
            QMessageBox.warning(self, "无法执行", "工作流中没有节点")
            return
        
        # 构建执行器
        from src.core.node_base import (
            VariableAssignNode, VariableCalcNode,
            SQLiteConnectNode, SQLiteExecuteNode, SQLStatementNode
        )
        
        # 清空现有节点
        self.executor.nodes.clear()
        self.executor.edges.clear()
        
        # 添加节点
        node_classes = {
            NodeType.VARIABLE_ASSIGN: VariableAssignNode,
            NodeType.VARIABLE_CALC: VariableCalcNode,
            NodeType.SQLITE_CONNECT: SQLiteConnectNode,
            NodeType.SQLITE_EXECUTE: SQLiteExecuteNode,
            NodeType.SQL_STATEMENT: SQLStatementNode,
        }
        
        for node_id, node_item in self.nodes.items():
            node_class = node_classes.get(node_item.node_type)
            if node_class:
                node = node_class(node_id, node_item.config)
                self.executor.add_node(node)
        
        # 添加连接
        for from_id, to_id in self.connections:
            self.executor.add_edge(from_id, to_id)
        
        # 准备环境
        print(f"\n执行工作流: {self.workflow_name}")
        if not self.uv_manager.check_uv_installed():
            print("警告: UV未安装，将使用当前Python环境")
        
        self.executor.prepare_environment()
        
        # 执行
        try:
            # 重置节点状态
            for node_item in self.nodes.values():
                node_item.set_executing(False)
                node_item.set_error(False)
            
            # 执行前更新UI
            self.run_btn.setEnabled(False)
            self.run_btn.setText("执行中...")
            
            # 执行工作流
            result = self.executor.execute()
            
            # 显示结果
            result_text = "执行成功！\n\n结果:\n"
            for key, value in result.items():
                result_text += f"  {key} = {value}\n"
            
            QMessageBox.information(self, "执行成功", result_text)
            
            print(f"\n工作流执行成功")
            print(f"结果: {result}")
            
        except Exception as e:
            QMessageBox.critical(self, "执行失败", f"工作流执行失败:\n\n{str(e)}")
            print(f"\n工作流执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("▶ 执行工作流")
    
    def _save_workflow(self):
        """保存工作流"""
        try:
            # 验证工作流名称（保存时排除当前工作流名称，因为保存同一个工作流是允许的）
            is_valid, error_msg = self._validate_workflow_name(self.workflow_name, exclude_current=True)
            if not is_valid:
                QMessageBox.warning(self, "名称无效", f"无法保存工作流:\n\n{error_msg}\n\n请重命名工作流后再保存。")
                return
            
            import os
            save_path = f"workflows/{self.workflow_name}/workflow.json"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 构建保存数据
            from src.core.node_base import (
                VariableAssignNode, VariableCalcNode,
                SQLiteConnectNode, SQLiteExecuteNode, SQLStatementNode
            )
            
            self.executor.nodes.clear()
            self.executor.edges.clear()
            
            node_classes = {
                NodeType.VARIABLE_ASSIGN: VariableAssignNode,
                NodeType.VARIABLE_CALC: VariableCalcNode,
                NodeType.SQLITE_CONNECT: SQLiteConnectNode,
                NodeType.SQLITE_EXECUTE: SQLiteExecuteNode,
                NodeType.SQL_STATEMENT: SQLStatementNode,
            }
            
            # 收集节点位置
            node_positions = {}
            for node_id, node_item in self.nodes.items():
                node_class = node_classes.get(node_item.node_type)
                if node_class:
                    node = node_class(node_id, node_item.config)
                    self.executor.add_node(node)
                    
                    # 保存节点位置
                    pos = node_item.pos()
                    node_positions[node_id] = {"x": pos.x(), "y": pos.y()}
            
            for from_id, to_id in self.connections:
                self.executor.add_edge(from_id, to_id)
            
            # 保存时传入位置信息
            self.executor.save_workflow(save_path, node_positions)
            
            # 保存成功后，重置修改状态
            self._set_modified(False)
            
            QMessageBox.information(self, "保存成功", f"工作流已保存到:\n{save_path}")
            print(f"工作流已保存: {save_path}")
            
            # 延迟刷新首页工作流列表（避免Qt对象访问冲突）
            if self.main_window:
                QTimer.singleShot(100, self._refresh_overview_list)
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存工作流时出错:\n\n{str(e)}")
            print(f"保存失败: {e}")
    
    def _refresh_overview_list(self):
        """刷新首页工作流列表"""
        try:
            if self.main_window:
                overview_tab = self.main_window.tabs.widget(0)
                if overview_tab and hasattr(overview_tab, 'refresh_workflows'):
                    overview_tab.refresh_workflows()
        except Exception as e:
            print(f"刷新首页列表失败: {e}")
    
    def get_workflow_name(self):
        return self.workflow_name
    
    def _validate_workflow_name(self, new_name: str, exclude_current: bool = True) -> tuple[bool, str]:
        """验证工作流名称是否有效
        
        Args:
            new_name: 新的工作流名称
            exclude_current: 是否排除当前工作流名称（用于重命名时）
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not new_name or not new_name.strip():
            return False, "工作流名称不能为空"
        
        new_name = new_name.strip()
        
        # 检查名称中是否包含非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            if char in new_name:
                return False, f"工作流名称不能包含字符: {char}"
        
        # 检查名称是否已存在
        workflows_dir = "workflows"
        if os.path.exists(workflows_dir):
            for item in os.listdir(workflows_dir):
                item_path = os.path.join(workflows_dir, item)
                if os.path.isdir(item_path):
                    # 如果是重命名操作，排除当前工作流名称
                    if exclude_current and item == self.workflow_name:
                        continue
                    if item == new_name:
                        return False, f"工作流 '{new_name}' 已存在"
        
        return True, ""
    
    def rename_workflow(self):
        """重命名工作流"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("重命名工作流")
        dialog.setFixedSize(400, 150)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # 输入框
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("新名称:"))
        name_input = QLineEdit(self.workflow_name)
        input_layout.addWidget(name_input)
        layout.addLayout(input_layout)
        
        # 错误提示标签
        error_label = QLabel("")
        error_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        layout.addWidget(error_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        def validate_name():
            new_name = name_input.text().strip()
            is_valid, error_msg = self._validate_workflow_name(new_name)
            
            if not is_valid:
                error_label.setText(error_msg)
                ok_btn.setEnabled(False)
            else:
                error_label.setText("")
                ok_btn.setEnabled(True)
        
        def accept_rename():
            new_name = name_input.text().strip()
            is_valid, error_msg = self._validate_workflow_name(new_name)
            
            if not is_valid:
                error_label.setText(error_msg)
                return
            
            # 执行重命名
            if self._rename_workflow_files(new_name):
                self.workflow_name = new_name
                self.executor.workflow_name = new_name
                
                # 更新工具栏中的名称标签
                if self.name_label:
                    self.name_label.setText(new_name)
                
                # 如果当前工作流已保存，重置修改状态
                if not self._is_modified:
                    self._set_modified(False)
                
                # 通知主窗口更新标签页名称
                if self.main_window:
                    self.main_window.update_tab_name(self, new_name)
                
                # 刷新首页工作流列表
                QTimer.singleShot(100, self._refresh_overview_list)
                
                dialog.accept()
            else:
                error_label.setText("重命名失败，请检查文件权限")
        
        name_input.textChanged.connect(validate_name)
        ok_btn.clicked.connect(accept_rename)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 初始验证
        validate_name()
        name_input.selectAll()
        name_input.setFocus()
        
        dialog.exec()
    
    def _rename_workflow_files(self, new_name: str) -> bool:
        """重命名工作流文件和目录
        
        Args:
            new_name: 新的工作流名称
            
        Returns:
            bool: 重命名是否成功
        """
        try:
            old_dir = f"workflows/{self.workflow_name}"
            new_dir = f"workflows/{new_name}"
            
            # 如果旧目录存在，重命名它
            if os.path.exists(old_dir):
                # 确保目标目录不存在
                if os.path.exists(new_dir):
                    return False
                
                shutil.move(old_dir, new_dir)
                
                # 更新工作流文件中的名称
                workflow_file = os.path.join(new_dir, "workflow.json")
                if os.path.exists(workflow_file):
                    self._update_workflow_name_in_file(workflow_file, new_name)
            
            return True
            
        except Exception as e:
            print(f"重命名工作流文件失败: {e}")
            return False
    
    def _update_workflow_name_in_file(self, file_path: str, new_name: str):
        """更新工作流文件中的名称字段
        
        Args:
            file_path: 工作流文件路径
            new_name: 新的工作流名称
        """
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'workflow_name' in data:
                data['workflow_name'] = new_name
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"更新工作流文件名称失败: {e}")