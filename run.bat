@echo off
echo 检查虚拟环境是否已存在...

if not exist venv_xhs (
    echo 创建新的虚拟环境...
    python -m venv venv_xhs
    
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