"""
GitHub 社区节点提供者
负责从 GitHub 仓库下载、安装和管理外部节点
"""
import os
import json
import re
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
from ..node_registry import NodeSource, NodeDefinition, get_registry

class GitHubNodeProvider:
    """GitHub 节点管理器"""
    
    def __init__(self, user_data_dir: Path):
        self.user_data_dir = user_data_dir
        self.github_dir = user_data_dir / "external_nodes" / "github"
        self.github_dir.mkdir(parents=True, exist_ok=True)
        
    def parse_url(self, url: str) -> Optional[Tuple[str, str]]:
        """
        解析 GitHub URL 获取作者和仓库名
        支持格式: 
        - https://github.com/owner/repo
        - owner/repo
        """
        url = url.strip()
        if not url:
            return None
            
        # 匹配 owner/repo 格式
        pattern = r"(?:https?://github\.com/)?([^/]+)/([^/.]+)(?:\.git)?(?:/.*)?"
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
        return None

    def fetch_node_info(self, url: str) -> Tuple[bool, Optional[dict]]:
        """
        从 GitHub 获取节点信息 (node.json)
        目前为 Mock 实现，后续可接入 GitHub API 或 raw.githubusercontent.com
        """
        parsed = self.parse_url(url)
        if not parsed:
            return False, {"error": "无效的 GitHub URL"}
            
        owner, repo = parsed
        
        # MOCK: 模拟 API 请求返回
        # 实际生产中应使用 requests.get(f"https://raw.githubusercontent.com/{owner}/{repo}/main/node.json")
        mock_info = {
            "node_type": f"github_{owner}_{repo}".lower(),
            "name": f"{repo} (GitHub)",
            "description": f"从 GitHub 仓库 {owner}/{repo} 导入的节点",
            "category": "GitHub",
            "entry_file": "node.py",
            "dependencies": ["requests"],
            "version": "1.0.0",
            "repo_url": url
        }
        
        return True, mock_info

    def download_node(self, url: str) -> Optional[NodeDefinition]:
        """
        下载并注册节点
        """
        parsed = self.parse_url(url)
        if not parsed:
            return None
            
        owner, repo = parsed
        success, info = self.fetch_node_info(url)
        if not success:
            return None
            
        node_type = info["node_type"]
        node_dir = self.github_dir / owner / repo
        node_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存 node.json
        with open(node_dir / "node.json", 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
            
        # 2. 下载/生成 entry_file (Mock 源代码)
        entry_file = node_dir / info.get("entry_file", "node.py")
        
        # MOCK: 模拟下载的源代码
        source_code = f'''def execute(self, input_data):
    """
    GitHub 节点: {info['name']}
    来源: {url}
    """
    print(f"执行来自 GitHub 的节点: {owner}/{repo}")
    
    # 示例逻辑：返回节点信息和输入
    return {{
        **input_data,
        "{node_type}_status": "success",
        "repo": "{owner}/{repo}"
    }}
'''
        with open(entry_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
            
        # 3. 创建 NodeDefinition 并注册
        node_def = NodeDefinition(
            node_type=node_type,
            name=info["name"],
            description=info["description"],
            source=NodeSource.GITHUB,
            category=info["category"],
            source_code=source_code,
            config_schema=info.get("config_schema", {}),
            repo_url=url,
            dependencies=info.get("dependencies", []),
            version=info.get("version", "1.0.0")
        )
        
        registry = get_registry()
        registry.register_external_node(node_def)
        
        return node_def

    def delete_node(self, node_type: str) -> bool:
        """删除导入的 GitHub 节点"""
        registry = get_registry()
        node_def = registry.get_node(node_type)
        if not node_def or node_def.source != NodeSource.GITHUB:
            return False
            
        # 解析 URL 以寻找目录
        parsed = self.parse_url(node_def.repo_url)
        if not parsed:
            return False
            
        owner, repo = parsed
        node_dir = self.github_dir / owner / repo
        
        if node_dir.exists():
            shutil.rmtree(node_dir)
            registry.unregister_node(node_type)
            return True
        return False
