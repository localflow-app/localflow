"""
节点基类和节点类型定义
每个节点都是一个独立的Python脚本
"""
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum


class NodeType(Enum):
    """节点类型枚举"""
    VARIABLE_ASSIGN = "variable_assign"  # 变量赋值
    VARIABLE_CALC = "variable_calc"      # 变量计算
    SQLITE_CONNECT = "sqlite_connect"    # SQLite连接
    SQLITE_EXECUTE = "sqlite_execute"    # SQLite执行
    SQL_STATEMENT = "sql_statement"      # SQL语句


class NodeBase(ABC):
    """节点基类"""
    
    def __init__(self, node_id: str, node_type: NodeType, config: dict = None):
        """
        初始化节点
        
        Args:
            node_id: 节点唯一ID
            node_type: 节点类型
            config: 节点配置
        """
        self.node_id = node_id
        self.node_type = node_type
        self.config = config or {}
        self.inputs = []  # 输入节点ID列表
        self.outputs = []  # 输出节点ID列表
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点逻辑
        
        Args:
            input_data: 输入数据字典
        
        Returns:
            输出数据字典
        """
        pass
    
    def generate_script(self, output_path: str) -> str:
        """
        生成节点的Python脚本文件
        
        Args:
            output_path: 输出路径
        
        Returns:
            脚本文件路径
        """
        script_content = self._get_script_template()
        
        script_path = Path(output_path) / f"node_{self.node_id}.py"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    @abstractmethod
    def _get_script_template(self) -> str:
        """获取脚本模板"""
        pass
    
    def _get_base_script_template(self, execute_code: str) -> str:
        """获取基础脚本模板"""
        config_json = json.dumps(self.config, ensure_ascii=False, indent=2)
        
        return f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节点脚本: {self.node_id}
类型: {self.node_type.value}
"""
import json
import sys

# 节点配置
NODE_CONFIG = {config_json}

def execute(input_data):
    """
    执行节点逻辑
    Args:
        input_data: 输入数据字典
    Returns:
        输出数据字典
    """
    try:
{execute_code}
        return output_data
    except Exception as e:
        raise RuntimeError(f"节点执行错误: {{e}}")

def read_input():
    """从stdin读取输入数据"""
    try:
        input_str = sys.stdin.read()
        if input_str:
            return json.loads(input_str)
        return {{}}
    except:
        return {{}}

def write_output(data):
    """写入输出数据到stdout"""
    print("###JSON_OUTPUT###")
    print(json.dumps(data, ensure_ascii=False))
    print("###JSON_OUTPUT_END###")

def main():
    """主执行函数"""
    input_data = read_input()
    
    try:
        output_data = execute(input_data)
        
        # 输出结果
        write_output(output_data)
        return 0
    except Exception as e:
        print(f"节点执行错误: {{e}}", file=sys.stderr)
        write_output({{"error": str(e)}})
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "config": self.config,
            "inputs": self.inputs,
            "outputs": self.outputs
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NodeBase':
        """从字典创建节点"""
        node_type_str = data["node_type"]
        
        # 尝试转换为枚举
        try:
            node_type = NodeType(node_type_str)
        except ValueError:
            node_type = None
            
        # 根据类型创建对应的节点实例
        if node_type == NodeType.VARIABLE_ASSIGN:
            node = VariableAssignNode(data["node_id"], data["config"])
        elif node_type == NodeType.VARIABLE_CALC:
            node = VariableCalcNode(data["node_id"], data["config"])
        elif node_type == NodeType.SQLITE_CONNECT:
            node = SQLiteConnectNode(data["node_id"], data["config"])
        elif node_type == NodeType.SQLITE_EXECUTE:
            node = SQLiteExecuteNode(data["node_id"], data["config"])
        elif node_type == NodeType.SQL_STATEMENT:
            node = SQLStatementNode(data["node_id"], data["config"])
        else:
            # 外部或自定义节点
            from src.core.node_registry import get_registry
            registry = get_registry()
            node_def = registry.get_node(node_type_str)
            
            if node_def:
                node = CustomNode(data["node_id"], node_type_str, data["config"])
                # 注入源代码，供模板使用
                node.source_code = node_def.source_code
            else:
                # 允许空节点占位，或者抛出异常
                print(f"警告: 未找到节点类型 {node_type_str} 的定义，将作为通用自定义节点处理")
                node = CustomNode(data["node_id"], node_type_str, data["config"])
        
        node.inputs = data.get("inputs", [])
        node.outputs = data.get("outputs", [])
        return node


class CustomNode(NodeBase):
    """外部导入或自定义节点"""
    
    def __init__(self, node_id: str, node_type_str: str, config: dict = None):
        # 注意：这里的 node_type 参数由于 NodeBase 的类型提示是 NodeType 枚举，
        # 在运行时期我们传入字符串，IDE 可能会报错，但 Python 运行没问题。
        # 为了规范，我们可以给 NodeBase.__init__ 的类型提示加 Union[NodeType, str]
        super().__init__(node_id, node_type_str, config)
        self.source_code = ""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        在当前进程执行自定义节点
        注意：复杂节点建议在虚拟环境中通过 generate_script 执行
        """
        # 这里可以使用 exec 实现本地执行，但出于安全和依赖考虑，
        # 多数情况下应通过 WorkflowExecutor 的 Worker 模式运行生成后的脚本。
        # 这里返回空或模拟
        return {**input_data}

    def _get_script_template(self) -> str:
        """获取脚本模板（直接使用存储的源代码）"""
        if not self.source_code:
            from src.core.node_registry import get_registry
            registry = get_registry()
            # 这里 node_type 在 CustomNode 中是字符串
            self.source_code = registry.get_source_code(self.node_type)
            
        # 查找 execute 函数的缩进并处理
        # 我们的基础模板 expect $execute_code 已经在函数体内
        # 而自定义节点的代码本身就是一个完整的 def execute(...)
        # 所以我们需要调整基础模板或者调整插入策略
        
        # 策略：如果自定义代码包含 'def execute', 我们需要一个更简单的基础模板
        # 或者直接使用自定义代码作为脚本的主体，并包装 read_input/write_output
        
        return f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

# 节点配置
NODE_CONFIG = {json.dumps(self.config, ensure_ascii=False, indent=2)}

{self.source_code}

def main():
    try:
        input_str = sys.stdin.read()
        input_data = json.loads(input_str) if input_str else {{}}
        
        # 实例化一个哑对象来作为 self 传递（如果代码中的 execute 是类成员方法或者期待 self）
        # 我们的模板通常写成 def execute(self, input_data):
        class NodeShim:
            def __init__(self, config):
                self.config = config
        
        shim = NodeShim(NODE_CONFIG)
        output_data = execute(shim, input_data)
        
        print("###JSON_OUTPUT###")
        print(json.dumps(output_data, ensure_ascii=False))
        print("###JSON_OUTPUT_END###")
    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''


class VariableAssignNode(NodeBase):
    """变量赋值节点"""
    
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, NodeType.VARIABLE_ASSIGN, config)
        # config: {"variable_name": "x", "value": "100", "value_type": "int"}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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
            value = json.loads(value)
        
        return {var_name: value}
    
    def _get_script_template(self) -> str:
        execute_code = '''        # 变量赋值逻辑
        var_name = NODE_CONFIG.get("variable_name", "result")
        value = NODE_CONFIG.get("value", "")
        value_type = NODE_CONFIG.get("value_type", "str")
        
        # 类型转换
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            value = json.loads(value)
        
        output_data = {var_name: value}'''
        
        return self._get_base_script_template(execute_code)


class VariableCalcNode(NodeBase):
    """变量计算节点"""
    
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, NodeType.VARIABLE_CALC, config)
        # config: {"expression": "x + y * 2", "output_var": "result"}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行变量计算"""
        expression = self.config.get("expression", "0")
        output_var = self.config.get("output_var", "result")
        
        # 使用输入数据作为计算上下文
        context = {**input_data}
        result = eval(expression, {"__builtins__": {}}, context)
        
        return {**input_data, output_var: result}
    
    def _get_script_template(self) -> str:
        execute_code = '''        # 变量计算逻辑
        expression = NODE_CONFIG.get("expression", "0")
        output_var = NODE_CONFIG.get("output_var", "result")
        
        # 使用输入数据作为计算上下文
        context = {**input_data}
        result = eval(expression, {"__builtins__": {}}, context)
        
        output_data = {**input_data, output_var: result}'''
        
        return self._get_base_script_template(execute_code)


class SQLiteConnectNode(NodeBase):
    """SQLite数据库连接节点"""
    
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, NodeType.SQLITE_CONNECT, config)
        # config: {"db_path": "./data.db", "connection_name": "db_conn"}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库连接"""
        db_path = self.config.get("db_path", ":memory:")
        conn_name = self.config.get("connection_name", "db_conn")
        
        # 返回连接信息（实际连接在脚本中建立）
        return {
            **input_data,
            conn_name: {
                "type": "sqlite",
                "db_path": db_path,
                "connected": True
            }
        }
    
    def _get_script_template(self) -> str:
        execute_code = '''        # SQLite连接逻辑
        import sqlite3
        
        db_path = NODE_CONFIG.get("db_path", ":memory:")
        conn_name = NODE_CONFIG.get("connection_name", "db_conn")
        
        # 建立连接
        conn = sqlite3.connect(db_path)
        
        # 返回连接信息
        output_data = {
            **input_data,
            conn_name: {
                "type": "sqlite",
                "db_path": db_path,
                "connected": True
            }
        }
        
        conn.close()'''
        
        return self._get_base_script_template(execute_code)


class SQLiteExecuteNode(NodeBase):
    """SQLite数据库执行节点"""
    
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, NodeType.SQLITE_EXECUTE, config)
        # config: {"connection_name": "db_conn", "sql_var": "sql", "output_var": "query_result"}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行SQL语句"""
        conn_name = self.config.get("connection_name", "db_conn")
        sql_var = self.config.get("sql_var", "sql")
        output_var = self.config.get("output_var", "query_result")
        
        # 这里只是模拟，实际执行在脚本中
        return {
            **input_data,
            output_var: []
        }
    
    def _get_script_template(self) -> str:
        execute_code = '''        # SQLite执行逻辑
        import sqlite3
        
        conn_name = NODE_CONFIG.get("connection_name", "db_conn")
        sql_var = NODE_CONFIG.get("sql_var", "sql")
        output_var = NODE_CONFIG.get("output_var", "query_result")
        
        # 获取连接信息和SQL语句
        conn_info = input_data.get(conn_name, {})
        sql = input_data.get(sql_var, "")
        
        if not sql:
            raise ValueError("SQL语句为空")
        
        # 连接数据库并执行
        db_path = conn_info.get("db_path", ":memory:")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            
            # 如果是查询语句，获取结果
            if sql.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
            else:
                # 非查询语句，返回影响的行数
                conn.commit()
                result = {"affected_rows": cursor.rowcount}
            
            output_data = {**input_data, output_var: result}
        finally:
            cursor.close()
            conn.close()'''
        
        return self._get_base_script_template(execute_code)


class SQLStatementNode(NodeBase):
    """SQL语句节点"""
    
    def __init__(self, node_id: str, config: dict = None):
        super().__init__(node_id, NodeType.SQL_STATEMENT, config)
        # config: {"sql": "SELECT * FROM users WHERE id = {user_id}", "output_var": "sql"}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成SQL语句"""
        sql_template = self.config.get("sql", "")
        output_var = self.config.get("output_var", "sql")
        
        # 使用输入数据格式化SQL
        sql = sql_template.format(**input_data)
        
        return {**input_data, output_var: sql}
    
    def _get_script_template(self) -> str:
        execute_code = '''        # SQL语句生成逻辑
        sql_template = NODE_CONFIG.get("sql", "")
        output_var = NODE_CONFIG.get("output_var", "sql")
        
        # 使用输入数据格式化SQL
        sql = sql_template.format(**input_data)
        
        output_data = {**input_data, output_var: sql}'''
        
        return self._get_base_script_template(execute_code)
