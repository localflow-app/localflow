"""
添加节点对话框
支持从GitHub、内网Git仓库导入节点，或创建自定义节点
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QRadioButton, QButtonGroup, 
                               QPushButton, QTextEdit, QGroupBox, QMessageBox)
from PySide6.QtCore import Qt

from src.core.theme_manager import ThemeManager


class AddNodeDialog(QDialog):
    """添加节点对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加节点")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 选项组
        self.option_group = QButtonGroup(self)
        
        # === GitHub 导入 ===
        github_group = QGroupBox("🐙 从 GitHub 仓库导入")
        github_layout = QVBoxLayout(github_group)
        
        self.github_radio = QRadioButton("从 GitHub 社区导入节点")
        self.github_radio.setChecked(True)
        self.option_group.addButton(self.github_radio, 1)
        github_layout.addWidget(self.github_radio)
        
        github_url_layout = QHBoxLayout()
        github_url_layout.addWidget(QLabel("仓库URL:"))
        self.github_url_input = QLineEdit()
        self.github_url_input.setPlaceholderText("https://github.com/username/node-repo")
        github_url_layout.addWidget(self.github_url_input)
        github_layout.addLayout(github_url_layout)
        
        github_hint = QLabel("💡 仓库需包含 node.json 配置文件")
        github_hint.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt;")
        github_layout.addWidget(github_hint)
        
        layout.addWidget(github_group)
        
        # === 内网导入 ===
        enterprise_group = QGroupBox("🏢 从内网 Git 仓库导入")
        enterprise_layout = QVBoxLayout(enterprise_group)
        
        self.enterprise_radio = QRadioButton("从企业内网仓库导入节点")
        self.option_group.addButton(self.enterprise_radio, 2)
        enterprise_layout.addWidget(self.enterprise_radio)
        
        enterprise_url_layout = QHBoxLayout()
        enterprise_url_layout.addWidget(QLabel("Git URL:"))
        self.enterprise_url_input = QLineEdit()
        self.enterprise_url_input.setPlaceholderText("git@internal.company.com:nodes/my-node.git")
        enterprise_url_layout.addWidget(self.enterprise_url_input)
        enterprise_layout.addLayout(enterprise_url_layout)
        
        enterprise_hint = QLabel("💡 需确保有仓库访问权限")
        enterprise_hint.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt;")
        enterprise_layout.addWidget(enterprise_hint)
        
        layout.addWidget(enterprise_group)
        
        # === 自定义节点 ===
        custom_group = QGroupBox("👤 创建自定义节点")
        custom_layout = QVBoxLayout(custom_group)
        
        self.custom_radio = QRadioButton("创建新的自定义节点")
        self.option_group.addButton(self.custom_radio, 3)
        custom_layout.addWidget(self.custom_radio)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("节点名称:"))
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("我的自定义节点")
        name_layout.addWidget(self.custom_name_input)
        custom_layout.addLayout(name_layout)
        
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("节点描述:"))
        self.custom_desc_input = QLineEdit()
        self.custom_desc_input.setPlaceholderText("这是一个自定义节点")
        desc_layout.addWidget(self.custom_desc_input)
        custom_layout.addLayout(desc_layout)
        
        custom_hint = QLabel("💡 创建后可在属性面板编辑源代码")
        custom_hint.setStyleSheet(f"color: {ThemeManager.COLORS['text_secondary']}; font-size: 9pt;")
        custom_layout.addWidget(custom_hint)
        
        layout.addWidget(custom_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(ThemeManager.get_button_style("secondary"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.confirm_btn = QPushButton("确定导入/创建")
        self.confirm_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(button_layout)
        
        # 连接单选按钮变化
        self.option_group.buttonClicked.connect(self._on_option_changed)
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeManager.COLORS['surface']};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {ThemeManager.COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {ThemeManager.COLORS['text']};
            }}
            QLabel {{
                color: {ThemeManager.COLORS['text']};
            }}
            QRadioButton {{
                color: {ThemeManager.COLORS['text']};
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
            }}
            {ThemeManager.get_input_style()}
        """)
    
    def _on_option_changed(self, button):
        """选项变化"""
        # 可以在这里更新UI状态
        pass
    
    def _on_confirm(self):
        """确认按钮"""
        selected_id = self.option_group.checkedId()
        
        if selected_id == 1:
            # GitHub 导入
            url = self.github_url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "提示", "请输入 GitHub 仓库 URL")
                return
            
            try:
                from src.core.node_registry import get_registry
                from src.core.providers.github_provider import GitHubNodeProvider
                
                registry = get_registry()
                provider = GitHubNodeProvider(registry._user_data_dir)
                
                node_def = provider.download_node(url)
                if node_def:
                    QMessageBox.information(
                        self, 
                        "成功", 
                        f"GitHub 节点 '{node_def.name}' 导入成功！\n请在节点浏览器的'GitHub'分类下查看。"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "错误", "无法从提供的 URL 导入节点，请检查 URL 是否正确。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入 GitHub 节点过程中发生异常: {str(e)}")
            return
            
        elif selected_id == 2:
            # 内网导入
            url = self.enterprise_url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "提示", "请输入内网 Git 仓库 URL")
                return
            
            # 内网导入功能将在 Phase 3 实现
            QMessageBox.information(
                self, 
                "功能预留", 
                f"内网节点导入功能将在 Phase 3 完善。\n\n仓库: {url}"
            )
            self.accept()
            return
            
        elif selected_id == 3:
            # 自定义节点
            name = self.custom_name_input.text().strip()
            desc = self.custom_desc_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "提示", "请输入节点名称")
                return
            
            try:
                from src.core.node_registry import get_registry
                from src.core.custom_node_manager import CustomNodeManager
                
                registry = get_registry()
                manager = CustomNodeManager(registry._user_data_dir)
                
                node_def = manager.create_node(name, desc)
                if node_def:
                    registry.register_external_node(node_def)
                    QMessageBox.information(
                        self, 
                        "成功", 
                        f"自定义节点 '{name}' 创建成功！\n请在节点浏览器的'自定义'分类下查看并编辑。"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "错误", "创建节点失败，请重试。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建节点过程中发生异常: {str(e)}")
