#!/usr/bin/env python3
"""
快速打包脚本 - 使用默认配置快速打包 LocalFlow
"""

import subprocess
import sys
import os

def quick_build():
    """快速构建"""
    print("🚀 快速打包 LocalFlow...")
    
    # 检查依赖
    try:
        import PyInstaller
    except ImportError:
        print("安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 快速构建命令 - PySide6 推荐目录版本
    cmd = [
        'pyinstaller',
        '--name=LocalFlow',
        '--windowed',  # 不显示控制台
        '--add-data=assets;assets',  # 包含资源文件
        '--add-data=examples;examples',  # 包含示例文件
        '--icon=assets/localflow_64.png',  # 图标
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--clean',
        '--noconfirm',
        '--onedir',  # 强制目录版本（符合LGPL）
        'main.py'
    ]
    
    print("开始构建...")
    try:
        subprocess.check_call(cmd)
        print("✅ 构建完成!")
        print("📁 输出文件: dist/LocalFlow/")
        print("   - LocalFlow.exe (主程序)")
        print("   - _internal/ (依赖文件)")
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    quick_build()