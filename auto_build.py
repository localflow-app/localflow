#!/usr/bin/env python3
"""
非交互式打包脚本 - 自动运行打包过程
"""

import sys
import os
from build import create_spec_file, clean_build, build_executable, verify_build, create_portable_package

def auto_build():
    """自动构建（不询问）"""
    print("=" * 50)
    print("LocalFlow 自动打包脚本")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('main.py'):
        print("[ERROR] 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    try:
        # 1. 清理之前的构建
        clean_build()
        
        # 2. 创建 spec 文件
        create_spec_file()
        
        # 3. 构建可执行文件
        if not build_executable():
            sys.exit(1)
        
        # 4. 验证构建
        if not verify_build():
            sys.exit(1)
        
        # 5. 创建便携版本
        create_portable_package()
        
        print("\n" + "=" * 50)
        print("[SUCCESS] 自动打包完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[ERROR] 打包过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    auto_build()