"""
工作流执行引擎
负责工作流的执行、节点调度、数据传递
"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

from .node_base import NodeBase, NodeType
from .uv_manager import UVManager


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, workflow_name: str, uv_manager: UVManager = None):
        """
        初始化工作流执行器
        
        Args:
            workflow_name: 工作流名称
            uv_manager: UV管理器实例
        """
        self.workflow_name = workflow_name
        self.uv_manager = uv_manager or UVManager()
        self.nodes: Dict[str, NodeBase] = {}
        self.edges: List[tuple] = []  # (from_node_id, to_node_id)
        self.execution_order: List[str] = []
        self.context: Dict[str, Any] = {}  # 执行上下文
    
    def add_node(self, node: NodeBase):
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, from_node_id: str, to_node_id: str):
        """添加边（连接）"""
        self.edges.append((from_node_id, to_node_id))
        
        # 更新节点的输入输出
        if from_node_id in self.nodes:
            self.nodes[from_node_id].outputs.append(to_node_id)
        if to_node_id in self.nodes:
            self.nodes[to_node_id].inputs.append(from_node_id)
    
    def prepare_environment(self, python_version: str = None, packages: List[str] = None) -> bool:
        """
        准备工作流执行环境
        
        Args:
            python_version: Python版本
            packages: 需要额外安装的包列表
        
        Returns:
            是否准备成功
        """
        # 1. 自动从节点收集依赖
        all_dependencies = self._collect_node_dependencies()
        
        # 2. 合并手动指定的包
        if packages:
            all_dependencies.extend(packages)
            
        # 3. 解析依赖（去重等）
        resolved_packages = self._resolve_dependencies(all_dependencies)
        
        # 创建虚拟环境
        if not self.uv_manager.create_workflow_env(self.workflow_name, python_version):
            return False
        
        # 安装依赖包
        if resolved_packages:
            print(f"正在安装工作流依赖: {resolved_packages}")
            if not self.uv_manager.install_packages(self.workflow_name, resolved_packages):
                return False
        
        return True

    def _collect_node_dependencies(self) -> List[str]:
        """收集工作流中所有节点声明的依赖"""
        from .node_registry import get_registry
        registry = get_registry()
        dependencies = []
        
        # 检查每个节点的定义，获取其 dependencies 列表
        seen_types = set()
        for node in self.nodes.values():
            node_type_str = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
            if node_type_str in seen_types:
                continue
                
            node_def = registry.get_node(node_type_str)
            if node_def and node_def.dependencies:
                dependencies.extend(node_def.dependencies)
            seen_types.add(node_type_str)
            
        return dependencies

    def _resolve_dependencies(self, dependencies: List[str]) -> List[str]:
        """解析并去重依赖，检测基本冲突"""
        if not dependencies:
            return []
            
        # 1. 清理和去重
        cleaned = sorted(list(set([d.strip() for d in dependencies if d.strip()])))
        
        # 2. 基本冲突检测 (同一包名由于不同版本声明)
        packages = {}
        for dep in cleaned:
            # 简单分割包名和版本提示 (例如 requests>=2.0.0)
            import re
            match = re.match(r'^([a-zA-Z0-9_\-\[\]]+)', dep)
            if match:
                pkg_name = match.group(1).lower().replace('_', '-')
                if pkg_name in packages and packages[pkg_name] != dep:
                    print(f"警告: 检测到潜在依赖冲突: '{packages[pkg_name]}' vs '{dep}'")
                packages[pkg_name] = dep
                
        return cleaned
    
    def _topological_sort(self) -> List[str]:
        """
        拓扑排序，确定节点执行顺序
        
        Returns:
            节点ID列表（执行顺序）
        """
        # 计算入度
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = 0
        
        for from_id, to_id in self.edges:
            in_degree[to_id] += 1
        
        # BFS拓扑排序
        queue = [node_id for node_id in self.nodes if in_degree[node_id] == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # 更新后继节点的入度
            for from_id, to_id in self.edges:
                if from_id == node_id:
                    in_degree[to_id] -= 1
                    if in_degree[to_id] == 0:
                        queue.append(to_id)
        
        # 检查是否有环
        if len(result) != len(self.nodes):
            raise ValueError("工作流中存在环路，无法执行")
        
        return result
    
    def generate_scripts(self) -> Dict[str, str]:
        """
        为所有节点生成Python脚本
        
        Returns:
            节点ID到脚本路径的映射
        """
        workflow_dir = self.uv_manager.get_workflow_dir(self.workflow_name)
        scripts_dir = workflow_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        script_paths = {}
        for node_id, node in self.nodes.items():
            script_path = node.generate_script(str(scripts_dir))
            script_paths[node_id] = script_path
        
        return script_paths
    
    def execute_node(self, node_id: str, input_data: Dict[str, Any] = None, worker_process = None) -> Dict[str, Any]:
        """
        执行单个节点
        
        Args:
            node_id: 节点ID
            input_data: 输入数据
            worker_process: 可选的Worker进程对象
        
        Returns:
            节点输出数据
        """
        if node_id not in self.nodes:
            raise ValueError(f"节点不存在: {node_id}")
        
        node = self.nodes[node_id]
        
        # 生成脚本
        workflow_dir = self.uv_manager.get_workflow_dir(self.workflow_name)
        scripts_dir = workflow_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        script_path = node.generate_script(str(scripts_dir))
        
        print(f"执行节点: {node_id} ({node.node_type.value})")
        
        # 如果有Worker进程，优先使用Worker
        if worker_process:
            command = {
                "type": "run_node",
                "script_path": script_path,
                "input_data": input_data or {}
            }
            result = self.uv_manager.send_command_to_worker(worker_process, command)
        else:
            # 否则回退到传统方式
            result = self.uv_manager.run_python_script(
                self.workflow_name,
                script_path,
                input_data or {}
            )
        
        if not result["success"]:
            raise RuntimeError(f"节点执行失败: {result['error']}")
        
        return result["data"] or {}
    
    def execute(self, initial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行整个工作流
        
        Args:
            initial_data: 初始输入数据
        
        Returns:
            最终输出数据
        """
        # 确定执行顺序
        self.execution_order = self._topological_sort()
        print(f"执行顺序: {self.execution_order}")
        
        # 初始化上下文
        self.context = initial_data or {}
        
        # 生成所有脚本
        script_paths = self.generate_scripts()
        print(f"已生成 {len(script_paths)} 个节点脚本")
        
        # 启动Worker进程
        worker_process = None
        try:
            print("正在启动工作流执行引擎...")
            worker_process = self.uv_manager.start_worker(self.workflow_name)
            if worker_process:
                print("工作流执行引擎启动成功")
            else:
                print("工作流执行引擎启动失败，将使用传统模式执行")
                
            # 按顺序执行节点
            for node_id in self.execution_order:
                node = self.nodes[node_id]
                
                # 收集输入数据
                input_data = self.context.copy()
                
                # 执行节点
                try:
                    output_data = self.execute_node(node_id, input_data, worker_process)
                    
                    # 更新上下文
                    self.context.update(output_data)
                    
                    print(f"节点 {node_id} 执行成功")
                    
                except Exception as e:
                    print(f"节点 {node_id} 执行失败: {e}")
                    raise
        finally:
            # 清理Worker进程
            if worker_process:
                try:
                    # 发送退出命令
                    self.uv_manager.send_command_to_worker(worker_process, {"type": "exit"}, timeout=2)
                    worker_process.terminate()
                    worker_process.wait(timeout=2)
                except:
                    if worker_process.poll() is None:
                        worker_process.kill()
                print("工作流执行引擎已关闭")
        
        return self.context
    
    def save_workflow(self, file_path: str, node_positions: dict = None):
        """保存工作流到文件
        
        Args:
            file_path: 保存路径
            node_positions: 节点位置信息 {node_id: {"x": x, "y": y}}
        """
        workflow_data = {
            "workflow_name": self.workflow_name,
            "nodes": [],
            "edges": self.edges,
            "dependencies": self._collect_node_dependencies()  # 保存依赖快照
        }
        
        # 保存节点数据（包括位置）
        for node in self.nodes.values():
            node_dict = node.to_dict()
            if node_positions and node.node_id in node_positions:
                node_dict["position"] = node_positions[node.node_id]
            workflow_data["nodes"].append(node_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_workflow(cls, file_path: str, uv_manager: UVManager = None) -> 'WorkflowExecutor':
        """从文件加载工作流"""
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        executor = cls(workflow_data["workflow_name"], uv_manager)
        
        # 加载节点
        for node_data in workflow_data["nodes"]:
            node = NodeBase.from_dict(node_data)
            executor.add_node(node)
        
        # 加载边
        for from_id, to_id in workflow_data["edges"]:
            executor.add_edge(from_id, to_id)
        
        return executor
    
    def get_execution_stats(self) -> dict:
        """获取执行统计信息"""
        return {
            "workflow_name": self.workflow_name,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "execution_order": self.execution_order,
            "context_keys": list(self.context.keys())
        }
