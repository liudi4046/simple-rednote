#!/bin/bash

# 检查虚拟环境是否已存在
if [ ! -d "venv_xhs" ]; then
    echo "创建新的虚拟环境..."
    python3 -m venv venv_xhs
    
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