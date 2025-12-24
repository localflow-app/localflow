"""
配置管理类
用于保存和恢复应用程序的各种设置和状态
"""
import json
import os
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_dock_state(self, dock_name: str) -> dict:
        """获取dock窗口状态
        
        Args:
            dock_name: dock窗口名称
            
        Returns:
            dict: 包含visible和width的状态信息
        """
        return self.config.get("dock_states", {}).get(dock_name, {
            "visible": True,
            "width": 300
        })
    
    def set_dock_state(self, dock_name: str, visible: bool = None, width: int = None):
        """设置dock窗口状态
        
        Args:
            dock_name: dock窗口名称
            visible: 可见性
            width: 宽度
        """
        if "dock_states" not in self.config:
            self.config["dock_states"] = {}
        
        if dock_name not in self.config["dock_states"]:
            self.config["dock_states"][dock_name] = {
                "visible": True,
                "width": 300
            }
        
        if visible is not None:
            self.config["dock_states"][dock_name]["visible"] = visible
        
        if width is not None:
            self.config["dock_states"][dock_name]["width"] = width
    
    def apply_dock_state(self, dock_widget, dock_name: str):
        """应用dock窗口状态
        
        Args:
            dock_widget: QDockWidget实例
            dock_name: dock窗口名称
        """
        state = self.get_dock_state(dock_name)
        
        # 应用可见性
        dock_widget.setVisible(state["visible"])
        
        # 应用宽度
        if state["width"] > 0:
            dock_widget.setMinimumWidth(state["width"])
            dock_widget.setMaximumWidth(state["width"] * 2)  # 允许一定程度的调整
    
    def save_dock_state(self, dock_widget, dock_name: str):
        """保存dock窗口状态
        
        Args:
            dock_widget: QDockWidget实例
            dock_name: dock窗口名称
        """
        self.set_dock_state(
            dock_name, 
            visible=dock_widget.isVisible(),
            width=dock_widget.width()
        )
    
    def get_window_geometry(self) -> dict:
        """获取窗口几何信息"""
        return self.config.get("window_geometry", {})
    
    def set_window_geometry(self, x: int, y: int, width: int, height: int):
        """设置窗口几何信息"""
        self.config["window_geometry"] = {
            "x": x, "y": y,
            "width": width, "height": height
        }
    
    def get_recent_workflows(self) -> list:
        """获取最近打开的工作流"""
        return self.config.get("recent_workflows", [])
    
    def add_recent_workflow(self, workflow_name: str, workflow_path: str):
        """添加最近打开的工作流"""
        if "recent_workflows" not in self.config:
            self.config["recent_workflows"] = []
        
        # 移除已存在的记录
        self.config["recent_workflows"] = [
            w for w in self.config["recent_workflows"] 
            if w["name"] != workflow_name
        ]
        
        # 添加到开头
        self.config["recent_workflows"].insert(0, {
            "name": workflow_name,
            "path": workflow_path
        })
        
        # 限制数量
        self.config["recent_workflows"] = self.config["recent_workflows"][:10]