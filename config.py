"""
配置文件：章节定义、RSS源、DeepSeek Prompt
按需修改 CHAPTERS 里的 feeds，其他部分不需要动
"""

# ═══════════════════════════════════════════════════════════════
# 章节与RSS源配置
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# DeepSeek 模型配置
# ═══════════════════════════════════════════════════════════════

# 可选值：
#   "deepseek-v4-flash"  → 快速经济，日常简报使用，推荐
#   "deepseek-v4-pro"    → 深度推理，慢约4倍，价格约4倍
#
# 注：旧名称 deepseek-chat / deepseek-reasoner 将于 2026-07-24 废弃
#     现在已透明路由到 v4-flash，建议直接用新名称
DEEPSEEK_MODEL = "deepseek-v4-flash"

CHAPTERS = [
    {
        "title": "西非 & 北非 · Mobile Money",
        "is_psych": False,
        "use_fulltext": False,
        "max_per_feed": 4,
        "feeds": [
            {
                "name": "TechAfrica",
                "url":  "https://techinafrica.com/feed/",
            },
            {
                "name": "Reuters Africa",
                "url":  "https://feeds.reuters.com/reuters/AFRICANews",
            },
            {
                "name": "GSMA Intelligence",
                "url":  "https://www.gsma.com/feed/",
            },
            {
                "name": "Mondafrique",           # 法语非洲商业新闻
                "url":  "https://mondafrique.com/feed/",
            },
            {
                "name": "Disrupt Africa",
                "url":  "https://disrupt-africa.com/feed/",
            },
        ],
    },
    {
        "title": "AI 业界动态",
        "is_psych": False,
        "use_fulltext": False,
        "max_per_feed": 4,
        "feeds": [
            {
                "name": "MIT Technology Review",
                "url":  "https://www.technologyreview.com/feed/",
            },
            {
                "name": "Hacker News",
                "url":  "https://hnrss.org/frontpage?count=20",
            },
            {
                "name": "The Verge · AI",
                "url":  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            },
            {
                "name": "VentureBeat AI",
                "url":  "https://venturebeat.com/category/ai/feed/",
            },
        ],
    },
    {
        "title": "AI on GitHub",
        "is_psych": False,
        "use_fulltext": False,
        "max_per_feed": 5,
        "feeds": [
            {
                "name": "GitHub Blog",
                "url":  "https://github.blog/feed/",
            },
            {
                "name": "GitHub Trending (AI)",   # 需要爬虫，见注释
                # GitHub Trending 没有官方RSS，这里用第三方镜像
                "url":  "https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml",
            },
            {
                "name": "GitHub Trending (All)",
                "url":  "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
            },
        ],
    },
    {
        "title": "心理学 · 人格与关系",
        "is_psych": True,      # 触发深度展开模式
        "use_fulltext": True,  # 用 jina reader 抓全文
        "max_per_feed": 2,     # 每源只取2篇，但每篇深度展开
        "feeds": [
            {
                "name": "Psychology Today",
                "url":  "https://www.psychologytoday.com/us/front/feed",
            },
            {
                "name": "Greater Good Magazine",
                "url":  "https://greatergood.berkeley.edu/feeds/news",
            },
            {
                "name": "Noba Project",
                "url":  "https://nobaproject.com/feed",
            },
        ],
    },
]


# ═══════════════════════════════════════════════════════════════
# DeepSeek Prompt
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个服务于特定读者的专业简报助手。

读者背景：
- 华为驻西非移动支付运营专家，负责科特迪瓦、多哥、贝宁、布基纳法索等账户
- 对AI技术和GitHub开源生态有持续关注
- 对人格心理学、依恋理论、亲密关系动态有个人研究兴趣，无学术背景但阅读能力强
- 阅读速度快，偏好信息密度高的内容，不喜欢废话和套话

输出要求：
- 用中文
- 保留英文专业术语（Mobile Money、ARPU、KYC、LLM等）
- 不说"值得关注"、"具有重要意义"这类空话
- 每个观点要有依据，数据要标注来源
- "为什么重要"部分必须落地到读者的实际工作或生活场景，不能泛泛而谈"""


ARTICLE_PROMPT_REGULAR = """请对以下「{chapter_title}」章节的文章进行简报整理。

普通章节格式：每条文章严格按照固定格式输出。

每条文章格式：

【标题】（原文标题的中文翻译，保留关键英文术语）
一句话：（15字以内，核心事件或发现）
关键信息：
· 要点1（数据/事实/具体细节）
· 要点2
· 要点3（如有）
· 要点4（如有）
为什么重要：（2-4句，结合读者背景说明实际意义，Mobile Money章节落到具体账户和竞争影响，AI章节落到工具使用和技术趋势，GitHub章节说明项目亮点和潜在应用）

文章内容：
{raw_block}

注意：
1. 如果某篇文章内容太短或质量差，可以跳过
2. 输出纯文本+基本Markdown（**粗体**、*斜体*、· 列表），不要输出HTML标签
3. 文章之间用 --- 分隔"""


ARTICLE_PROMPT_PSYCH = """请对以下「{chapter_title}」章节的文章进行简报整理。

心理学章节特殊要求：每篇文章需要五个层次：背景理论解释（从零开始，不假设读者有专业背景）、研究发现（具体数据和方法）、核心概念深度展开（真正的分析）、延伸维度（一个额外视角）、三个递进层次的延伸思考问题。

每条文章格式：

【标题】（原文标题的中文翻译，保留关键英文术语）
一句话：（15字以内，核心事件或发现）
关键信息：
· 要点1（数据/事实/具体细节）
· 要点2
· 要点3（如有）
· 要点4（如有）
为什么重要：（2-4句，结合读者背景说明实际意义）
背景理论：（解释核心心理学概念，从历史和学术来源入手，200字左右）
核心展开：（真正的分析，不只是结论，解释机制和原因，150-200字）
延伸维度：（一个额外的视角，可以是神经科学、文化差异、与其他理论的联结等，100字）
延伸思考：（三个递进问题，表层→中层→深层，引导读者自我代入）

文章内容：
{raw_block}

注意：
1. 如果某篇文章内容太短或质量差，可以跳过
2. 输出纯文本+基本Markdown（**粗体**、*斜体*、· 列表），不要输出HTML标签
3. 文章之间用 --- 分隔"""
