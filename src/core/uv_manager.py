"""
UV环境管理器
管理每个工作流的Python虚拟环境（使用uv的共享缓存）
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, List


class UVManager:
    """UV虚拟环境管理器"""
    
    def __init__(self, workspace_root: str = None):
        """
        初始化UV管理器
        
        Args:
            workspace_root: 工作空间根目录，默认为 ./workflows
        """
        if workspace_root is None:
            workspace_root = os.path.join(os.getcwd(), "workflows")
        
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.custom_uv_path = None
        self.custom_mirror = None
        self._load_mirror_config()
    
    def get_workflow_dir(self, workflow_name: str) -> Path:
        """获取工作流目录"""
        workflow_dir = self.workspace_root / workflow_name
        workflow_dir.mkdir(parents=True, exist_ok=True)
        return workflow_dir
    
    def get_venv_path(self, workflow_name: str) -> Path:
        """获取虚拟环境路径"""
        return self.get_workflow_dir(workflow_name) / ".venv"
    
    def create_workflow_env(self, workflow_name: str, python_version: str = None) -> bool:
        """
        为工作流创建UV虚拟环境（使用共享缓存）
        
        Args:
            workflow_name: 工作流名称
            python_version: Python版本，如 "3.11"
        
        Returns:
            是否创建成功
        """
        workflow_dir = self.get_workflow_dir(workflow_name)
        venv_path = self.get_venv_path(workflow_name)
        
        # 如果已存在，跳过创建
        if venv_path.exists():
            print(f"虚拟环境已存在: {venv_path}")
            return True
        
        # 获取uv可执行文件路径
        uv_path = self.get_preferred_uv_path()
        if not uv_path:
            print("错误: 未找到uv命令，请先安装uv")
            return False
        
        try:
            # 使用 uv venv 创建虚拟环境（自动使用共享缓存）
            cmd = [uv_path, "venv", str(venv_path)]
            if python_version:
                cmd.extend(["--python", python_version])
            
            result = subprocess.run(
                cmd,
                cwd=str(workflow_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"成功创建虚拟环境: {venv_path}")
                return True
            else:
                print(f"创建虚拟环境失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"创建虚拟环境时出错: {e}")
            return False
    
    def install_packages(self, workflow_name: str, packages: List[str]) -> bool:
        """
        在工作流环境中安装包（使用共享缓存）
        
        Args:
            workflow_name: 工作流名称
            packages: 包列表
        
        Returns:
            是否安装成功
        """
        venv_path = self.get_venv_path(workflow_name)
        
        if not venv_path.exists():
            print(f"虚拟环境不存在: {venv_path}")
            return False
        
        if not packages:
            return True
        
        # 获取uv可执行文件路径
        uv_path = self.get_preferred_uv_path()
        if not uv_path:
            print("错误: 未找到uv命令，请先安装uv")
            return False
        
        try:
            # 使用 uv pip install 安装包（自动使用共享缓存）
            python_exe = self._get_python_executable(workflow_name)
            
            for package in packages:
                cmd = [uv_path, "pip", "install", package, "--python", str(python_exe)]
                
                # 如果配置了镜像，添加镜像参数
                current_mirror = self.get_current_mirror()
                if current_mirror:
                    cmd.extend(["--index-url", current_mirror])
                    print(f"使用镜像: {current_mirror}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    print(f"安装包 {package} 失败: {result.stderr}")
                    return False
                else:
                    print(f"成功安装: {package}")
            
            return True
            
        except Exception as e:
            print(f"安装包时出错: {e}")
            return False
    
    def _get_python_executable(self, workflow_name: str) -> Path:
        """获取虚拟环境中的Python可执行文件路径"""
        venv_path = self.get_venv_path(workflow_name)
        
        if os.name == 'nt':  # Windows
            return venv_path / "Scripts" / "python.exe"
        else:  # Unix-like
            return venv_path / "bin" / "python"
    
    def run_python_script(
        self,
        workflow_name: str,
        script_path: str,
        input_data: dict = None,
        timeout: int = 300
    ) -> dict:
        """
        在工作流环境中运行Python脚本
        
        Args:
            workflow_name: 工作流名称
            script_path: 脚本路径
            input_data: 输入数据（将通过stdin传递）
            timeout: 超时时间（秒）
        
        Returns:
            执行结果字典 {success, output, error, data}
        """
        python_exe = self._get_python_executable(workflow_name)
        
        # 如果虚拟环境不存在，使用当前Python
        if not python_exe.exists():
            print(f"虚拟环境不存在，使用当前Python: {sys.executable}")
            python_exe = Path(sys.executable)
        
        try:
            # 准备输入数据
            input_json = json.dumps(input_data) if input_data else ""
            
            # 运行脚本
            result = subprocess.run(
                [str(python_exe), script_path],
                input=input_json,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # 解析输出
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            # 尝试从输出中提取JSON数据
            data = None
            if success and output:
                try:
                    # 查找JSON标记
                    if "###JSON_OUTPUT###" in output:
                        json_start = output.find("###JSON_OUTPUT###") + len("###JSON_OUTPUT###")
                        json_end = output.find("###JSON_OUTPUT_END###")
                        if json_end != -1:
                            json_str = output[json_start:json_end].strip()
                            data = json.loads(json_str)
                except Exception as e:
                    print(f"解析输出JSON失败: {e}")
            
            return {
                "success": success,
                "output": output,
                "error": error,
                "data": data
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"脚本执行超时（{timeout}秒）",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"执行脚本时出错: {e}",
                "data": None
            }
    
    def delete_workflow_env(self, workflow_name: str) -> bool:
        """删除工作流环境"""
        import shutil
        
        venv_path = self.get_venv_path(workflow_name)
        
        if venv_path.exists():
            try:
                shutil.rmtree(venv_path)
                print(f"已删除虚拟环境: {venv_path}")
                return True
            except Exception as e:
                print(f"删除虚拟环境失败: {e}")
                return False
        
        return True
    
    def check_uv_installed(self) -> bool:
        """检查uv是否已安装"""
        uv_paths = self.find_uv_installations()
        return len(uv_paths) > 0
    
    def find_uv_installations(self) -> List[str]:
        """
        查找系统中所有可用的uv安装路径
        
        Returns:
            可用的uv可执行文件路径列表
        """
        uv_paths = []
        
        # 1. 首先检查PATH中的uv命令
        try:
            result = subprocess.run(
                ["where" if os.name == 'nt' else "which", "uv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # where/which 可能返回多个路径
                paths = [path.strip() for path in result.stdout.strip().split('\n') if path.strip()]
                uv_paths.extend(paths)
        except:
            pass
        
        # 2. 检查常见的安装位置
        common_paths = self._get_common_uv_paths()
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                if path not in uv_paths:
                    uv_paths.append(path)
        
        # 3. 验证每个找到的uv是否真的可用
        valid_uv_paths = []
        for uv_path in uv_paths:
            if self._verify_uv_executable(uv_path):
                valid_uv_paths.append(uv_path)
        
        return valid_uv_paths
    
    def _get_common_uv_paths(self) -> List[str]:
        """获取常见的uv安装路径"""
        paths = []
        
        if os.name == 'nt':  # Windows
            # 用户级别安装
            local_app_data = os.environ.get('LOCALAPPDATA', '')
            if local_app_data:
                paths.extend([
                    os.path.join(local_app_data, 'uv', 'uv.exe'),
                    os.path.join(local_app_data, 'uv', 'bin', 'uv.exe'),
                    os.path.join(local_app_data, 'Programs', 'uv', 'uv.exe'),
                ])
            
            # 系统级别安装
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
            
            paths.extend([
                os.path.join(program_files, 'uv', 'uv.exe'),
                os.path.join(program_files, 'uv', 'bin', 'uv.exe'),
                os.path.join(program_files_x86, 'uv', 'uv.exe'),
                os.path.join(program_files_x86, 'uv', 'bin', 'uv.exe'),
            ])
            
            # Python Scripts 目录
            python_scripts = os.path.join(os.path.dirname(sys.executable), 'Scripts')
            paths.append(os.path.join(python_scripts, 'uv.exe'))
            
            # 当前用户的Python Scripts目录
            try:
                import site
                user_scripts = os.path.join(site.USER_BASE, 'Scripts') if site.USER_BASE else ''
                if user_scripts:
                    paths.append(os.path.join(user_scripts, 'uv.exe'))
            except:
                pass
        
        else:  # Unix-like (Linux, macOS)
            # 用户级别安装
            home = os.path.expanduser('~')
            paths.extend([
                os.path.join(home, '.local', 'bin', 'uv'),
                os.path.join(home, '.cargo', 'bin', 'uv'),
                os.path.join(home, 'bin', 'uv'),
            ])
            
            # 系统级别安装
            paths.extend([
                '/usr/local/bin/uv',
                '/usr/bin/uv',
                '/opt/uv/bin/uv',
            ])
            
            # Python 用户base
            try:
                import site
                if site.USER_BASE:
                    paths.append(os.path.join(site.USER_BASE, 'bin', 'uv'))
            except:
                pass
        
        return [p for p in paths if os.path.exists(p)]
    
    def _verify_uv_executable(self, uv_path: str) -> bool:
        """验证uv可执行文件是否可用"""
        try:
            result = subprocess.run(
                [uv_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_preferred_uv_path(self, selected_path: str = None) -> Optional[str]:
        """
        获取首选的uv路径
        
        Args:
            selected_path: 用户选择的uv路径，如果提供则优先使用
        
        Returns:
            首选的uv可执行文件路径，如果没有找到则返回None
        """
        # 如果用户指定了路径，验证并使用
        if selected_path and os.path.isfile(selected_path) and self._verify_uv_executable(selected_path):
            return selected_path
        
        # 如果有自定义路径，优先使用
        if self.custom_uv_path and os.path.isfile(self.custom_uv_path) and self._verify_uv_executable(self.custom_uv_path):
            return self.custom_uv_path
        
        uv_paths = self.find_uv_installations()
        if not uv_paths:
            return None
        
        # 优先选择PATH中的uv（通常是第一个）
        try:
            result = subprocess.run(
                ["where" if os.name == 'nt' else "which", "uv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                primary_path = result.stdout.strip().split('\n')[0].strip()
                if primary_path in uv_paths:
                    return primary_path
        except:
            pass
        
        # 如果PATH中的不可用，返回第一个找到的
        return uv_paths[0]
    
    def set_custom_uv_path(self, uv_path: str) -> bool:
        """
        设置自定义的uv路径
        
        Args:
            uv_path: uv可执行文件路径
        
        Returns:
            是否设置成功
        """
        if os.path.isfile(uv_path) and self._verify_uv_executable(uv_path):
            self.custom_uv_path = uv_path
            return True
        return False
    
    def set_custom_mirror(self, mirror_url: str) -> bool:
        """
        设置自定义镜像地址
        
        Args:
            mirror_url: 镜像地址
        
        Returns:
            是否设置成功
        """
        self.custom_mirror = mirror_url
        self._save_mirror_config()
        return True
    
    def _load_mirror_config(self):
        """加载镜像配置"""
        # 检查配置文件
        config_file = os.path.join(os.path.expanduser("~"), ".uv", "uv.toml")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                match = re.search(r'index-url\s*=\s*"([^"]+)"', content)
                if match:
                    self.custom_mirror = match.group(1)
                    return
            except:
                pass
        
        # 检查环境变量
        env_mirror = os.environ.get("UV_INDEX_URL", "")
        if env_mirror:
            self.custom_mirror = env_mirror
    
    def _save_mirror_config(self):
        """保存镜像配置"""
        if self.custom_mirror:
            # 设置环境变量
            os.environ["UV_INDEX_URL"] = self.custom_mirror
            
            # 保存到配置文件
            try:
                config_dir = os.path.join(os.path.expanduser("~"), ".uv")
                os.makedirs(config_dir, exist_ok=True)
                
                config_file = os.path.join(config_dir, "uv.toml")
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    content = ""
                
                import re
                if "[pip]" in content:
                    content = re.sub(r'index-url\s*=\s*".*?"', f'index-url = "{self.custom_mirror}"', content)
                else:
                    if content and not content.endswith('\n'):
                        content += '\n'
                    content += '[pip]\n'
                    content += f'index-url = "{self.custom_mirror}"\n'
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"保存镜像配置时出错: {e}")
    
    def get_current_mirror(self) -> str:
        """获取当前使用的镜像地址"""
        if self.custom_mirror:
            return self.custom_mirror
        return os.environ.get("UV_INDEX_URL", "")
