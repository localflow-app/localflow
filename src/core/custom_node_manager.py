"""
自定义节点管理器
管理用户创建的本地节点
"""
import json
from pathlib import Path
from typing import List
from .node_base import NodeSource

class CustomNodeManager:
    """自定义节点管理器 (Phase 1 存根)"""
    
    def __init__(self, user_data_dir: Path):
        self.user_data_dir = user_data_dir
        self.custom_nodes_dir = user_data_dir / "custom_nodes"
        self.custom_nodes_dir.mkdir(parents=True, exist_ok=True)
        
    def load_all_custom_nodes(self) -> List:
        """从本地目录加载所有自定义节点"""
        from .node_registry import NodeDefinition, NodeSource
        nodes = []
        
        if not self.custom_nodes_dir.exists():
            return nodes
            
        for node_dir in self.custom_nodes_dir.iterdir():
            if not node_dir.is_dir(): continue
            
            config_file = node_dir / "node.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        
                    node_def = NodeDefinition(
                        node_type=config.get("node_type", node_dir.name),
                        name=config.get("name", node_dir.name),
                        description=config.get("description", ""),
                        source=NodeSource.CUSTOM,
                        category=config.get("category", "自定义"),
                        source_code="",
                        config_schema=config.get("config_schema", {}),
                        dependencies=config.get("dependencies", []),
                        version=config.get("version", "1.0.0")
                    )
                    
                    entry_file = node_dir / config.get("entry_file", "node.py")
                    if entry_file.exists():
                        with open(entry_file, 'r', encoding='utf-8') as sf:
                            node_def.source_code = sf.read()
                            
                    nodes.append(node_def)
                except Exception as e:
                    print(f"加载自定义节点失败 {node_dir}: {e}")
                    
        return nodes

    def create_node(self, name: str, description: str) -> bool:
        """创建新节点 (存根)"""
        # 将在 Phase 4 详细实现
        return True
