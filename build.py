#!/usr/bin/env python3
"""
PyInstaller 打包脚本
用于将 LocalFlow 打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_requirements():
    """检查必要的依赖"""
    print("检查打包依赖...")
    
    try:
        import PyInstaller
        print("[OK] PyInstaller 已安装")
    except ImportError:
        print("[ERROR] PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller 安装完成")
    
    try:
        import PIL
        print("[OK] Pillow 已安装")
    except ImportError:
        print("[ERROR] Pillow 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("[OK] Pillow 安装完成")

def create_spec_file():
    """创建 PyInstaller spec 文件"""
    print("创建 PyInstaller spec 文件...")
    
    # 验证必要的文件和目录
    ROOT_DIR = Path(".")
    ASSETS_DIR = ROOT_DIR / "assets"
    ICONS_DIR = ASSETS_DIR / "icons"
    EXAMPLES_DIR = ROOT_DIR / "examples"
    
    # 检查文件是否存在
    missing_files = []
    
    # 优先使用 ICO 格式的图标
    ico_file = ASSETS_DIR / "localflow.ico"
    png_file = ASSETS_DIR / "localflow_64.png"
    
    icon_file = None
    if ico_file.exists():
        icon_file = ico_file
        print(f"[OK] 使用 ICO 格式图标: {ico_file}")
    elif png_file.exists():
        icon_file = png_file
        print(f"[OK] 使用 PNG 格式图标: {png_file}")
    else:
        missing_files.append(str(ico_file))
        missing_files.append(str(png_file))
        print("[WARNING] 没有找到图标文件")
    
    if not ICONS_DIR.exists():
        missing_files.append(str(ICONS_DIR))
    
    if missing_files:
        print("[WARNING] 警告: 以下文件或目录不存在:")
        for file in missing_files:
            print(f"   - {file}")
        print("将跳过这些文件...")
    
    # 构建文件列表
    added_files = []
    
    # 资源文件
    if png_file.exists():
        added_files.append((str(png_file), "assets"))
    
    if ICONS_DIR.exists():
        added_files.append((str(ICONS_DIR), "assets/icons"))
    
    # 示例文件
    if EXAMPLES_DIR.exists():
        added_files.append((str(EXAMPLES_DIR), "examples"))
    
    # 手动构建spec内容，避免f-string问题
    spec_lines = [
        '# -*- mode: python ; coding: utf-8 -*-',
        '',
        'import sys',
        'from pathlib import Path',
        '',
        '# 项目根目录',
        'ROOT_DIR = Path(".")',
        'ASSETS_DIR = ROOT_DIR / "assets"',
        '',
        '# 收集所有需要的文件',
        'added_files = ' + repr(added_files),
        '',
        '# 隐藏导入',
        'hiddenimports = [',
        '    # PySide6 模块',
        '    "PySide6.QtCore",',
        '    "PySide6.QtWidgets",', 
        '    "PySide6.QtGui",',
        '    "PySide6.QtNetwork",',
        '    ',
        '    # 项目模块',
        '    "src.main_window",',
        '    "src.views.workflow_canvas",',
        '    "src.views.workflow_tab_widget",',
        '    "src.views.overview_widget",',
        '    "src.views.node_graphics",',
        '    "src.views.node_browser",',
        '    "src.views.node_properties",',
        '    "src.dialogs.settings_dialog",',
        '    "src.core.workflow_executor",',
        '    "src.core.uv_manager",',
        '    "src.core.node_base",',
        '    ',
        '    # JSON 和其他依赖',
        '    "json",',
        '    "pathlib",',
        '    "shutil",',
        '    "time",',
        '    "math",',
        '    ',
        '    # UV 相关',
        '    "uv",',
        ']',
        '',
        'a = Analysis(',
        '    ["main.py"],',
        '    pathex=[str(ROOT_DIR)],',
        '    binaries=[],',
        '    datas=added_files,',
        '    hiddenimports=hiddenimports,',
        '    hookspath=[],',
        '    hooksconfig={},',
        '    runtime_hooks=[],',
        '    excludes=[',
        '        # 排除不需要的模块以减小体积',
        '        "tkinter",',
        '        "matplotlib",',
        '        "numpy",',
        '        "scipy",',
        '        "pandas",',
        '        "IPython",',
        '    ],',
        '    noarchive=False,',
        ')',
        '',
        'pyz = PYZ(a.pure)',
        '',
        '# 图标路径',
        'icon_path = None',
        'if Path("' + str(icon_file) + '").exists():',
        '    icon_path = "' + str(icon_file) + '"',
        '    print(f"[INFO] 设置图标: {icon_path}")',
        'else:',
        '    print("[WARNING] 跳过图标设置")',
        '',
        '# 注意：PySide6 使用 LGPL 许可证，为了合规性，',
        '# 不建议打包为单文件，而是使用目录版本',
        'exe = EXE(',
        '    pyz,',
        '    a.scripts,',
        '    [],  # 不包含 binaries 和 datas，由 COLLECT 处理',
        '    name="LocalFlow",',
        '    debug=False,',
        '    bootloader_ignore_signals=False,',
        '    strip=False,',
        '    upx=True,',
        '    upx_exclude=[],',
        '    runtime_tmpdir=None,',
        '    console=False,  # 不显示控制台窗口',
        '    disable_windowed_traceback=False,',
        '    argv_emulation=False,',
        '    target_arch=None,',
        '    codesign_identity=None,',
        '    entitlements_file=None,',
        '    icon=icon_path,',
        ')',
        '',
        '# 创建目录版本（PySide6 推荐方式）',
        'coll = COLLECT(',
        '    exe,',
        '    a.binaries,',
        '    a.datas,',
        '    strip=False,',
        '    upx=True,',
        '    upx_exclude=[],',
        '    name="LocalFlow"',
        ')',
    ]
    
    spec_content = '\n'.join(spec_lines)
    
    with open('LocalFlow.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("[OK] LocalFlow.spec 文件已创建")

def clean_build():
    """清理之前的构建文件"""
    print("清理之前的构建文件...")
    
    dirs_to_clean = ['build', 'dist', 'LocalFlow_dir']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  - 已删除 {dir_name}")
    
    files_to_clean = ['LocalFlow.spec']
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  - 已删除 {file_name}")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 构建
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'LocalFlow.spec'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("[OK] 构建完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 构建失败: {e}")
        return False

def verify_build():
    """验证构建结果"""
    print("验证构建结果...")
    
    # 检查目录版本（PySide6 推荐方式）
    dir_path = Path('dist/LocalFlow')
    if dir_path.exists():
        print(f"[OK] 目录版本已生成: {dir_path}")
        
        # 检查主可执行文件
        main_exe = dir_path / 'LocalFlow.exe'
        if main_exe.exists():
            size_mb = main_exe.stat().st_size / (1024 * 1024)
            print(f"   主可执行文件: {main_exe}")
            print(f"   文件大小: {size_mb:.1f} MB")
            print("   ✅ 符合 PySide6 LGPL 许可要求")
        
        return True
    else:
        print("[ERROR] 目录版本未找到")
        return False

def create_portable_package():
    """创建便携版本"""
    print("创建便携版本...")
    
    portable_dir = Path('dist/LocalFlow_Portable')
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # 复制目录版本
    dir_path = Path('dist/LocalFlow')
    if dir_path.exists():
        shutil.copytree(dir_path, portable_dir / 'LocalFlow', dirs_exist_ok=True)
    
    # 创建启动脚本
    if os.name == 'nt':  # Windows
        start_script = portable_dir / '启动LocalFlow.bat'
        start_script.write_text('''@echo off
cd /d "%~dp0LocalFlow"
LocalFlow.exe
pause
''')
        print("[OK] 便携版本已创建 (启动脚本: 启动LocalFlow.bat)")
    else:  # Linux/Mac
        start_script = portable_dir / 'start_localflow.sh'
        start_script.write_text('''#!/bin/bash
cd "$(dirname "$0")/LocalFlow"
./LocalFlow
''')
        os.chmod(start_script, 0o755)
        print("[OK] 便携版本已创建 (启动脚本: start_localflow.sh)")

def main():
    """主函数"""
    print("=" * 50)
    print("LocalFlow PyInstaller 打包脚本")
    print("=" * 50)
    
    # 检查当前目录
    if not Path('main.py').exists():
        print("[ERROR] 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    try:
        # 1. 检查依赖
        check_requirements()
        
        # 2. 询问是否清理
        clean = input("\n是否清理之前的构建文件? (y/N): ").lower().startswith('y')
        if clean:
            clean_build()
        
        # 3. 创建 spec 文件
        create_spec_file()
        
        # 4. 构建可执行文件
        if not build_executable():
            sys.exit(1)
        
        # 5. 验证构建
        if not verify_build():
            sys.exit(1)
        
        # 6. 创建便携版本
        create_portable_package()
        
        print("\n" + "=" * 50)
        print("[SUCCESS] 打包完成！")
        print("=" * 50)
        print("\n输出文件:")
        print("  - dist/LocalFlow/                (目录版本 - 推荐方式)")
        print("     - LocalFlow.exe             (主程序)")
        print("     - _internal/               (依赖文件)")
        print("  - dist/LocalFlow_Portable/       (便携版本)")
        print("\n✅ 符合 PySide6 LGPL 许可要求:")
        print("  - 使用目录版本而非单文件")
        print("  - 保留Qt动态链接库分离")
        print("  - 允许用户替换Qt库")
        print("\n推荐使用:")
        print("  - 目录版本用于分发和调试")
        print("  - 便携版本用于专业部署")
        
    except KeyboardInterrupt:
        print("\n\n[INFO] 打包已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()