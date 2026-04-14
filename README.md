# 博客 RSS 邮件订阅系统

基于 GitHub Actions 的博客更新邮件通知系统，支持 RSS Feed 监控和邮件订阅管理。

## 功能特性

- 📡 **RSS 自动监控**: 定时抓取博客 RSS，检测文章新增和删除
- 📧 **邮件通知**: 自动发送文章更新通知给订阅者
- ✅ **订阅确认**: 通过 GitHub Issues 管理订阅，关闭议题后触发确认
- ❌ **退订功能**: 支持用户通过 Issues 提交退订请求
- 🔒 **状态管理**: 议题打开时不发送通知，关闭后才激活订阅
- 🎨 **精美邮件模板**: 使用新拟态设计风格

## 项目结构

```
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── subscribe.yml      # 订阅表单模板
│   │   └── unsubscribe.yml    # 退订表单模板
│   └── workflows/
│       ├── rss-check.yml      # RSS 监控工作流
│       ├── subscribe.yml      # 订阅处理工作流
│       └── unsubscribe.yml    # 退订处理工作流
├── src/
│   ├── rss_notifier.py        # RSS 抓取和通知脚本
│   ├── subscription_handler.py # 订阅处理脚本
│   └── unsubscribe_handler.py # 退订处理脚本
├── templates/
│   ├── update_notification.html # 更新通知邮件模板
│   ├── welcome.html           # 欢迎邮件模板
│   └── unsubscribe_success.html # 退订成功邮件模板
├── data/
│   ├── feed_history.json      # RSS 历史数据
│   └── subscribers.json       # 订阅者列表
├── .env.example               # 环境变量示例
└── README.md
```

## 快速开始

### 1. 创建 GitHub 仓库

将此项目代码推送到你的 GitHub 仓库。

### 2. 配置环境变量

在仓库 Settings -> Secrets and variables -> Actions 中添加以下 Secrets:

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `RSS_URL` | 博客 RSS 地址 | `https://example.com/feed.xml` |
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 | `587` |
| `SMTP_USER` | SMTP 用户名 | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP 密码或授权码 | `your-app-password` |
| `FROM_EMAIL` | 发件人邮箱 | `noreply@example.com` |
| `BLOG_NAME` | 博客名称 | `我的博客` |
| `BLOG_URL` | 博客地址 | `https://example.com` |

### 3. 创建订阅议题模板

在 `.github/ISSUE_TEMPLATE/` 目录下创建 `subscribe.yml`:

```yaml
name: 订阅博客更新
about: 提交您的邮箱订阅博客文章更新通知
title: "[Subscribe] "
labels: ["subscribe"]
body:
  - type: markdown
    attributes:
      value: |
        ## 订阅博客更新通知
        请输入您的邮箱地址，关闭此议题后将发送确认邮件。
  
  - type: input
    id: email
    attributes:
      label: 邮箱地址
      description: 用于接收博客更新通知的邮箱
      placeholder: example@email.com
    validations:
      required: true
  
  - type: checkboxes
    id: agreement
    attributes:
      label: 确认事项
      options:
        - label: 我确认提交的邮箱地址正确，并同意接收博客更新通知
          required: true
```

### 4. 启动工作流

- **RSS 监控**: 每 6 小时自动运行，或手动触发
- **订阅处理**: 当带有 `subscribe` 标签的议题被关闭时自动触发
- **退订处理**: 当带有 `unsubscribe` 标签的议题被关闭时自动触发

## 工作流程

### 订阅流程

1. 用户创建订阅议题，填写邮箱地址
2. 管理员审核后关闭议题
3. 工作流自动触发，发送确认邮件
4. 邮箱被添加到订阅列表

### 退订流程

1. 用户创建退订议题，填写要退订的邮箱地址
2. 管理员关闭议题
3. 工作流自动触发，从订阅列表移除邮箱
4. 发送退订成功确认邮件

### 通知流程

1. 定时工作流抓取 RSS Feed
2. 对比历史数据，检测文章变更（新增/删除）
3. 获取所有已确认且议题关闭的订阅者
4. 发送更新通知邮件

## 邮件模板

系统包含三个邮件模板:

- **欢迎邮件** (`templates/welcome.html`): 订阅确认后发送
- **更新通知** (`templates/update_notification.html`): 文章更新时发送
- **退订成功** (`templates/unsubscribe_success.html`): 退订成功后发送

你可以自定义这些模板，支持以下变量:

### 欢迎邮件变量
- `{{BLOG_NAME}}` - 博客名称
- `{{BLOG_URL}}` - 博客地址
- `{{EMAIL}}` - 订阅者邮箱
- `{{SUBSCRIBE_TIME}}` - 订阅时间
- `{{GITHUB_REPO}}` - GitHub 仓库地址

### 更新通知变量
- `{{BLOG_NAME}}` - 博客名称
- `{{BLOG_URL}}` - 博客地址
- `{{ADDED_ARTICLES}}` - 新增文章列表 HTML
- `{{REMOVED_ARTICLES}}` - 删除文章列表 HTML
- `{{UPDATE_TIME}}` - 更新时间

### 退订成功邮件变量
- `{{BLOG_NAME}}` - 博客名称
- `{{BLOG_URL}}` - 博客地址
- `{{EMAIL}}` - 退订邮箱
- `{{UNSUBSCRIBE_TIME}}` - 退订时间

## 数据存储

所有数据存储在仓库的 `data/` 目录下:

- `feed_history.json`: 存储 RSS 历史数据，用于检测变更
- `subscribers.json`: 存储订阅者信息

```json
// subscribers.json 格式
[
  {
    "email": "user@example.com",
    "issue_number": 1,
    "status": "confirmed",
    "issue_state": "closed",
    "created_at": "2026-01-01T00:00:00",
    "confirmed_at": "2026-01-01T00:00:00"
  }
]
```

## 自定义配置

### 修改检查频率

编辑 `.github/workflows/rss-check.yml`:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # 每 6 小时，可修改为其他频率
```

Cron 表达式参考:
- `0 */6 * * *` - 每 6 小时
- `0 0 * * *` - 每天凌晨
- `0 0 * * 0` - 每周日
- `*/30 * * * *` - 每 30 分钟

### 退订功能

退订功能已内置，用户可以通过以下方式退订:

1. 在欢迎邮件中点击"点击退订"链接
2. 手动创建带有 `unsubscribe` 标签的议题
3. 填写要退订的邮箱地址
4. 关闭议题后自动处理退订

## 常见问题

### Q: 邮件发送失败怎么办？

检查以下几点:
1. SMTP 配置是否正确
2. 邮箱是否开启了 SMTP 服务
3. 是否使用了正确的授权码（非邮箱密码）

### Q: 如何测试 RSS 抓取？

手动触发 `RSS Feed Check and Notify` 工作流，查看运行日志。

### Q: 订阅者没有收到通知？

检查:
1. 订阅议题是否已关闭
2. 邮箱格式是否正确
3. 邮件是否进入垃圾邮件箱

## 技术栈

- **GitHub Actions**: 工作流自动化
- **Python 3.11**: 脚本语言
- **feedparser**: RSS 解析
- **smtplib**: 邮件发送
- **HTML/CSS**: 邮件模板

## License

MIT License

## 作者

克喵爱吃卤面 - [喵洛阁](https://kemeow0815.github.io)
