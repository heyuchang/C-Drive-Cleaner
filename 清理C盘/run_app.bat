@echo off
title 启动清理工具...

:: Try using the Python Launcher for Windows (py)
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo Found 'py' launcher. Starting...
    py main.py
    if %errorlevel% equ 0 goto :EOF
)

:: If py failed or not found, try 'python'
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo Found 'python' command. Starting...
    python main.py
    if %errorlevel% equ 0 goto :EOF
)

:: If both fail
echo.
echo [Error] 无法找到 Python 环境。
echo 请确保您已安装 Python，并且勾选了 "Add Python to PATH" (或者安装了 py 启动器)。
echo.
echo 您可以访问 https://www.python.org/downloads/ 下载安装。
echo.
pause
