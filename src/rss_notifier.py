#!/usr/bin/env python3
"""
RSS Feed Notifier
抓取博客 RSS 并检测文章变更（新增/删除），然后发送邮件通知给订阅者
"""

import os
import json
import re
import smtplib
import base64
import feedparser
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from urllib.parse import quote
import urllib.request

# 配置
RSS_URL = os.environ.get('RSS_URL')
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
BLOG_NAME = os.environ.get('BLOG_NAME', '博客')
BLOG_URL = os.environ.get('BLOG_URL', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')

DATA_FILE = 'data/feed_history.json'
SUBSCRIBERS_FILE = 'data/subscribers.json'


def load_json_file(filepath, default=None):
    """加载 JSON 文件"""
    if default is None:
        default = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json_file(filepath, data):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_rss_feed():
    """解析 RSS Feed"""
    print(f"正在抓取 RSS: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    articles = {}
    for entry in feed.entries:
        # 使用链接作为唯一标识
        article_id = entry.get('id', entry.get('link', ''))
        articles[article_id] = {
            'title': entry.get('title', '无标题'),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', entry.get('description', '')),
            'author': entry.get('author', ''),
        }
    
    print(f"获取到 {len(articles)} 篇文章")
    return articles


def detect_changes(current_articles, previous_articles):
    """检测文章变更"""
    current_ids = set(current_articles.keys())
    previous_ids = set(previous_articles.keys())
    
    # 新增的文章
    added_ids = current_ids - previous_ids
    # 删除的文章
    removed_ids = previous_ids - current_ids
    
    added = [current_articles[id] for id in added_ids]
    removed = [previous_articles[id] for id in removed_ids]
    
    return added, removed


def load_email_template(template_name):
    """加载邮件模板"""
    template_path = f'templates/{template_name}.html'
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def render_update_email(added, removed):
    """渲染更新通知邮件"""
    template = load_email_template('update_notification')
    
    # 构建新增文章列表
    added_html = ''
    if added:
        added_items = ''
        for article in added:
            added_items += f'''
            <div style="margin: 15px 0; padding: 15px; border-radius: 10px; border: 1px solid #ddd; box-shadow: inset 3px 3px 6px #f4f4f4, inset -3px -3px 6px #dcdcdc;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{article['title']}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 13px;">发布时间: {article['published']}</p>
                <p style="margin: 10px 0; color: #555; font-size: 14px;">{article['summary'][:200]}...</p>
                <div class="twikoo-chakan" style="margin-top: 10px;">
                    <a href="{article['link']}" target="_blank">阅读全文 &gt;&gt;</a>
                </div>
            </div>
            '''
        added_html = f'''
        <p class="twikoo-bold" style="color: #27c93f;">📢 新增文章 ({len(added)} 篇):</p>
        {added_items}
        '''
    
    # 构建删除文章列表
    removed_html = ''
    if removed:
        removed_items = ''
        for article in removed:
            removed_items += f'''
            <div style="margin: 10px 0; padding: 10px; border-radius: 8px; background: #f5f5f5; border-left: 3px solid #ff5f56;">
                <p style="margin: 0; color: #666; text-decoration: line-through;">{article['title']}</p>
            </div>
            '''
        removed_html = f'''
        <p class="twikoo-bold" style="color: #ff5f56;">🗑️ 已删除文章 ({len(removed)} 篇):</p>
        {removed_items}
        '''
    
    # 如果没有变更
    if not added and not removed:
        return None
    
    # 替换模板变量
    if template:
        html = template.replace('{{BLOG_NAME}}', BLOG_NAME)
        html = html.replace('{{BLOG_URL}}', BLOG_URL)
        html = html.replace('{{ADDED_ARTICLES}}', added_html)
        html = html.replace('{{REMOVED_ARTICLES}}', removed_html)
        html = html.replace('{{UPDATE_TIME}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return html
    else:
        # 默认模板
        return f'''
        <div class="twikoo-main">
            <center>
                <h3>📝 {BLOG_NAME} 文章更新通知</h3>
            </center>
            <hr class="twikoo-hr">
            {added_html}
            {removed_html}
            <p class="twikoo-bold">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="twikoo-chakan">
                <a href="{BLOG_URL}" target="_blank">访问博客 &gt;&gt;</a>
            </div>
            <div class="twikoo-footer-p">
                <hr class="twikoo-footer-hr">
                © {datetime.now().year} <a href="{BLOG_URL}" class="twikoo-footer-link" target="_blank">{BLOG_NAME}</a>
            </div>
        </div>
        '''


def encode_header(text):
    """对邮件头进行 RFC2047 编码"""
    try:
        # 如果全是 ASCII 字符，直接返回
        text.encode('ascii')
        return text
    except UnicodeEncodeError:
        # 包含非 ASCII 字符，使用 Base64 编码
        encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
        return f'=?UTF-8?B?{encoded}?='


def send_email(to_email, subject, html_content):
    """发送邮件"""
    try:
        msg = MIMEMultipart('alternative')
        
        # 对主题进行编码
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 对发件人名称进行 RFC2047 编码
        encoded_name = encode_header(BLOG_NAME)
        msg['From'] = f'{encoded_name} <{FROM_EMAIL}>'
        
        # 收件人
        msg['To'] = to_email
        
        # 添加 HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 连接 SMTP 服务器
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        # 发送邮件
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        
        print(f"邮件已发送至: {to_email}")
        return True
    except Exception as e:
        print(f"发送邮件失败 ({to_email}): {e}")
        return False


def get_active_subscribers():
    """获取活跃的订阅者（议题已关闭的）"""
    subscribers = load_json_file(SUBSCRIBERS_FILE, [])
    active_subscribers = []
    
    for sub in subscribers:
        if sub.get('status') == 'confirmed' and sub.get('issue_state') == 'closed':
            active_subscribers.append(sub)
    
    return active_subscribers


def main():
    """主函数"""
    print("=" * 50)
    print("RSS Feed Notifier 启动")
    print("=" * 50)
    
    # 检查必要的环境变量
    required_vars = ['RSS_URL', 'SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'FROM_EMAIL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        return
    
    # 加载历史数据
    history = load_json_file(DATA_FILE, {})
    previous_articles = history.get('articles', {})
    
    # 解析 RSS
    current_articles = parse_rss_feed()
    
    # 检测变更
    added, removed = detect_changes(current_articles, previous_articles)
    
    print(f"新增文章: {len(added)} 篇")
    print(f"删除文章: {len(removed)} 篇")
    
    # 如果有变更，发送通知
    if added or removed:
        # 渲染邮件内容
        email_html = render_update_email(added, removed)
        
        if email_html:
            # 获取活跃订阅者
            subscribers = get_active_subscribers()
            print(f"活跃订阅者数量: {len(subscribers)}")
            
            # 发送邮件给每个订阅者
            subject = f"[{BLOG_NAME}] 文章更新通知 - {datetime.now().strftime('%m-%d')}"
            success_count = 0
            
            for sub in subscribers:
                email = sub.get('email')
                if email:
                    if send_email(email, subject, email_html):
                        success_count += 1
            
            print(f"邮件发送成功: {success_count}/{len(subscribers)}")
    else:
        print("没有检测到文章变更")
    
    # 保存当前状态
    history['articles'] = current_articles
    history['last_check'] = datetime.now().isoformat()
    save_json_file(DATA_FILE, history)
    
    print("=" * 50)
    print("RSS Feed Notifier 完成")
    print("=" * 50)


if __name__ == '__main__':
    main()
