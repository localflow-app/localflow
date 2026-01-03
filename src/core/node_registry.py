"""
节点注册表
管理所有节点的元数据、源代码和修改状态
"""
import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


class NodeSource(Enum):
    """节点来源枚举"""
    OFFICIAL = "official"        # 官方节点
    GITHUB = "github"            # GitHub社区节点
    ENTERPRISE = "enterprise"    # 企业内网节点
    CUSTOM = "custom"            # 用户自定义节点


# 节点来源显示信息
NODE_SOURCE_INFO = {
    NodeSource.OFFICIAL: {"name": "官方", "color": "#4CAF50"},
    NodeSource.GITHUB: {"name": "GitHub", "color": "#6e5494"},
    NodeSource.ENTERPRISE: {"name": "内网", "color": "#FF9800"},
    NodeSource.CUSTOM: {"name": "自定义", "color": "#2196F3"},
}


@dataclass
class NodeDefinition:
    """节点定义"""
    node_type: str           # 节点类型标识
    name: str                # 显示名称
    description: str         # 描述
    source: NodeSource       # 来源
    category: str            # 分类
    source_code: str         # 源代码（execute函数）
    config_schema: Dict      # 配置项定义
    modified: bool = False   # 是否被用户修改
    repo_url: str = ""       # 来源仓库URL（GitHub/内网节点）
    dependencies: List[str] = field(default_factory=list)  # pip 依赖包列表
    version: str = "1.0.0"   # 节点版本


class NodeRegistry:
    """节点注册表"""
    
    def __init__(self):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._user_data_dir = Path("user_data")
        self._load_official_nodes()
        self._load_external_nodes()
    
    def _load_official_nodes(self):
        """加载官方节点"""
        official_nodes = [
            NodeDefinition(
                node_type="variable_assign",
                name="变量赋值",
                description="创建变量并赋值",
                source=NodeSource.OFFICIAL,
                category="变量操作",
                source_code='''def execute(self, input_data):
    """执行变量赋值"""
    var_name = self.config.get("variable_name", "result")
    value = self.config.get("value", "")
    value_type = self.config.get("value_type", "str")
    
    # 类型转换
    if value_type == "int":
        value = int(value)
    elif value_type == "float":
        value = float(value)
    elif value_type == "bool":
        value = value.lower() in ("true", "1", "yes")
    elif value_type == "json":
        import json
        value = json.loads(value)
    
    return {var_name: value}''',
                config_schema={
                    "variable_name": {"type": "string", "label": "变量名"},
                    "value": {"type": "string", "label": "值"},
                    "value_type": {"type": "enum", "options": ["str", "int", "float", "bool", "json"], "label": "类型"}
                }
            ),
            NodeDefinition(
                node_type="variable_calc",
                name="变量计算",
                description="使用表达式计算变量",
                source=NodeSource.OFFICIAL,
                category="变量操作",
                source_code='''def execute(self, input_data):
    """执行变量计算"""
    expression = self.config.get("expression", "0")
    output_var = self.config.get("output_var", "result")
    
    # 使用输入数据作为计算上下文
    context = {**input_data}
    result = eval(expression, {"__builtins__": {}}, context)
    
    return {**input_data, output_var: result}''',
                config_schema={
                    "expression": {"type": "string", "label": "表达式"},
                    "output_var": {"type": "string", "label": "输出变量"}
                },
                modified=False
            ),
            NodeDefinition(
                node_type="sqlite_connect",
                name="SQLite连接",
                description="连接SQLite数据库",
                source=NodeSource.OFFICIAL,
                category="数据库",
                source_code='''def execute(self, input_data):
    """执行数据库连接"""
    import sqlite3
    
    db_path = self.config.get("db_path", ":memory:")
    conn_name = self.config.get("connection_name", "db_conn")
    
    # 建立连接
    conn = sqlite3.connect(db_path)
    
    return {
        **input_data,
        conn_name: {
            "type": "sqlite",
            "db_path": db_path,
            "connected": True
        }
    }''',
                config_schema={
                    "db_path": {"type": "string", "label": "数据库路径"},
                    "connection_name": {"type": "string", "label": "连接名称"}
                }
            ),
            NodeDefinition(
                node_type="sql_statement",
                name="SQL语句",
                description="构建SQL查询语句",
                source=NodeSource.OFFICIAL,
                category="数据库",
                source_code='''def execute(self, input_data):
    """生成SQL语句"""
    sql_template = self.config.get("sql", "")
    output_var = self.config.get("output_var", "sql")
    
    # 使用输入数据格式化SQL
    sql = sql_template.format(**input_data)
    
    return {**input_data, output_var: sql}''',
                config_schema={
                    "sql": {"type": "text", "label": "SQL语句"},
                    "output_var": {"type": "string", "label": "输出变量"}
                }
            ),
            NodeDefinition(
                node_type="sqlite_execute",
                name="SQLite执行",
                description="执行SQL语句",
                source=NodeSource.OFFICIAL,
                category="数据库",
                source_code='''def execute(self, input_data):
    """执行SQL语句"""
    import sqlite3
    
    conn_name = self.config.get("connection_name", "db_conn")
    sql_var = self.config.get("sql_var", "sql")
    output_var = self.config.get("output_var", "query_result")
    
    conn_info = input_data.get(conn_name, {})
    sql = input_data.get(sql_var, "")
    
    if not sql:
        raise ValueError("SQL语句为空")
    
    db_path = conn_info.get("db_path", ":memory:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result = {"affected_rows": cursor.rowcount}
        
        return {**input_data, output_var: result}
    finally:
        cursor.close()
        conn.close()''',
                config_schema={
                    "connection_name": {"type": "string", "label": "连接名称"},
                    "sql_var": {"type": "string", "label": "SQL变量"},
                    "output_var": {"type": "string", "label": "输出变量"}
                }
            ),
        ]
        
        for node in official_nodes:
            self._nodes[node.node_type] = node
    
    def _load_external_nodes(self):
        """加载外部和下载的节点"""
        # 加载自定义节点
        from src.core.custom_node_manager import CustomNodeManager
        manager = CustomNodeManager(self._user_data_dir)
        custom_nodes = manager.load_all_custom_nodes()
        for node in custom_nodes:
            self._nodes[node.node_type] = node
            
        # 加载外部下载的节点 (GitHub/Enterprise)
        external_dir = self._user_data_dir / "external_nodes"
        if not external_dir.exists():
            return
            
        # 遍历外部节点目录
        for source_dir in external_dir.iterdir():
            if not source_dir.is_dir(): continue
            for node_dir in source_dir.iterdir():
                if not node_dir.is_dir(): continue
                
                config_file = node_dir / "node.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            # 从配置文件创建 NodeDefinition
                            node_def = NodeDefinition(
                                node_type=config.get("node_type", node_dir.name),
                                name=config.get("name", node_dir.name),
                                description=config.get("description", ""),
                                source=NodeSource(source_dir.name),
                                category=config.get("category", "外部"),
                                source_code="", # 将在运行时按需加载或通过 read_file
                                config_schema=config.get("config_schema", {}),
                                repo_url=config.get("repo_url", ""),
                                dependencies=config.get("dependencies", []),
                                version=config.get("version", "1.0.0")
                            )
                            # 读取源代码
                            entry_file = node_dir / config.get("entry_file", "node.py")
                            if entry_file.exists():
                                with open(entry_file, 'r', encoding='utf-8') as sf:
                                    node_def.source_code = sf.read()
                                    
                            self._nodes[node_def.node_type] = node_def
                    except Exception as e:
                        print(f"加载外部节点失败 {node_dir}: {e}")

    def register_external_node(self, node_def: NodeDefinition) -> bool:
        """注册外部节点"""
        self._nodes[node_def.node_type] = node_def
        return True

    def unregister_node(self, node_type: str) -> bool:
        """注销节点"""
        if node_type in self._nodes:
            del self._nodes[node_type]
            return True
        return False
    

    
    # === 查询方法 ===
    
    def get_all_nodes(self) -> List[dict]:
        """获取所有节点（转换为字典格式供UI使用）"""
        result = []
        for node in self._nodes.values():
            result.append(self._node_to_dict(node))
        return result
    
    def get_node(self, node_type) -> Optional[NodeDefinition]:
        """获取指定节点 (支持枚举 or 字符串)"""
        # 直接尝试获取
        node = self._nodes.get(node_type)
        if node:
            return node
            
        # 如果是字符串，尝试匹配枚举键
        if isinstance(node_type, str):
            for key, val in self._nodes.items():
                if hasattr(key, 'value') and key.value == node_type:
                    return val
        
        # 如果是枚举，尝试直接用其值字符串匹配
        if hasattr(node_type, 'value'):
            return self._nodes.get(node_type.value)
            
        return None
    
    def get_nodes_by_source(self, source: NodeSource) -> List[NodeDefinition]:
        """按来源获取节点"""
        return [n for n in self._nodes.values() if n.source == source]
    
    def _node_to_dict(self, node: NodeDefinition) -> dict:
        """将NodeDefinition转换为字典"""
        from src.core.node_base import NodeType
        
        # 尝试获取对应的NodeType枚举
        try:
            node_type_enum = NodeType(node.node_type)
        except ValueError:
            node_type_enum = None
        
        return {
            "type": node_type_enum,  # 可能为None（外部节点）
            "type_str": node.node_type,
            "name": node.name,
            "description": node.description,
            "source": node.source,
            "category": node.category,
            "modified": node.modified,
            "color": NODE_SOURCE_INFO[node.source]["color"],
            "repo_url": node.repo_url,
            "dependencies": node.dependencies,
            "version": node.version
        }
    
    # === 源代码管理 ===
    
    def get_source_code(self, node_type) -> str:
        """获取节点源代码"""
        node = self.get_node(node_type)
        if node:
            return node.source_code
        return ""
    
    def save_modified_source(self, node_type: str, source_code: str) -> bool:
        """保存修改后的源代码"""
        node = self._nodes.get(node_type)
        if not node:
            return False
        
        # 更新内存中的源代码
        node.source_code = source_code
        
        if node.source == NodeSource.CUSTOM:
            # 自定义节点：直接保存到其目录
            from src.core.custom_node_manager import CustomNodeManager
            manager = CustomNodeManager(self._user_data_dir)
            return manager.save_node(node_type, source_code)
        else:
            # 官方或其他节点：作为修改覆盖保存
            node.modified = True
            modified_dir = self._user_data_dir / "modified_nodes"
            modified_dir.mkdir(parents=True, exist_ok=True)
            
            modified_file = modified_dir / f"{node_type}.py"
            with open(modified_file, 'w', encoding='utf-8') as f:
                f.write(source_code)
            
            return True
    
    def reset_to_original(self, node_type: str) -> bool:
        """重置为原始源代码"""
        # 简单实现，删除修改文件
        node = self._nodes.get(node_type)
        if not node:
            return False
        
        modified_file = self._user_data_dir / "modified_nodes" / f"{node_type}.py"
        if modified_file.exists():
            modified_file.unlink()
        
        node.modified = False
        # 重新加载原始代码（这里简化处理，实际需要重新加载）
        return True
    
    def is_modified(self, node_type: str) -> bool:
        """检查节点是否被修改"""
        node = self._nodes.get(node_type)
        return node.modified if node else False
    
    def get_node_info(self, node_type) -> dict:
        """获取节点显示信息"""
        node = self.get_node(node_type)
        if node:
            return {
                "name": node.name,
                "source": node.source,
                "source_info": NODE_SOURCE_INFO[node.source]
            }
        # 返回默认信息
        return {
            "name": node_type,
            "source": NodeSource.OFFICIAL,
            "source_info": NODE_SOURCE_INFO[NodeSource.OFFICIAL]
        }


# 全局单例
_registry_instance = None

def get_registry() -> NodeRegistry:
    """获取全局节点注册表实例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = NodeRegistry()
    return _registry_instance
