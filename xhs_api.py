#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书API核心功能模块
提供发布帖子、查看数据和关注者的功能
"""

import os
import time
import json
import random
import string
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from xhs import XhsClient
from xhs.exception import DataFetchError

# 配置信息
CONFIG_FILE = 'config.json'  # 配置文件路径，用于获取Cookie
OUTPUT_DIR = 'notes_output'  # 输出目录

def generate_xsec_token(length=64):
    """生成随机xsec_token（备用方法）"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

class XhsSimpleApi:
    """小红书简易API封装类"""

    def __init__(self, cookie: str):
        """
        初始化API客户端
        
        参数:
            cookie: 小红书的Cookie
        """
        self.cookie = cookie
        self.client = XhsClient(cookie=cookie, sign=self._sign)
        # 存储已获取的xsec_token
        self.xsec_tokens = {}
        
        # 确保输出目录存在
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            print(f"创建输出目录: {OUTPUT_DIR}")
    
    def _sign(self, uri, data=None, a1="", web_session=""):
        """
        签名函数，用于小红书API请求的签名
        这里使用一个简单的实现，实际使用时可能需要更复杂的签名逻辑
        """
        try:
            from playwright.sync_api import sync_playwright
            
            for _ in range(5):
                try:
                    with sync_playwright() as playwright:
                        chromium = playwright.chromium
                        browser = chromium.launch(headless=True)
                        browser_context = browser.new_context()
                        
                        context_page = browser_context.new_page()
                        context_page.goto("https://www.xiaohongshu.com")
                        
                        if a1:
                            browser_context.add_cookies([
                                {'name': 'a1', 'value': a1, 'domain': ".xiaohongshu.com", 'path': "/"}
                            ])
                            context_page.reload()
                            time.sleep(1)
                        
                        encrypt_params = context_page.evaluate("([url, data]) => window._webmsxyw(url, data)", [uri, data])
                        return {
                            "x-s": encrypt_params["X-s"],
                            "x-t": str(encrypt_params["X-t"])
                        }
                except Exception as e:
                    print(f"签名失败，重试中: {e}")
                    time.sleep(1)
            
            raise Exception("重试多次后签名仍然失败")
        except ImportError:
            print("请安装playwright: pip install playwright")
            print("并安装浏览器: playwright install chromium")
            raise
    
    def publish_image_note(
        self,
        title: str,
        desc: str,
        image_paths: List[str],
        topics: Optional[List[Dict]] = None,
        ats: Optional[List[Dict]] = None,
        is_private: bool = False,
        post_time: Optional[str] = None
    ) -> Dict:
        """
        发布图文笔记
        
        参数:
            title: 笔记标题
            desc: 笔记内容
            image_paths: 图片路径列表
            topics: 话题列表，格式为[{"id": "话题ID", "name": "话题名称", "type": "topic"}]
            ats: @用户列表，格式为[{"nickname": "用户昵称", "user_id": "用户ID", "name": "用户名称"}]
            is_private: 是否设为私密笔记
            post_time: 发布时间，格式为"YYYY-MM-DD HH:MM:SS"
            
        返回:
            发布结果
        """
        # 检查图片文件是否存在
        for image_path in image_paths:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 发布笔记
        result = self.client.create_image_note(
            title=title,
            desc=desc,
            files=image_paths,
            topics=topics or [],
            ats=ats or [],
            is_private=is_private,
            post_time=post_time
        )
        
        return result
    
    def publish_video_note(
        self,
        title: str,
        desc: str,
        video_path: str,
        cover_path: Optional[str] = None,
        topics: Optional[List[Dict]] = None,
        ats: Optional[List[Dict]] = None,
        is_private: bool = False,
        post_time: Optional[str] = None
    ) -> Dict:
        """
        发布视频笔记
        
        参数:
            title: 视频标题
            desc: 视频内容
            video_path: 视频文件路径
            cover_path: 封面图片路径（可选）
            topics: 话题列表，格式为[{"id": "话题ID", "name": "话题名称", "type": "topic"}]
            ats: @用户列表，格式为[{"nickname": "用户昵称", "user_id": "用户ID", "name": "用户名称"}]
            is_private: 是否设为私密笔记
            post_time: 发布时间，格式为"YYYY-MM-DD HH:MM:SS"
            
        返回:
            发布结果
        """
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 检查封面图片是否存在
        if cover_path and not os.path.exists(cover_path):
            raise FileNotFoundError(f"封面图片不存在: {cover_path}")
        
        # 发布笔记
        result = self.client.create_video_note(
            title=title,
            desc=desc,
            video_path=video_path,
            cover_path=cover_path,
            topics=topics or [],
            ats=ats or [],
            is_private=is_private,
            post_time=post_time
        )
        
        return result
    
    def get_note_stats(self, note_id: str) -> Dict:
        """
        获取笔记的统计数据（点赞、评论、收藏）
        
        参数:
            note_id: 笔记ID
            
        返回:
            笔记统计数据
        """
        try:
            # 获取笔记详情
            note_detail = self.client.get_note_by_id(note_id)
            
            # 检查返回值是否为None
            if note_detail is None:
                print(f"获取笔记详情返回None: {note_id}")
                return {
                    "note_id": note_id,
                    "title": "",
                    "desc": "",
                    "likes": 0,
                    "comments": 0,
                    "collects": 0,
                    "shares": 0,
                    "views": 0,
                    "time": "",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 提取统计数据
            stats = {
                "note_id": note_id,
                "title": note_detail.get("title", ""),
                "desc": note_detail.get("desc", ""),
                "likes": note_detail.get("likes", 0),
                "comments": note_detail.get("comments", 0),
                "collects": note_detail.get("collects", 0),
                "shares": note_detail.get("shares", 0),
                "views": note_detail.get("views", 0),
                "time": note_detail.get("time", ""),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return stats
        except DataFetchError as e:
            print(f"获取笔记统计数据失败: {e}")
            return {
                "note_id": note_id,
                "error": str(e),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_note_comments(self, note_id: str, cursor: str = "", count: int = 20) -> Dict:
        """
        获取笔记的评论
        
        参数:
            note_id: 笔记ID
            cursor: 分页游标
            count: 每页评论数量
            
        返回:
            评论列表和分页信息
        """
        try:
            # 获取笔记评论
            comments_data = self.client.get_note_comments(note_id, cursor, count)
            
            # 检查返回值是否为None
            if comments_data is None:
                print(f"获取笔记评论返回None: {note_id}")
                return {
                    "note_id": note_id,
                    "comments": [],
                    "has_more": False,
                    "cursor": "",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 提取评论数据
            comments = []
            for comment in comments_data.get("comments", []):
                comments.append({
                    "comment_id": comment.get("id", ""),
                    "content": comment.get("content", ""),
                    "user_id": comment.get("user_id", ""),
                    "nickname": comment.get("nickname", ""),
                    "avatar": comment.get("avatar", ""),
                    "likes": comment.get("likes", 0),
                    "time": comment.get("time", ""),
                    "sub_comments": comment.get("sub_comment_count", 0)
                })
            
            return {
                "note_id": note_id,
                "comments": comments,
                "has_more": comments_data.get("has_more", False),
                "cursor": comments_data.get("cursor", ""),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except DataFetchError as e:
            print(f"获取笔记评论失败: {e}")
            return {
                "note_id": note_id,
                "comments": [],
                "error": str(e),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_followers(self, cursor: str = "", count: int = 20) -> Dict:
        """
        获取关注者列表
        
        参数:
            cursor: 分页游标
            count: 每页数量
            
        返回:
            关注者列表和分页信息
        """
        try:
            # 获取关注者列表
            followers_data = self.client.get_follow_notifications(count, cursor)
            
            # 检查返回值是否为None
            if followers_data is None:
                print("获取关注者列表返回None")
                return {
                    "followers": [],
                    "has_more": False,
                    "cursor": "",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # 提取关注者数据
            followers = []
            for follower in followers_data.get("message_list", []):
                if follower.get("type") == "follow/you":
                    user_info = follower.get("user", {})
                    followers.append({
                        "user_id": user_info.get("userid", ""),
                        "nickname": user_info.get("nickname", ""),
                        "avatar": user_info.get("images", ""),
                        "desc": "",  # 返回数据中没有描述字段
                        "gender": 0,  # 返回数据中没有性别字段
                        "follow_status": 1 if user_info.get("fstatus") == "fans" else (2 if user_info.get("fstatus") == "both" else 0),
                        "followed_time": datetime.fromtimestamp(follower.get("time", 0)).strftime("%Y-%m-%d %H:%M:%S") if follower.get("time") else ""
                    })
            
            return {
                "followers": followers,
                "has_more": followers_data.get("has_more", False),
                "cursor": followers_data.get("cursor", ""),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"获取关注者列表失败: {e}")
            return {
                "followers": [],
                "error": str(e),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_note_by_id(self, note_id, xsec_token=None):
        """
        获取笔记详情（使用新API）
        
        参数:
            note_id: 笔记ID
            xsec_token: 可选，指定xsec_token
            
        返回:
            笔记详情数据
        """
        try:
            # 使用正确的API调用方式
            uri = '/api/sns/web/v1/feed'
            
            # 优先使用传入的xsec_token，其次使用已存储的，最后随机生成
            if not xsec_token:
                xsec_token = self.xsec_tokens.get(note_id)
            
            if not xsec_token:
                xsec_token = generate_xsec_token()
                print(f"未找到笔记 {note_id} 的xsec_token，使用随机生成的token")
            else:
                print(f"使用已有的xsec_token: {xsec_token[:10]}...")
            
            data = {
                "source_note_id": note_id,
                "image_formats": ["jpg", "webp", "avif"],
                "extra": {"need_body_topic": "1"},
                "xsec_source": "pc_search",
                "xsec_token": xsec_token
            }
            
            res = self.client.post(uri, data=data)
            
            if isinstance(res, dict) and "items" in res and len(res["items"]) > 0:
                note_card = res["items"][0]["note_card"]
                # 保存获取到的xsec_token以备后用
                if "xsec_token" in note_card:
                    self.xsec_tokens[note_id] = note_card["xsec_token"]
                    print(f"已保存笔记 {note_id} 的xsec_token: {note_card['xsec_token'][:10]}...")
                return note_card
            else:
                print(f"获取笔记失败，返回数据结构不符合预期: {res}")
                return None
        except Exception as e:
            print(f"获取笔记失败: {e}")
            traceback.print_exc()
            return None
    
    def get_user_notes(self, user_id, cursor="", count=20):
        """
        获取用户笔记列表（使用新API）
        
        参数:
            user_id: 用户ID
            cursor: 分页游标
            count: 每页数量
            
        返回:
            笔记列表
        """
        try:
            uri = '/api/sns/web/v1/user_posted'
            xsec_token = generate_xsec_token()
            
            params = {
                "num": count, 
                "cursor": cursor, 
                "user_id": user_id, 
                "image_scenes": "FD_WM_WEBP",
                "xsec_source": "pc_profile",
                "xsec_token": xsec_token
            }
            
            result = self.client.get(uri, params)

            
            # 检查返回结果的结构
            if isinstance(result, dict):
                # 如果直接返回了notes数组
                if "notes" in result:
                    notes = result.get("notes", [])
                    # 保存笔记的xsec_token
                    for note in notes:
                        if "note_id" in note and "xsec_token" in note:
                            self.xsec_tokens[note["note_id"]] = note["xsec_token"]
                            print(f"已保存笔记 {note['note_id']} 的xsec_token: {note['xsec_token'][:10]}...")
                    return notes
                # 如果返回了success字段
                elif result.get("success") is True and result.get("data") is not None:
                    data = result.get("data")
                    if "notes" in data:
                        notes = data.get("notes", [])
                        # 保存笔记的xsec_token
                        for note in notes:
                            if "note_id" in note and "xsec_token" in note:
                                self.xsec_tokens[note["note_id"]] = note["xsec_token"]
                                print(f"已保存笔记 {note['note_id']} 的xsec_token: {note['xsec_token'][:10]}...")
                        return notes
            
            print(f"获取用户笔记失败，API返回: {result}")
            return []
        except Exception as e:
            print(f"获取用户笔记失败: {e}")
            traceback.print_exc()
            return []
