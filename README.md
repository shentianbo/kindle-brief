# Kindle Daily Brief v2

每天自动抓取4个专题 → DeepSeek中文深度总结 → 生成带封面的EPUB → 推送Kindle。

## 文件结构

```
kindle-brief/
├── daily_brief.py        # 主脚本
├── config.py             # 章节、RSS源、Prompt配置
├── requirements.txt
└── .github/
    └── workflows/
        └── daily_brief.yml
```

## 四个专题

| 章节 | 内容 | 密度 |
|------|------|------|
| 西非 & 北非 · Mobile Money | Wave/Orange竞品、BCEAO监管、非洲Fintech | 高，保留数据和竞品信息 |
| AI 业界动态 | MIT Tech Review、HN、The Verge | 中，趋势为主 |
| AI on GitHub | GitHub Trending、GitHub Blog | 中，项目亮点+应用场景 |
| 心理学 · 人格与关系 | Psychology Today、Greater Good | 高，五层深度展开 |

## 部署步骤

### 第一步：Gmail 应用专用密码

1. 登录 Gmail → 账号设置 → 安全
2. 开启两步验证（必须先开）
3. 搜索「App passwords」→ 选 Mail + Other → 生成16位密码
4. 复制保存，只显示一次

### 第二步：Amazon 白名单

1. 打开 https://www.amazon.com/mycd
2. 首选项 → 已批准的个人文档电子邮件列表
3. 添加你的 Gmail 地址

### 第三步：查 Kindle 邮箱

同上页面 → 设备 → 找到你的Kindle → Send-to-Kindle 邮箱（格式：xxx@kindle.com）

### 第四步：GitHub Secrets

仓库 → Settings → Secrets and variables → Actions → New repository secret

| 名称 | 值 |
|------|-----|
| `DEEPSEEK_API_KEY` | https://platform.deepseek.com 控制台获取 |
| `SENDER_EMAIL` | 你的Gmail地址 |
| `SENDER_PASSWORD` | 上面生成的16位应用密码 |
| `KINDLE_EMAIL` | xxx@kindle.com |

### 第五步：Push，完成

每天北京时间 09:00 自动运行。
也可以在 Actions 页面点「Run workflow」立即测试。

## 自定义

### 修改RSS源

编辑 `config.py` 中的 `CHAPTERS`，每个章节的 `feeds` 列表按需增删：

```python
{
    "name": "你的源名称",
    "url":  "https://example.com/feed.xml",
},
```

### 修改发送时间

编辑 `.github/workflows/daily_brief.yml` 中的 cron：

```yaml
- cron: '0 1 * * *'   # UTC 01:00 = 北京 09:00
- cron: '0 0 * * *'   # UTC 00:00 = 北京 08:00
- cron: '30 22 * * *' # UTC 22:30 = 北京 06:30
```

### 修改心理学章节深度

在 `config.py` 的 `ARTICLE_PROMPT` 里调整字数要求。

## 成本估算

| 项目 | 费用 |
|------|------|
| GitHub Actions | 免费（私有仓库2000分钟/月，本脚本约5分钟/次） |
| DeepSeek API | 约 $0.01-0.02/天（4章节，心理学章节token较多） |
| Jina Reader | 免费额度200次/天，足够 |
| Gmail SMTP | 免费 |

## 常见问题

**Kindle收不到文件？**
- 检查发件Gmail是否在Amazon白名单
- 确认Subject是"convert"（代码里已设置）
- 检查Kindle是否联网

**某个RSS源抓不到？**
- 正常现象，源可能临时失效
- 脚本会跳过失败的源，继续处理其他源
- 在Actions日志里可以看到每个源的抓取结果

**DeepSeek超时？**
- 心理学章节token较多，90秒超时基本够
- 如果频繁超时，在config.py里把`max_per_feed`改小
