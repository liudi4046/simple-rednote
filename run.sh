#!/bin/bash

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "检测到 Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否大于 3.11
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -gt 11 ]; then
    echo "警告: 检测到 Python 版本高于 3.11，可能会导致兼容性问题"
    echo "建议使用 Python 3.11 或更低版本"
    
    # 检查是否安装了 Python 3.11
    if command -v python3.11 &> /dev/null; then
        echo "找到 Python 3.11，将使用它来创建虚拟环境"
        PYTHON_CMD="python3.11"
    else
        echo "未找到 Python 3.11，将尝试使用当前版本，但可能会遇到问题"
        PYTHON_CMD="python3"
    fi
else
    echo "Python 版本兼容，继续执行"
    PYTHON_CMD="python3"
fi

# 检查虚拟环境是否已存在
if [ ! -d "venv_xhs" ]; then
    echo "创建新的虚拟环境..."
    $PYTHON_CMD -m venv venv_xhs
    
    echo "安装依赖..."
    source venv_xhs/bin/activate
    pip install -r requirements.txt
    
    # 安装pyppeteer
    echo "安装pyppeteer..."
    pip install pyppeteer
    # pyppeteer会自动下载并安装chromium
else
    echo "使用已存在的虚拟环境..."
    source venv_xhs/bin/activate
fi

# 运行应用
echo "启动应用..."
python app.py