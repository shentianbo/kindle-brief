"""
配置文件：章节定义、RSS源、DeepSeek Prompt
"""

# ═══════════════════════════════════════════════════════════════
# DeepSeek 模型配置
# ═══════════════════════════════════════════════════════════════
DEEPSEEK_MODEL = "deepseek-v4-flash"


# ═══════════════════════════════════════════════════════════════
# 章节与 RSS 源配置
# ═══════════════════════════════════════════════════════════════

CHAPTERS = [

    # ── 章节1：Mobile Money 竞争情报 ──────────────────────────
    {
        "title":        "Mobile Money 竞争情报",
        "chapter_type": "mm",
        "is_psych":     False,
        "use_fulltext": False,
        "max_per_feed": 5,
        "feeds": [
            # 西非科技/Fintech 核心媒体
            {"name": "TechCabal",         "url": "https://techcabal.com/feed/"},
            {"name": "Techpoint Africa",  "url": "https://techpoint.africa/feed/"},
            {"name": "Disrupt Africa",    "url": "https://disrupt-africa.com/feed/"},
            # 法语西非 + 北非商业
            {"name": "Mondafrique",       "url": "https://mondafrique.com/feed/"},
            # 泛非洲 + MENA（覆盖埃及/摩洛哥/突尼斯）
            {"name": "The Africa Report", "url": "https://www.theafricareport.com/feed/"},
            {"name": "Wamda",             "url": "https://www.wamda.com/feed"},
        ],
    },

    # ── 章节2：AI 工具与应用 ──────────────────────────────────
    {
        "title":        "AI 工具与应用",
        "chapter_type": "ai",
        "is_psych":     False,
        "use_fulltext": False,
        "max_per_feed": 4,
        "feeds": [
            # AI 热点
            {"name": "OpenAI Blog",          "url": "https://openai.com/news/rss.xml",                                    "subsection": "AI热点"},
            {"name": "MIT Tech Review",       "url": "https://www.technologyreview.com/feed/",                            "subsection": "AI热点"},
            {"name": "The Verge AI",          "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "subsection": "AI热点"},
            {"name": "Hacker News",           "url": "https://hnrss.org/frontpage?count=20",                             "subsection": "AI热点"},
            # GitHub 项目
            {"name": "GitHub Trending (Py)",  "url": "https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml",  "subsection": "GitHub项目"},
            {"name": "GitHub Trending (All)", "url": "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",     "subsection": "GitHub项目"},
            {"name": "GitHub Blog",           "url": "https://github.blog/feed/",                                         "subsection": "GitHub项目"},
        ],
    },

    # ── 章节3：心理学 · 依恋与人格 ───────────────────────────
    {
        "title":        "心理学 · 依恋与人格",
        "chapter_type": "psych",
        "is_psych":     True,
        "use_fulltext": True,
        "max_per_feed": 3,
        # 不在 fetch 阶段过滤，让 DeepSeek 根据 prompt 判断相关性
        "feeds": [
            {"name": "Psychology Today",      "url": "https://www.psychologytoday.com/us/front/feed"},
            {"name": "Greater Good Magazine", "url": "https://greatergood.berkeley.edu/feeds/news"},
            {"name": "Noba Project",          "url": "https://nobaproject.com/feed"},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════
# DeepSeek System Prompt
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个服务于特定读者的专业简报助手。

读者背景：
- 华为驻非洲移动支付运营专家，负责西非多个账户（科特迪瓦、多哥、贝宁、布基纳法索等）
- 长期跟踪非洲 Mobile Money 生态，熟悉 Wave、Orange Money、MTN MoMo、BCEAO 等
- 对 AI 工具和 GitHub 开源生态有持续关注
- 对依恋理论、人格心理学、亲密关系动态有个人研究兴趣

输出要求：
- 用中文
- 保留英文专业术语（Mobile Money、ARPU、KYC、LLM、OTT 等）
- 不说"值得关注"、"具有重要意义"这类空话
- 每个观点要有依据，数据标注来源
- 具体胜于抽象：点名玩家和市场，胜于泛泛而谈"""


# ═══════════════════════════════════════════════════════════════
# 章节 Prompt（三个独立模板）
# ═══════════════════════════════════════════════════════════════

ARTICLE_PROMPT_MM = """请对以下「Mobile Money 竞争情报」章节的文章进行简报整理。

聚焦点：非洲（西非 + 北非）Mobile Money 生态的竞争动态，包括：
- 运营商钱包：Orange Money、MTN MoMo、Airtel Money、Moov Money、Vodafone Cash、Ooredoo Money 等
- OTT 支付玩家：Wave、PalmPay、Chipper Cash、Fawry、MFS Africa 等
- 监管动向：BCEAO、各国央行、KYC/AML 政策
- 融资 / 并购 / 合作 / 产品发布

与 Mobile Money 完全无关的文章（纯政治、娱乐、体育）直接跳过，无需说明。

每条文章格式：

【标题】（中文翻译，玩家名称和地名保留英文）
一句话：（15字以内，核心事件）
关键信息：
· 要点1（数字 / 具体事实）
· 要点2
· 要点3（如有）
竞争意义：（2-3句，说明对竞争格局的影响，务必点名具体玩家和市场）

文章内容：
{raw_block}

注意：
1. 输出纯文本 + 基本 Markdown（**粗体**、· 列表），不要 HTML 标签
2. 文章之间用 --- 分隔"""


ARTICLE_PROMPT_AI = """请对以下「AI 工具与应用」章节的文章进行简报整理。

文章分为两类，请按顺序处理：先输出全部「AI热点」，再输出全部「GitHub项目」，中间用 ═══ 单独一行分隔。

▌AI热点（OpenAI / MIT / The Verge / HackerNews 来源）

Hacker News 文章只处理与 AI / LLM / 开发者工具直接相关的，其他直接跳过。

每条格式：
【标题】（中文翻译）
一句话：（15字以内）
关键信息：
· 要点1
· 要点2（如有）
值得关注：（1-2句，说清楚这个进展对实际使用者的影响）

---

▌GitHub项目（GitHub Trending 来源）

每条格式：
【项目名】（保留英文原名）
⭐ Star 数 / 今日新增（内容中有则填，没有则省略此行）
是什么：（一句话，项目核心功能，15字以内）
能做什么：（2-3句，面向使用者而非开发者，说清楚具体使用场景和亮点）

文章内容（每条已标注所属板块）：
{raw_block}

注意：
1. 输出纯文本 + 基本 Markdown，不要 HTML 标签
2. 同一板块内文章之间用 --- 分隔"""


ARTICLE_PROMPT_PSYCH = """请对以下「心理学 · 依恋与人格」章节的文章进行深度整理。

每篇文章按以下五个层次展开：

【标题】（原文标题中文翻译）
一句话：（15字以内，核心发现）
关键信息：
· 研究发现1（具体数据或结论）
· 研究发现2
· 研究发现3（如有）
背景理论：（从零开始解释核心心理学概念，不假设读者有专业背景，200字左右）
核心展开：（机制分析，不只是结论，解释为什么会这样，150-200字）
延伸维度：（一个额外视角：神经科学 / 文化差异 / 与其他理论的联结，100字）
延伸思考：
· 表层：（一个直接的自我观察问题）
· 中层：（一个需要反思的问题）
· 深层：（一个触及核心的问题）

文章内容：
{raw_block}

注意：
1. 与依恋、人格、亲密关系完全无关的文章（如减肥、职场压力、育儿技巧等）直接跳过
2. 内容太短或质量差的文章直接跳过
3. 输出纯文本 + 基本 Markdown，不要 HTML 标签
4. 文章之间用 --- 分隔"""
