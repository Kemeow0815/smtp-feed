#!/usr/bin/env python3
"""
Subscription Handler
处理 GitHub Issues 订阅请求，验证邮箱并发送确认邮件
"""

import os
import json
import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 配置
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
BLOG_NAME = os.environ.get('BLOG_NAME', '博客')
BLOG_URL = os.environ.get('BLOG_URL', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')
ISSUE_NUMBER = os.environ.get('ISSUE_NUMBER')
ISSUE_BODY = os.environ.get('ISSUE_BODY', '')
ISSUE_TITLE = os.environ.get('ISSUE_TITLE', '')

SUBSCRIBERS_FILE = 'data/subscribers.json'


def load_json_file(filepath, default=None):
    """加载 JSON 文件"""
    if default is None:
        default = []
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


def extract_email(text):
    """从文本中提取邮箱地址"""
    if not text:
        return None
    
    # 匹配邮箱正则
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    
    if match:
        return match.group(0).lower()
    return None


def is_valid_email(email):
    """验证邮箱格式"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def load_email_template(template_name):
    """加载邮件模板"""
    template_path = f'templates/{template_name}.html'
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def render_welcome_email(email):
    """渲染欢迎邮件"""
    template = load_email_template('welcome')
    
    if template:
        html = template.replace('{{BLOG_NAME}}', BLOG_NAME)
        html = html.replace('{{BLOG_URL}}', BLOG_URL)
        html = html.replace('{{EMAIL}}', email)
        html = html.replace('{{GITHUB_REPO}}', GITHUB_REPO)
        html = html.replace('{{SUBSCRIBE_TIME}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return html
    else:
        # 默认模板
        return f'''
        <div class="twikoo-main">
            <center>
                <h3>🎉 订阅成功!</h3>
            </center>
            <hr class="twikoo-hr">
            <p class="twikoo-bold">您好!</p>
            <p>感谢您订阅 <a class="twikoo-link" href="{BLOG_URL}">{BLOG_NAME}</a> 的文章更新通知。</p>
            <p>您的邮箱 <strong>{email}</strong> 已成功添加到订阅列表。</p>
            <p>每当博客有新文章发布时，您将收到邮件通知。</p>
            <br>
            <div class="twikoo-chakan">
                <a href="{BLOG_URL}" target="_blank">访问博客 &gt;&gt;</a>
            </div>
            <br>
            <p style="font-size: 12px; color: #999;">
                如不想继续接收通知，可<a href="https://github.com/{GITHUB_REPO}/issues/new?template=unsubscribe.yml">点击退订</a>
            </p>
            <div class="twikoo-footer-p">
                <hr class="twikoo-footer-hr">
                © {datetime.now().year} <a href="{BLOG_URL}" class="twikoo-footer-link" target="_blank">{BLOG_NAME}</a>
            </div>
        </div>
        '''


def render_error_email(email, error_message):
    """渲染错误邮件"""
    return f'''
    <div class="twikoo-main">
        <center>
            <h3 style="color: #ff5f56;">⚠️ 订阅遇到问题</h3>
        </center>
        <hr class="twikoo-hr">
        <p class="twikoo-bold">您好!</p>
        <p>您在 <a class="twikoo-link" href="{BLOG_URL}">{BLOG_NAME}</a> 的订阅请求遇到了问题:</p>
        <div class="twikoo-content" style="border-left-color: #ff5f56;">
            <p style="color: #ff5f56; margin: 0;">{error_message}</p>
        </div>
        <p>请检查您提供的信息是否正确，然后重新提交订阅请求。</p>
        <br>
        <div class="twikoo-chakan">
            <a href="{BLOG_URL}" target="_blank">访问博客 &gt;&gt;</a>
        </div>
        <div class="twikoo-footer-p">
            <hr class="twikoo-footer-hr">
            © {datetime.now().year} <a href="{BLOG_URL}" class="twikoo-footer-link" target="_blank">{BLOG_NAME}</a>
        </div>
    </div>
    '''


def send_email(to_email, subject, html_content):
    """发送邮件"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = Header(f"{BLOG_NAME} <{FROM_EMAIL}>", 'utf-8')
        msg['To'] = Header(to_email, 'utf-8')
        
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


def add_subscriber(email, issue_number):
    """添加订阅者"""
    subscribers = load_json_file(SUBSCRIBERS_FILE, [])
    
    # 检查是否已存在
    for sub in subscribers:
        if sub.get('email') == email:
            # 更新状态
            sub['status'] = 'confirmed'
            sub['issue_state'] = 'closed'
            sub['confirmed_at'] = datetime.now().isoformat()
            sub['issue_number'] = issue_number
            save_json_file(SUBSCRIBERS_FILE, subscribers)
            return False  # 已存在
    
    # 添加新订阅者
    new_subscriber = {
        'email': email,
        'issue_number': issue_number,
        'status': 'confirmed',
        'issue_state': 'closed',
        'created_at': datetime.now().isoformat(),
        'confirmed_at': datetime.now().isoformat()
    }
    subscribers.append(new_subscriber)
    save_json_file(SUBSCRIBERS_FILE, subscribers)
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("Subscription Handler 启动")
    print("=" * 50)
    
    # 检查必要的环境变量
    required_vars = ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'FROM_EMAIL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        return
    
    print(f"处理 Issue #{ISSUE_NUMBER}")
    print(f"Issue 标题: {ISSUE_TITLE}")
    print(f"Issue 内容: {ISSUE_BODY[:200]}...")
    
    # 提取邮箱
    email = extract_email(ISSUE_BODY) or extract_email(ISSUE_TITLE)
    
    if not email:
        print("错误: 无法从 Issue 中提取邮箱地址")
        return
    
    print(f"提取到邮箱: {email}")
    
    # 验证邮箱格式
    if not is_valid_email(email):
        print(f"错误: 邮箱格式无效: {email}")
        # 发送错误通知
        error_html = render_error_email(email, "邮箱格式无效，请检查您输入的邮箱地址。")
        send_email(email, f"[{BLOG_NAME}] 订阅失败通知", error_html)
        return
    
    # 添加到订阅列表
    is_new = add_subscriber(email, ISSUE_NUMBER)
    
    if is_new:
        print(f"新订阅者已添加: {email}")
    else:
        print(f"订阅者已存在，状态已更新: {email}")
    
    # 发送欢迎邮件
    welcome_html = render_welcome_email(email)
    subject = f"🎉 欢迎订阅 {BLOG_NAME}！"
    
    if send_email(email, subject, welcome_html):
        print(f"欢迎邮件发送成功: {email}")
    else:
        print(f"欢迎邮件发送失败: {email}")
    
    print("=" * 50)
    print("Subscription Handler 完成")
    print("=" * 50)


if __name__ == '__main__':
    main()
