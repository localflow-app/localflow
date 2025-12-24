import subprocess
import sys
import os

# 检查是否在虚拟环境中
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("在虚拟环境中，安装Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
else:
    print("不在虚拟环境中，跳过Pillow安装")