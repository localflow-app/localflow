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
        
        try:
            # 使用 uv venv 创建虚拟环境（自动使用共享缓存）
            cmd = ["uv", "venv", str(venv_path)]
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
                
        except FileNotFoundError:
            print("错误: 未找到uv命令，请先安装uv")
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
        
        try:
            # 使用 uv pip install 安装包（自动使用共享缓存）
            python_exe = self._get_python_executable(workflow_name)
            
            for package in packages:
                cmd = ["uv", "pip", "install", package, "--python", str(python_exe)]
                
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
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
