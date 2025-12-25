import os
import sys
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QGroupBox, QMessageBox,
                               QTextEdit, QProgressBar, QApplication, QComboBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette


class InstallWorker(QThread):
    """Worker thread for installing uv"""
    finished = Signal(bool, str)
    progress = Signal(str)
    
    def __init__(self, install_command):
        super().__init__()
        self.install_command = install_command
    
    def run(self):
        try:
            self.progress.emit("正在安装 uv，请稍候...")
            
            # Run installation command
            process = subprocess.Popen(
                self.install_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.progress.emit("安装成功！")
                self.finished.emit(True, stdout)
            else:
                self.progress.emit("安装失败！")
                self.finished.emit(False, stderr)
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.uv_path = ""
        self.uv_mirror = ""
        self.uv_paths = []  # 存储找到的所有uv路径
        self.install_worker = None
        self.is_dark_theme = self._detect_dark_theme()
        
        self._setup_ui()
        self._detect_uv()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # UV Package Manager Group
        uv_group = QGroupBox("UV 包管理工具")
        uv_layout = QVBoxLayout()
        
        # UV Path
        path_layout = QHBoxLayout()
        path_label = QLabel("UV 路径:")
        path_label.setFixedWidth(80)
        
        # 使用下拉框显示多个uv路径
        self.path_combo = QComboBox()
        self.path_combo.setMinimumWidth(300)
        self.path_combo.currentTextChanged.connect(self._on_uv_path_changed)
        
        self.detect_btn = QPushButton("重新检测")
        self.detect_btn.clicked.connect(self._detect_uv)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_combo)
        path_layout.addWidget(self.detect_btn)
        uv_layout.addLayout(path_layout)
        
        # 路径详情显示
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("未检测到 uv")
        self.path_input.setReadOnly(True)
        uv_layout.addWidget(self.path_input)
        
        # UV Mirror
        mirror_layout = QHBoxLayout()
        mirror_label = QLabel("镜像地址:")
        mirror_label.setFixedWidth(80)
        self.mirror_combo = QComboBox()
        self.mirror_combo.setEditable(True)  # 允许用户输入自定义镜像
        self.mirror_combo.setMinimumWidth(300)
        self.mirror_combo.currentTextChanged.connect(self._on_mirror_changed)
        
        # 预设的常用镜像
        self.mirror_combo.addItems([
            "默认镜像",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.aliyun.com/pypi/simple", 
            "https://pypi.mirrors.ustc.edu.cn/simple",
            "https://mirrors.cloud.tencent.com/pypi/simple",
            "自定义镜像..."
        ])
        
        mirror_layout.addWidget(mirror_label)
        mirror_layout.addWidget(self.mirror_combo)
        uv_layout.addLayout(mirror_layout)
        
        # Status
        self.status_label = QLabel("状态: 检测中...")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        uv_layout.addWidget(self.status_label)
        
        uv_group.setLayout(uv_layout)
        layout.addWidget(uv_group)
        
        # Installation Group
        install_group = QGroupBox("安装 UV")
        install_layout = QVBoxLayout()
        
        info_label = QLabel("UV 是一个快速的 Python 包管理工具，可以替代 pip。")
        info_label.setWordWrap(True)
        if self.is_dark_theme:
            info_label.setStyleSheet("color: #a0a0a0;")
        else:
            info_label.setStyleSheet("color: #555555;")
        install_layout.addWidget(info_label)
        
        # Installation methods
        methods_label = QLabel("<b>快速安装方法（Windows）:</b>")
        install_layout.addWidget(methods_label)
        
        # Method 1: PowerShell
        method1_layout = QHBoxLayout()
        method1_label = QLabel("方法1: 使用 PowerShell")
        method1_label.setFixedWidth(150)
        self.install_ps_btn = QPushButton("一键安装")
        self.install_ps_btn.clicked.connect(self._install_uv_powershell)
        method1_layout.addWidget(method1_label)
        method1_layout.addWidget(self.install_ps_btn)
        method1_layout.addStretch()
        install_layout.addLayout(method1_layout)
        
        # Method 2: pip
        method2_layout = QHBoxLayout()
        method2_label = QLabel("方法2: 使用 pip")
        method2_label.setFixedWidth(150)
        self.install_pip_btn = QPushButton("一键安装")
        self.install_pip_btn.clicked.connect(self._install_uv_pip)
        method2_layout.addWidget(method2_label)
        method2_layout.addWidget(self.install_pip_btn)
        method2_layout.addStretch()
        install_layout.addLayout(method2_layout)
        
        # Manual installation instructions
        manual_label = QLabel("<b>手动安装:</b>")
        install_layout.addWidget(manual_label)
        
        self.manual_text = QTextEdit()
        self.manual_text.setReadOnly(True)
        self.manual_text.setMaximumHeight(100)
        self.manual_text.setPlainText(
            "PowerShell:\n"
            "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n\n"
            "或使用 pip:\n"
            "pip install uv"
        )
        install_layout.addWidget(self.manual_text)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        install_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        if self.is_dark_theme:
            self.progress_label.setStyleSheet("color: #1177bb;")
        else:
            self.progress_label.setStyleSheet("color: #007ACC;")
        install_layout.addWidget(self.progress_label)
        
        install_group.setLayout(install_layout)
        layout.addWidget(install_group)
        
        layout.addStretch()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setFixedWidth(100)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self._apply_styles()
    
    def _detect_dark_theme(self):
        """Detect if the current theme is dark"""
        palette = QApplication.palette()
        window_color = palette.color(QPalette.Window)
        # If window background is dark (brightness < 128), it's a dark theme
        brightness = (window_color.red() + window_color.green() + window_color.blue()) / 3
        return brightness < 128
    
    def _apply_styles(self):
        """Apply modern styles to the dialog based on theme"""
        if self.is_dark_theme:
            # Dark theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #3f3f3f;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 10px;
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #e0e0e0;
                }
                QLabel {
                    color: #e0e0e0;
                }
                QLineEdit {
                    padding: 6px;
                    border: 1px solid #3f3f3f;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                }
                QLineEdit:read-only {
                    background-color: #252525;
                    color: #a0a0a0;
                }
                QPushButton {
                    padding: 6px 12px;
                    background-color: #0e639c;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #0d5689;
                }
                QPushButton:disabled {
                    background-color: #3f3f3f;
                    color: #666666;
                }
                QTextEdit {
                    border: 1px solid #3f3f3f;
                    border-radius: 4px;
                    background-color: #252525;
                    color: #d4d4d4;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10pt;
                }
                QProgressBar {
                    border: 1px solid #3f3f3f;
                    border-radius: 4px;
                    background-color: #252525;
                    text-align: center;
                    color: #e0e0e0;
                }
                QProgressBar::chunk {
                    background-color: #0e639c;
                }
            """)
        else:
            # Light theme styles
            self.setStyleSheet("""
                QDialog {
                    background-color: #f5f5f5;
                    color: #000000;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 10px;
                    background-color: white;
                    color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QLineEdit {
                    padding: 6px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                    color: #000000;
                }
                QLineEdit:read-only {
                    background-color: #f0f0f0;
                    color: #666666;
                }
                QPushButton {
                    padding: 6px 12px;
                    background-color: #007ACC;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
                QTextEdit {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: #fafafa;
                    color: #000000;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10pt;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                    text-align: center;
                    color: #000000;
                }
                QProgressBar::chunk {
                    background-color: #007ACC;
                }
            """)
    
    def _detect_uv(self):
        """Detect uv installation and mirror configuration"""
        self.status_label.setText("状态: 检测中...")
        if self.is_dark_theme:
            self.status_label.setStyleSheet("color: #888888; font-style: italic;")
        else:
            self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        
        # Import UVManager here to avoid circular imports
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from core.uv_manager import UVManager
            uv_manager = UVManager()
            self.uv_paths = uv_manager.find_uv_installations()
            
            if self.uv_paths:
                # 清空下拉框并添加找到的uv路径
                self.path_combo.clear()
                
                for uv_path in self.uv_paths:
                    # 获取版本信息
                    try:
                        result = subprocess.run(
                            [uv_path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip()
                            # 显示路径和版本
                            display_text = f"{uv_path} ({version})"
                        else:
                            display_text = uv_path
                    except:
                        display_text = uv_path
                    
                    self.path_combo.addItem(display_text, uv_path)
                
                # 添加自定义选项
                self.path_combo.addItem("自定义路径...", "custom")
                
                # 启用下拉框并设置默认选择第一个
                self.path_combo.setEnabled(True)
                if self.uv_paths:
                    self.path_combo.setCurrentIndex(0)
                    self.uv_path = self.uv_paths[0]
                    self.path_input.setText(self.uv_path)
                
                # Check for mirror configuration
                self._detect_mirror()
                
                # 显示状态
                count = len(self.uv_paths)
                if count == 1:
                    self.status_label.setText(f"状态: ✓ 已安装 1 个uv")
                else:
                    self.status_label.setText(f"状态: ✓ 已安装 {count} 个uv")
                
                if self.is_dark_theme:
                    self.status_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
                else:
                    self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self._uv_not_found()
                
        except Exception as e:
            print(f"检测uv时出错: {e}")
            self._uv_not_found()
    
    def _detect_mirror(self):
        """Detect uv mirror configuration"""
        try:
            # 首先检查 uv 配置文件
            config_file = os.path.join(os.path.expanduser("~"), ".uv", "uv.toml")
            config_mirror = None
            
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import re
                    match = re.search(r'index-url\s*=\s*"([^"]+)"', content)
                    if match:
                        config_mirror = match.group(1)
                except:
                    pass
            
            # 检查环境变量
            env_mirror = os.environ.get("UV_INDEX_URL", "")
            
            # 优先使用配置文件中的镜像，然后是环境变量
            if config_mirror:
                self.uv_mirror = config_mirror
                self._set_mirror_selection(config_mirror)
            elif env_mirror:
                self.uv_mirror = env_mirror
                self._set_mirror_selection(env_mirror)
            else:
                # 尝试从 pip 配置检测
                try:
                    pip_result = subprocess.run(
                        ["pip", "config", "get", "global.index-url"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if pip_result.returncode == 0:
                        pip_mirror = pip_result.stdout.strip()
                        if pip_mirror:
                            self.uv_mirror = pip_mirror
                            self._set_mirror_selection(f"{pip_mirror} (从 pip 配置检测)")
                except:
                    pass
                
                if not self.uv_mirror:
                    self.mirror_combo.setCurrentIndex(0)  # 默认镜像
                    
        except Exception as e:
            print(f"检测镜像配置时出错: {e}")
            self.mirror_combo.setCurrentIndex(0)
    
    def _set_mirror_selection(self, mirror_url):
        """根据镜像URL设置下拉框选择"""
        # 检查是否为预设镜像
        preset_mirrors = [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.aliyun.com/pypi/simple", 
            "https://pypi.mirrors.ustc.edu.cn/simple",
            "https://mirrors.cloud.tencent.com/pypi/simple"
        ]
        
        if mirror_url in preset_mirrors:
            index = self.mirror_combo.findText(mirror_url)
            if index >= 0:
                self.mirror_combo.setCurrentIndex(index)
        else:
            # 添加为自定义镜像
            self.mirror_combo.setItemText(self.mirror_combo.count() - 1, f"自定义: {mirror_url}")
            self.mirror_combo.setCurrentIndex(self.mirror_combo.count() - 1)
    
    def _on_uv_path_changed(self, display_text):
        """处理uv路径选择变更"""
        if not display_text:
            return
        
        # 获取选择的uv路径
        current_data = self.path_combo.currentData()
        if current_data == "custom":
            # 用户选择自定义路径
            self._show_custom_path_dialog()
        elif current_data:
            self.uv_path = current_data
            self.path_input.setText(self.uv_path)
            
            # 更新UVManager的自定义路径
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from core.uv_manager import UVManager
                uv_manager = UVManager()
                uv_manager.set_custom_uv_path(self.uv_path)
            except:
                pass
    
    def _on_mirror_changed(self, text):
        """处理镜像地址变更"""
        # 检查是否是特殊选项
        if text == "自定义镜像...":
            self._show_custom_mirror_dialog()
            return
        elif text == "默认镜像":
            # 清除镜像配置
            self.uv_mirror = ""
            self._save_mirror_config()
            return
        
        # 检查是否是自定义镜像（以"自定义:"开头）
        if text.startswith("自定义:"):
            # 提取实际的镜像地址
            actual_mirror = text[4:]  # 去掉"自定义:"前缀
            self.uv_mirror = actual_mirror
            return
        
        # 预设镜像或直接输入的镜像地址
        self.uv_mirror = text
        self._save_mirror_config()
    
    def _show_custom_path_dialog(self):
        """显示自定义路径对话框"""
        from PySide6.QtWidgets import QInputDialog
        
        current_path = self.path_input.text() if self.path_input.text() != "未检测到 uv" else ""
        
        # 设置默认提示文本
        if not current_path:
            current_path = "C:\\path\\to\\uv.exe" if os.name == 'nt' else "/path/to/uv"
        
        path, ok = QInputDialog.getText(
            self,
            "自定义 UV 路径",
            "请输入 UV 可执行文件的完整路径:\n(例如: C:\\Users\\username\\.local\\bin\\uv.exe)",
            text=current_path
        )
        
        if ok and path:
            # 验证路径
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from core.uv_manager import UVManager
                uv_manager = UVManager()
                if uv_manager._verify_uv_executable(path):
                    self.uv_path = path
                    self.path_input.setText(path)
                    self.path_combo.setItemText(self.path_combo.currentIndex(), f"自定义: {path}")
                    self.path_combo.setItemData(self.path_combo.currentIndex(), path)
                    
                    # 更新UVManager
                    uv_manager.set_custom_uv_path(path)
                    
                    QMessageBox.information(self, "成功", "自定义 UV 路径设置成功！")
                else:
                    QMessageBox.warning(self, "错误", "指定的路径不是有效的 UV 可执行文件")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"验证路径时出错: {str(e)}")
        elif ok:
            # 用户取消了输入，恢复到第一个可用选项
            if self.uv_paths:
                self.path_combo.setCurrentIndex(0)
    
    def _show_custom_mirror_dialog(self):
        """显示自定义镜像对话框"""
        from PySide6.QtWidgets import QInputDialog
        
        current_mirror = self.uv_mirror if self.uv_mirror else ""
        
        # 设置默认文本作为提示
        if not current_mirror:
            current_mirror = "https://example.com/simple"
        
        mirror, ok = QInputDialog.getText(
            self,
            "自定义镜像地址",
            "请输入 PyPI 镜像地址:\n(例如: https://pypi.tuna.tsinghua.edu.cn/simple)",
            text=current_mirror
        )
        
        if ok and mirror and mirror != "https://example.com/simple":
            self.uv_mirror = mirror
            self.mirror_combo.setItemText(self.mirror_combo.currentIndex(), f"自定义: {mirror}")
            self._save_mirror_config()
        elif ok:
            # 用户取消了输入或使用了默认提示，恢复到默认镜像
            self.mirror_combo.setCurrentIndex(0)
    
    def _save_mirror_config(self):
        """保存镜像配置到环境变量和文件"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from core.uv_manager import UVManager
            uv_manager = UVManager()
            uv_manager.set_custom_mirror(self.uv_mirror)
        except Exception as e:
            print(f"保存镜像配置时出错: {e}")
    
    def _uv_not_found(self):
        """Handle case when uv is not found"""
        self.uv_path = ""
        self.uv_paths = []
        self.path_combo.clear()
        self.path_combo.addItem("未检测到 uv", "")
        self.path_combo.addItem("自定义路径...", "custom")
        self.path_combo.setEnabled(False)
        self.path_input.setText("未检测到 uv")
        self.path_input.setPlaceholderText("请安装 uv")
        self.mirror_combo.setCurrentIndex(0)
        self.status_label.setText("状态: ✗ 未安装")
        if self.is_dark_theme:
            self.status_label.setStyleSheet("color: #f48771; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    def _install_uv_powershell(self):
        """Install uv using PowerShell"""
        if sys.platform != "win32":
            QMessageBox.warning(self, "不支持", "此安装方法仅支持 Windows 系统。")
            return
        
        reply = QMessageBox.question(
            self,
            "确认安装",
            "将使用 PowerShell 安装 uv，这需要管理员权限。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            command = 'powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"'
            self._start_installation(command)
    
    def _install_uv_pip(self):
        """Install uv using pip"""
        reply = QMessageBox.question(
            self,
            "确认安装",
            "将使用 pip 安装 uv。\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Use python -m pip to ensure we're using the right pip
            command = f'"{sys.executable}" -m pip install uv'
            self._start_installation(command)
    
    def _start_installation(self, command):
        """Start the installation process"""
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText("正在安装...")
        
        # Disable install buttons
        self.install_ps_btn.setEnabled(False)
        self.install_pip_btn.setEnabled(False)
        
        # Create and start worker thread
        self.install_worker = InstallWorker(command)
        self.install_worker.progress.connect(self._on_install_progress)
        self.install_worker.finished.connect(self._on_install_finished)
        self.install_worker.start()
    
    def _on_install_progress(self, message):
        """Handle installation progress updates"""
        self.progress_label.setText(message)
    
    def _on_install_finished(self, success, message):
        """Handle installation completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Re-enable install buttons
        self.install_ps_btn.setEnabled(True)
        self.install_pip_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self,
                "安装成功",
                "UV 已成功安装！\n\n请重新检测以确认。"
            )
            self._detect_uv()
        else:
            QMessageBox.critical(
                self,
                "安装失败",
                f"安装 UV 时出现错误：\n\n{message}\n\n请尝试手动安装。"
            )
