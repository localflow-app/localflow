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


class NodeRegistry:
    """节点注册表"""
    
    def __init__(self):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._user_data_dir = Path("user_data")
        self._load_official_nodes()
    
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
    

    
    # === 查询方法 ===
    
    def get_all_nodes(self) -> List[dict]:
        """获取所有节点（转换为字典格式供UI使用）"""
        result = []
        for node in self._nodes.values():
            result.append(self._node_to_dict(node))
        return result
    
    def get_node(self, node_type: str) -> Optional[NodeDefinition]:
        """获取指定节点"""
        return self._nodes.get(node_type)
    
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
        }
    
    # === 源代码管理 ===
    
    def get_source_code(self, node_type: str) -> str:
        """获取节点源代码"""
        node = self._nodes.get(node_type)
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
        node.modified = True
        
        # 持久化到文件
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
    
    def get_node_info(self, node_type: str) -> dict:
        """获取节点显示信息"""
        node = self._nodes.get(node_type)
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
