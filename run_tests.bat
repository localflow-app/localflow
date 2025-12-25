@echo off
echo === LocalFlow 测试运行器 ===
echo.
echo 选择要运行的测试类型:
echo 1. 单元测试 (Unit Tests)
echo 2. 集成测试 (Integration Tests)
echo 3. UI 测试 (UI Tests)
echo 4. 所有测试 (All Tests)
echo 5. 退出
echo.
set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" (
    python test/run_tests.py unit
) else if "%choice%"=="2" (
    python test/run_tests.py integration
) else if "%choice%"=="3" (
    python test/run_tests.py ui
) else if "%choice%"=="4" (
    python test/run_tests.py
) else if "%choice%"=="5" (
    exit /b 0
) else (
    echo 无效选项，请重新运行
)

echo.
pause