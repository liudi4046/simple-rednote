@echo off
setlocal enabledelayedexpansion

echo 检查 Python 版本...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 检测到 Python 版本: %PYTHON_VERSION%

:: 提取主版本号和次版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

:: 检查 Python 版本是否大于 3.11
if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% GTR 11 (
        echo 警告: 检测到 Python 版本高于 3.11，可能会导致兼容性问题
        echo 建议使用 Python 3.11 或更低版本

        :: 检查是否安装了 Python 3.11
        where python3.11 >nul 2>&1
        if not errorlevel 1 (
            echo 找到 Python 3.11，将使用它来创建虚拟环境
            set PYTHON_CMD=python3.11
        ) else (
            echo 未找到 Python 3.11，将尝试使用当前版本，但可能会遇到问题
            set PYTHON_CMD=python
        )
    ) else (
        echo Python 版本兼容，继续执行
        set PYTHON_CMD=python
    )
) else (
    echo Python 版本兼容，继续执行
    set PYTHON_CMD=python
)

echo 检查虚拟环境是否已存在...

if not exist venv_xhs (
    echo 创建新的虚拟环境...
    %PYTHON_CMD% -m venv venv_xhs
    
    echo 安装依赖...
    call venv_xhs\Scripts\activate.bat
    pip install -r requirements.txt
    
    echo 安装pyppeteer...
    pip install pyppeteer
) else (
    echo 使用已存在的虚拟环境...
    call venv_xhs\Scripts\activate.bat
)

echo 启动应用...
python app.py

pause