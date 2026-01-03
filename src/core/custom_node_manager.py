"""
自定义节点管理器
管理用户创建的本地节点
"""
import json
import ast
import shutil
import zipfile
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

class CustomNodeManager:
    """自定义节点管理器"""
    
    NODE_TEMPLATE = '''def execute(self, input_data: dict) -> dict:
    """
    执行节点逻辑
    
    Args:
        input_data: 输入数据字典，包含上游节点的输出
        
    Returns:
        输出数据字典，将传递给下游节点
    """
    # 获取配置
    # param1 = self.config.get("param1", "")
    
    # 获取输入
    # input_val = input_data.get("input_key", None)
    
    # TODO: 在此处编写逻辑
    result = {}
    
    return {**input_data, **result}
'''

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
            
            node_def = self._load_node_from_dir(node_dir)
            if node_def:
                nodes.append(node_def)
                    
        return nodes

    def _load_node_from_dir(self, node_dir: Path):
        """从指定目录加载节点定义"""
        from .node_registry import NodeDefinition, NodeSource
        config_file = node_dir / "node.json"
        if not config_file.exists():
            return None
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            node_type = config.get("node_type", node_dir.name)
            node_def = NodeDefinition(
                node_type=node_type,
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
                    
            return node_def
        except Exception as e:
            print(f"加载节点失败 {node_dir}: {e}")
            return None

    def create_node(self, name: str, description: str, category: str = "自定义") -> Optional[Any]:
        """创建新节点"""
        from .node_registry import NodeDefinition, NodeSource
        
        # 转换名称为 node_type (蛇形命名)
        import re
        node_type = re.sub(r'[^\w]', '_', name.lower())
        node_type = f"custom_{node_type}_{datetime.now().strftime('%H%M%S')}"
        
        node_dir = self.custom_nodes_dir / node_type
        if node_dir.exists():
            # 理论上不会重复，因为带了时间戳
            return None
            
        node_dir.mkdir(parents=True)
        
        # 创建 node.json
        config = {
            "node_type": node_type,
            "name": name,
            "description": description,
            "category": category,
            "version": "1.0.0",
            "entry_file": "node.py",
            "dependencies": [],
            "config_schema": {}
        }
        
        with open(node_dir / "node.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        # 创建 node.py
        with open(node_dir / "node.py", 'w', encoding='utf-8') as f:
            f.write(self.NODE_TEMPLATE)
            
        return NodeDefinition(
            node_type=node_type,
            name=name,
            description=description,
            source=NodeSource.CUSTOM,
            category=category,
            source_code=self.NODE_TEMPLATE,
            config_schema={},
            dependencies=[],
            version="1.0.0"
        )

    def save_node(self, node_type: str, source_code: str, config_schema: dict = None, 
                  name: str = None, description: str = None, category: str = None, 
                  dependencies: list = None) -> bool:
        """保存节点修改"""
        node_dir = self.custom_nodes_dir / node_type
        if not node_dir.exists():
            return False
            
        config_file = node_dir / "node.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            return False
            
        # 更新配置
        if config_schema is not None: config["config_schema"] = config_schema
        if name is not None: config["name"] = name
        if description is not None: config["description"] = description
        if category is not None: config["category"] = category
        if dependencies is not None: config["dependencies"] = dependencies
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        # 更新代码
        entry_file = node_dir / config.get("entry_file", "node.py")
        with open(entry_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
            
        return True

    def validate_node(self, source_code: str) -> Tuple[bool, str]:
        """验证节点代码语法"""
        try:
            ast.parse(source_code)
            
            # 检查是否定义了 execute 函数
            has_execute = False
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "execute":
                    # 检查参数
                    # 期待 self, input_data
                    has_execute = True
                    break
            
            if not has_execute:
                return False, "未找到 execute(self, input_data) 函数定义"
                
            return True, "验证通过"
        except SyntaxError as e:
            return False, f"语法错误: {e.msg} (第{e.lineno}行)"
        except Exception as e:
            return False, f"验证失败: {str(e)}"

    def export_node(self, node_type: str, output_path: str) -> bool:
        """导出节点为标准格式 ZIP 包"""
        node_dir = self.custom_nodes_dir / node_type
        if not node_dir.exists():
            return False
            
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in node_dir.iterdir():
                    if file.is_file():
                        zf.write(file, file.name)
            return True
        except Exception as e:
            print(f"导出节点失败: {e}")
            return False

    def delete_node(self, node_type: str) -> bool:
        """删除节点"""
        node_dir = self.custom_nodes_dir / node_type
        if node_dir.exists():
            shutil.rmtree(node_dir)
            return True
        return False
