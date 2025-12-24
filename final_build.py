#!/usr/bin/env python3
"""
LocalFlow 最终打包脚本 - 解决所有问题
支持图标，符合LGPL，无Unicode问题
"""

import subprocess
import sys
import os
from pathlib import Path

def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"[CLEAN] 已删除 {dir_name}")

def main():
    print("=" * 50)
    print("LocalFlow 最终打包脚本")
    print("=" * 50)
    
    # 检查环境
    if not Path('main.py').exists():
        print("[ERROR] 请在项目根目录运行")
        sys.exit(1)
    
    # 清理
    clean_build()
    
    # 检查图标
    assets_dir = Path('assets')
    ico_file = assets_dir / 'localflow.ico'
    
    # 构建命令 - 基础版本
    cmd = [
        'pyinstaller',
        '--name=LocalFlow',
        '--windowed',
        '--clean', 
        '--noconfirm',
        '--onedir',  # 符合LGPL
        '--add-data=assets;assets',
        '--add-data=examples;examples',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=src.core.uv_manager',
        '--hidden-import=uv',
        '--hidden-import=resource',  # 用于资源路径处理
        '--hidden-import=importlib.resources',  # 现代资源处理
        'main.py'
    ]
    
    # 添加图标（如果存在）
    if ico_file.exists():
        cmd.extend(['--icon', str(ico_file)])
        print(f"[ICON] 使用图标: {ico_file}")
    else:
        print("[WARNING] 未找到图标文件")
    
    print("\n[BUILD] 开始构建...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] PyInstaller 执行完成")
        
        # 验证
        exe_path = Path('dist/LocalFlow/LocalFlow.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n[SUCCESS] 构建完成!")
            print(f"[OUTPUT] {exe_path}")
            print(f"[SIZE]   {size_mb:.1f} MB")
            print(f"[LIC]    符合PySide6 LGPL要求")
            
            # 创建便携版本
            create_portable()
            
        else:
            print("[ERROR] 可执行文件未生成")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

def create_portable():
    """创建便携版本"""
    print("\n[PORTABLE] 创建便携版本...")
    
    portable_dir = Path('dist/LocalFlow_Portable')
    if portable_dir.exists():
        import shutil
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # 复制主程序
    source_dir = Path('dist/LocalFlow')
    import shutil
    if source_dir.exists():
        shutil.copytree(source_dir, portable_dir / 'LocalFlow', dirs_exist_ok=True)
    
    # 创建启动脚本
    if os.name == 'nt':  # Windows
        start_script = portable_dir / '启动LocalFlow.bat'
        start_script.write_text('''@echo off
cd /d "%~dp0LocalFlow"
LocalFlow.exe
pause
''')
        print("[OK] Windows便携版本已创建")
    else:
        start_script = portable_dir / 'start_localflow.sh'
        start_script.write_text('''#!/bin/bash
cd "$(dirname "$0")/LocalFlow"
./LocalFlow
''')
        os.chmod(start_script, 0o755)
        print("[OK] Linux/Mac便携版本已创建")

if __name__ == '__main__':
    main()