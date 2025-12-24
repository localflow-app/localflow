#!/usr/bin/env python3
"""
修复图标问题的打包脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 50)
    print("LocalFlow 图标修复打包")
    print("=" * 50)
    
    # 检查环境
    if not Path('main.py').exists():
        print("[ERROR] 请在项目根目录运行")
        sys.exit(1)
    
    # 确定图标文件
    assets_dir = Path('assets')
    ico_file = assets_dir / 'localflow.ico'
    png_file = assets_dir / 'localflow_64.png'
    
    icon_option = []
    if ico_file.exists():
        icon_option = ['--icon', str(ico_file)]
        print(f"[OK] 使用ICO图标: {ico_file}")
    elif png_file.exists():
        # 先尝试安装Pillow
        print("[INFO] PNG图标需要Pillow，正在检查...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            icon_option = ['--icon', str(png_file)]
            print(f"[OK] 使用PNG图标: {png_file}")
        except:
            print("[WARNING] Pillow安装失败，跳过图标")
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--name=LocalFlow',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--onedir',  # 目录版本
        f'--add-data=assets;assets',
        f'--add-data=examples;examples',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
    ]
    
    # 添加图标选项
    if icon_option:
        cmd.extend(icon_option)
    
    cmd.append('main.py')
    
    print("\n[INFO] 开始构建...")
    print(f"[CMD] {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        
        # 验证结果
        exe_path = Path('dist/LocalFlow/LocalFlow.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n[SUCCESS] 构建完成!")
            print(f"[OUTPUT] {exe_path}")
            print(f"[SIZE] {size_mb:.1f} MB")
            
            if icon_option:
                print("[ICON] 图标已设置")
            else:
                print("[WARNING] 未设置图标")
        else:
            print("[ERROR] 构建失败")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()