#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书简易管理工具 - Web界面
提供发布帖子、查看数据和关注者的Web界面
"""

import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
import random
import requests

from xhs_api import XhsSimpleApi
# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制上传文件大小为100MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局API客户端
api_client = None

# 配置文件路径
CONFIG_FILE = 'config.json'


# 添加全局模板变量
@app.context_processor
def inject_now():
    return {'now': datetime.now()}


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"cookie": ""}


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def init_api_client():
    """初始化API客户端"""
    global api_client
    config = load_config()
    cookie = config.get("cookie", "")
    if cookie:
        try:
            api_client = XhsSimpleApi(cookie)
            return True
        except Exception as e:
            print(f"初始化API客户端失败: {e}")
    return False


@app.route('/')
def index():
    """首页"""
    # 检查是否已登录
    if not api_client:
        if not init_api_client():
            return redirect(url_for('login'))
    
    # 获取当前用户信息
    try:
        self_info = api_client.client.get_self_info2()
        user_id = self_info.get('user_id', '')
        
        if not user_id:
            flash('获取用户信息失败，请重新登录或检查网络连接', 'danger')
            return redirect(url_for('login'))
            
        print(f"当前用户ID: {user_id}")
        
        # 获取用户笔记列表
        notes_data = api_client.get_user_notes(user_id)
        
        # 处理笔记数据以适应UI显示
        formatted_notes = []
        for note in notes_data:
            # 打印每个笔记的原始数据，用于调试
            
            interact_info = note.get('interact_info', {})
            if isinstance(interact_info, str):
                try:
                    interact_info = json.loads(interact_info)
                except:
                    interact_info = {}
            
            # 获取封面图片URL
            cover_url = ''
            if isinstance(note.get('cover'), dict) and 'info_list' in note.get('cover', {}):
                info_list = note.get('cover', {}).get('info_list', [])
                if info_list and len(info_list) > 0:
                    cover_url = info_list[0].get('url', '')
            
            # 处理点赞数
            likes = interact_info.get('liked_count', '0')
            try:
                likes = int(likes)
            except:
                likes = 0
            
            formatted_note = {
                'note_id': note.get('note_id', ''),
                'title': note.get('display_title', '无标题').strip(),
                'desc': note.get('desc', ''),
                'cover': cover_url,
                'likes': likes,
                'time': note.get('time', '')
            }
            formatted_notes.append(formatted_note)
        
        # 显示用户信息
        nickname = self_info.get('nickname', '')
        if nickname:
            flash(f'欢迎回来，{nickname}！', 'success')
        
        return render_template('index.html', notes=formatted_notes)
    except Exception as e:
        flash(f'获取用户信息或笔记列表失败: {e}', 'danger')
        return render_template('index.html', notes=[])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        cookie = request.form.get('cookie', '')
        if cookie:
            # 保存Cookie
            config = load_config()
            config["cookie"] = cookie
            save_config(config)
            
            # 初始化API客户端
            if init_api_client():
                try:
                    # 获取并保存用户信息
                    self_info = api_client.client.get_self_info2()
                    user_id = self_info.get('user_id', '')
                    if user_id:
                        config["user_id"] = user_id
                        save_config(config)
                        flash('登录成功', 'success')
                    else:
                        flash('登录成功，但获取用户信息失败', 'warning')
                except Exception as e:
                    flash(f'登录成功，但获取用户信息失败: {e}', 'warning')
                
                return redirect(url_for('index'))
            else:
                flash('登录失败，请检查Cookie是否有效', 'danger')
        else:
            flash('请输入Cookie', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """退出登录"""
    global api_client
    api_client = None
    flash('已退出登录', 'success')
    return redirect(url_for('login'))


@app.route('/publish', methods=['GET', 'POST'])
def publish():
    """发布笔记页面"""
    # 检查是否已登录
    if not api_client:
        if not init_api_client():
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title', '')
        desc = request.form.get('desc', '')
        is_private = request.form.get('is_private', 'false') == 'true'
        
        if not title or not desc:
            flash('标题和内容不能为空', 'danger')
            return redirect(url_for('publish'))
        
        try:
            # 处理图片上传
            images = []
            for file in request.files.getlist('images'):
                if file and file.filename:
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filename)
                    images.append(filename)
            
            if not images:
                flash('请上传至少一张图片', 'danger')
                return redirect(url_for('publish'))
            
            # 发布图文笔记
            result = api_client.publish_image_note(
                title=title,
                desc=desc,
                image_paths=images,
                is_private=is_private
            )
            
            flash(f'图文笔记发布成功: {result.get("note_id", "")}', 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            flash(f'发布失败: {e}', 'danger')
            return redirect(url_for('publish'))
    
    return render_template('publish.html')


@app.route('/note/<note_id>')
def note_detail(note_id):
    """笔记详情页面"""
    # 检查是否已登录
    if not api_client:
        if not init_api_client():
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
    
    # 使用新API获取笔记详情
    note_data = api_client.get_note_by_id(note_id)
    
    # 使用小红书评论API获取评论
    comments = []
    try:
        # 获取xsec_token
        xsec_token = ""
        if note_data and "xsec_token" in note_data:
            xsec_token = note_data["xsec_token"]
        else:
            # 如果笔记详情中没有xsec_token，尝试从api_client的缓存中获取
            xsec_token = api_client.xsec_tokens.get(note_id, "")
        
        # 构建评论API请求URL
        comment_url = f"https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
        params = {
            "note_id": note_id,
            "cursor": "",
            "top_comment_id": "",
            "image_formats": "jpg,webp,avif"
        }
        
        # 如果有xsec_token，添加到参数中
        if xsec_token:
            params["xsec_token"] = xsec_token
        
        # 使用与api_client相同的cookie发送请求
        headers = {
            "Cookie": api_client.cookie,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": f"https://www.xiaohongshu.com/explore/{note_id}"
        }
        
        # 发送请求获取评论数据
        response = requests.get(comment_url, params=params, headers=headers)
        
        if response.status_code == 200:
            comment_data = response.json()
            if "data" in comment_data and "comments" in comment_data["data"]:
                raw_comments = comment_data["data"]["comments"]
                
                # 处理评论数据
                for comment in raw_comments:
                    comments.append({
                        'comment_id': comment.get("id", ""),
                        'content': comment.get("content", ""),
                        'user_id': comment.get("user_info", {}).get("user_id", ""),
                        'nickname': comment.get("user_info", {}).get("nickname", ""),
                        'avatar': comment.get("user_info", {}).get("image", ""),
                        'likes': int(comment.get("like_count", 0)),
                        'time': comment.get("create_time", ""),
                        'sub_comments': int(comment.get("sub_comment_count", 0))
                    })
        else:
            print(f"获取评论失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"获取评论异常: {e}")
    
    if not note_data:
        stats = {'error': '获取笔记详情失败'}
    else:
        # 处理笔记统计数据
        stats = {
            'title': note_data.get('title', '无标题'),
            'desc': note_data.get('desc', ''),
            'likes': note_data.get('interact_info', {}).get('liked_count', 0),
            'comments': note_data.get('interact_info', {}).get('comment_count', 0),
            'collects': note_data.get('interact_info', {}).get('collected_count', 0),
            'time': note_data.get('time', ''),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 获取图片列表
        images = []
        if 'image_list' in note_data:
            for image in note_data.get('image_list', []):
                # 直接使用info_list中的URL
                if 'info_list' in image and len(image.get('info_list', [])) > 0:
                    for info in image.get('info_list', []):
                        # 优先使用WB_DFT场景的图片
                        if info.get('image_scene') == 'WB_DFT' and info.get('url'):
                            images.append(info.get('url'))
                            break
                # 如果没有找到WB_DFT场景的图片，使用第一个可用的URL
                if not images and 'info_list' in image and len(image.get('info_list', [])) > 0:
                    images.append(image.get('info_list', [])[0].get('url', ''))
        
        # 如果还是没有找到图片，尝试从note_card中获取
        if not images and 'note_card' in note_data and 'image_list' in note_data.get('note_card', {}):
            for image in note_data.get('note_card', {}).get('image_list', []):
                if 'info_list' in image and len(image.get('info_list', [])) > 0:
                    for info in image.get('info_list', []):
                        if info.get('image_scene') == 'WB_DFT' and info.get('url'):
                            images.append(info.get('url'))
                            break
        

    
    return render_template('note_detail.html', stats=stats, comments=comments, note_id=note_id, images=images)


@app.route('/followers')
def followers():
    """关注者列表页面"""
    # 检查是否已登录
    if not api_client:
        if not init_api_client():
            flash('请先登录', 'danger')
            return redirect(url_for('login'))
    
    # 获取关注者列表
    followers_data = api_client.get_followers()

    
    return render_template('followers.html', followers_data=followers_data)


@app.route('/proxy_image')
def proxy_image():
    """代理获取小红书图片"""
    image_url = request.args.get('url', '')
    if not image_url:
        return "No URL provided", 400
    
    try:
        # 设置请求头，模拟浏览器请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        # 获取图片
        response = requests.get(image_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 获取图片内容类型
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # 返回图片，设置缓存控制
            resp = Response(response.content, content_type=content_type)
            resp.headers['Cache-Control'] = 'public, max-age=86400'  # 缓存一天
            return resp
        else:
            print(f"获取图片失败，状态码: {response.status_code}")
            return Response("Failed to fetch image", status=400)
    except Exception as e:
        print(f"获取图片异常: {e}")
        return Response(f"Error: {str(e)}", status=500)


if __name__ == '__main__':
    # 初始化API客户端
    init_api_client()
    
    # 启动Flask应用，修改端口为5001
    app.run(debug=True, host='0.0.0.0', port=5002) 