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
        self._load_mock_external_nodes()  # Phase 1: 使用mock数据
    
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
                modified=True  # Mock: 模拟用户已修改
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
    
    def _load_mock_external_nodes(self):
        """加载Mock外部节点（Phase 1测试用）"""
        mock_nodes = [
            # GitHub 节点
            NodeDefinition(
                node_type="http_request",
                name="HTTP请求",
                description="发送HTTP GET/POST请求",
                source=NodeSource.GITHUB,
                category="网络",
                source_code='''def execute(self, input_data):
    """发送HTTP请求"""
    import requests
    
    url = self.config.get("url", "")
    method = self.config.get("method", "GET")
    output_var = self.config.get("output_var", "response")
    
    if method == "GET":
        response = requests.get(url)
    else:
        response = requests.post(url, json=input_data)
    
    return {
        **input_data,
        output_var: {
            "status_code": response.status_code,
            "body": response.text
        }
    }''',
                config_schema={
                    "url": {"type": "string", "label": "请求URL"},
                    "method": {"type": "enum", "options": ["GET", "POST"], "label": "请求方法"},
                    "output_var": {"type": "string", "label": "输出变量"}
                },
                repo_url="https://github.com/example/http-node"
            ),
            NodeDefinition(
                node_type="json_parse",
                name="JSON解析",
                description="解析JSON字符串为对象",
                source=NodeSource.GITHUB,
                category="数据处理",
                source_code='''def execute(self, input_data):
    """解析JSON字符串"""
    import json
    
    json_var = self.config.get("json_var", "json_str")
    output_var = self.config.get("output_var", "parsed")
    
    json_str = input_data.get(json_var, "{}")
    parsed = json.loads(json_str)
    
    return {**input_data, output_var: parsed}''',
                config_schema={
                    "json_var": {"type": "string", "label": "JSON变量"},
                    "output_var": {"type": "string", "label": "输出变量"}
                },
                repo_url="https://github.com/example/json-node"
            ),
            
            # 内网节点
            NodeDefinition(
                node_type="enterprise_db",
                name="企业数据库",
                description="连接企业内部Oracle数据库",
                source=NodeSource.ENTERPRISE,
                category="企业内部",
                source_code='''def execute(self, input_data):
    """连接企业数据库"""
    # 注意：需要安装 cx_Oracle
    import cx_Oracle
    
    host = self.config.get("host", "db.internal.company.com")
    port = self.config.get("port", "1521")
    service = self.config.get("service", "ORCL")
    username = self.config.get("username", "")
    password = self.config.get("password", "")
    
    dsn = cx_Oracle.makedsn(host, port, service_name=service)
    conn = cx_Oracle.connect(username, password, dsn)
    
    return {
        **input_data,
        "enterprise_conn": {
            "type": "oracle",
            "connected": True
        }
    }''',
                config_schema={
                    "host": {"type": "string", "label": "主机地址"},
                    "port": {"type": "string", "label": "端口"},
                    "service": {"type": "string", "label": "服务名"},
                    "username": {"type": "string", "label": "用户名"},
                    "password": {"type": "password", "label": "密码"}
                },
                repo_url="git@internal.company.com:nodes/enterprise-db.git"
            ),
            NodeDefinition(
                node_type="enterprise_mq",
                name="企业消息队列",
                description="发送消息到企业MQ",
                source=NodeSource.ENTERPRISE,
                category="企业内部",
                source_code='''def execute(self, input_data):
    """发送消息到企业MQ"""
    queue_name = self.config.get("queue_name", "default")
    message_var = self.config.get("message_var", "message")
    
    message = input_data.get(message_var, "")
    
    # 模拟发送到MQ
    print(f"发送消息到队列 {queue_name}: {message}")
    
    return {
        **input_data,
        "mq_result": {"sent": True, "queue": queue_name}
    }''',
                config_schema={
                    "queue_name": {"type": "string", "label": "队列名称"},
                    "message_var": {"type": "string", "label": "消息变量"}
                },
                repo_url="git@internal.company.com:nodes/mq-node.git"
            ),
            
            # 自定义节点
            NodeDefinition(
                node_type="custom_logger",
                name="日志记录",
                description="我的自定义日志节点",
                source=NodeSource.CUSTOM,
                category="自定义",
                source_code='''def execute(self, input_data):
    """记录日志"""
    log_level = self.config.get("log_level", "INFO")
    message_var = self.config.get("message_var", "log_message")
    
    message = input_data.get(message_var, str(input_data))
    
    print(f"[{log_level}] {message}")
    
    return input_data''',
                config_schema={
                    "log_level": {"type": "enum", "options": ["DEBUG", "INFO", "WARNING", "ERROR"], "label": "日志级别"},
                    "message_var": {"type": "string", "label": "消息变量"}
                }
            ),
            NodeDefinition(
                node_type="custom_delay",
                name="延时等待",
                description="等待指定时间后继续",
                source=NodeSource.CUSTOM,
                category="自定义",
                source_code='''def execute(self, input_data):
    """延时等待"""
    import time
    
    seconds = float(self.config.get("seconds", "1"))
    
    print(f"等待 {seconds} 秒...")
    time.sleep(seconds)
    
    return input_data''',
                config_schema={
                    "seconds": {"type": "string", "label": "等待秒数"}
                }
            ),
        ]
        
        for node in mock_nodes:
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
        # Phase 1: 简单实现，删除修改文件
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
