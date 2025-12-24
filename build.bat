@echo off
echo ========================================
echo LocalFlow 一键打包脚本 (Windows)
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: Python 未安装或未添加到 PATH
    echo 请先安装 Python 并确保其在 PATH 中
    pause
    exit /b 1
)

echo ✅ Python 已安装

REM 询问打包类型
echo.
echo 请选择打包类型:
echo 1. 完整打包 (推荐) - 包含所有优化和配置
echo 2. 快速打包 - 适合快速测试
echo.
set /p choice="请输入选择 (1/2): "

if "%choice%"=="1" (
    echo.
    echo 🚀 开始完整打包...
    python build.py
) else if "%choice%"=="2" (
    echo.
    echo ⚡ 开始快速打包...
    python quick_build.py
) else (
    echo ❌ 无效选择，使用默认快速打包...
    python quick_build.py
)

echo.
echo 打包完成！输出文件在 dist/ 目录中
echo.
pause