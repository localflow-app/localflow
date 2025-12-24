#!/bin/bash

echo "========================================"
echo "LocalFlow 一键打包脚本 (Linux/Mac)"
echo "========================================"
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    echo "请先安装 Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 询问打包类型
echo
echo "请选择打包类型:"
echo "1. 完整打包 (推荐) - 包含所有优化和配置"
echo "2. 快速打包 - 适合快速测试"
echo
read -p "请输入选择 (1/2): " choice

case $choice in
    1)
        echo
        echo "🚀 开始完整打包..."
        python3 build.py
        ;;
    2)
        echo
        echo "⚡ 开始快速打包..."
        python3 quick_build.py
        ;;
    *)
        echo
        echo "❌ 无效选择，使用默认快速打包..."
        python3 quick_build.py
        ;;
esac

echo
echo "打包完成！输出文件在 dist/ 目录中"
echo

# 设置可执行权限
if [ -f "dist/LocalFlow" ]; then
    chmod +x dist/LocalFlow
    echo "✅ 已设置可执行权限"
fi