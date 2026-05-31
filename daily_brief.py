"""
Kindle Daily Brief — 完整版
四章节：Mobile Money / AI业界 / AI on GitHub / 心理学
生成带封面的EPUB → 发送到Kindle邮箱
"""

import os, re, html, smtplib, textwrap, json
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import requests
import feedparser
from PIL import Image, ImageDraw, ImageFont
from config import CHAPTERS, SYSTEM_PROMPT, ARTICLE_PROMPT_MM, ARTICLE_PROMPT_AI, ARTICLE_PROMPT_PSYCH, DEEPSEEK_MODEL

# ── 环境变量 ──────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
SENDER_EMAIL     = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD  = os.environ["SENDER_PASSWORD"]
KINDLE_EMAIL     = os.environ["KINDLE_EMAIL"]

TODAY     = datetime.now()
DATE_STR  = TODAY.strftime("%Y年%m月%d日")
DATE_FILE = TODAY.strftime("%Y%m%d")
WEEKDAY   = ["周一","周二","周三","周四","周五","周六","周日"][TODAY.weekday()]


# ═══════════════════════════════════════════════════════════════
# 1. 抓取文章
# ═══════════════════════════════════════════════════════════════

def clean_html(raw: str) -> str:
    """去除HTML标签，还原实体"""
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = html.unescape(raw)
    return re.sub(r'\s+', ' ', raw).strip()


def fetch_full_text(url: str) -> str:
    """用 jina reader 抓全文，失败则返回空字符串"""
    try:
        r = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.text[:3000]
    except Exception:
        pass
    return ""


def fetch_chapter(chapter_cfg: dict) -> list[dict]:
    """抓取单个章节的所有文章"""
    articles    = []
    max_per_feed = chapter_cfg.get("max_per_feed", 4)
    use_fulltext = chapter_cfg.get("use_fulltext", False)
    keywords     = chapter_cfg.get("keywords", [])   # 心理学章节关键词过滤

    for feed_cfg in chapter_cfg["feeds"]:
        subsection = feed_cfg.get("subsection", "")
        try:
            feed = feedparser.parse(feed_cfg["url"])
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break
                title   = clean_html(entry.title)[:150]
                summary = clean_html(getattr(entry, "summary", "") or "")
                link    = getattr(entry, "link", "")

                # 关键词过滤：仅保留匹配的文章
                if keywords:
                    haystack = (title + " " + summary).lower()
                    if not any(kw.lower() in haystack for kw in keywords):
                        continue

                # 心理学章节尝试抓全文
                fulltext = ""
                if use_fulltext and link:
                    fulltext = fetch_full_text(link)

                text = fulltext if fulltext else summary
                if not text:
                    continue

                articles.append({
                    "source":     feed_cfg["name"],
                    "title":      title,
                    "link":       link,
                    "text":       text[:3500],
                    "chapter":    chapter_cfg["title"],
                    "subsection": subsection,
                })
                count += 1

            print(f"  ✓ {feed_cfg['name']}: {count} 条")
        except Exception as e:
            print(f"  ✗ {feed_cfg['name']}: {e}")

    return articles


def fetch_all() -> dict[str, list[dict]]:
    """抓取所有章节，返回 {章节标题: [文章列表]}"""
    result = {}
    total  = 0
    for ch in CHAPTERS:
        print(f"\n[抓取] {ch['title']}")
        articles = fetch_chapter(ch)
        result[ch["title"]] = articles
        total += len(articles)
    print(f"\n[INFO] 共抓取 {total} 条文章")
    return result


# ═══════════════════════════════════════════════════════════════
# 2. DeepSeek 总结
# ═══════════════════════════════════════════════════════════════

def call_deepseek(prompt: str, max_tokens: int = 3000) -> str:
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type":  "application/json",
        },
        json={
            "model":       DEEPSEEK_MODEL,
            "messages":    [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens":  max_tokens,
            "temperature": 0.65,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def summarize_chapter(chapter_cfg: dict, articles: list[dict]) -> str:
    """对单章节文章做总结，返回 Markdown 内容"""
    chapter_title = chapter_cfg["title"]
    chapter_type  = chapter_cfg.get("chapter_type", "regular")

    if not articles:
        return "*今日暂无相关内容。*"

    # ── 构建 raw_block ──────────────────────────────────────
    if chapter_type == "ai":
        # AI 章节按子板块分组，方便 DeepSeek 区分处理
        sections: dict[str, list] = {}
        for a in articles:
            ss = a.get("subsection") or "其他"
            sections.setdefault(ss, []).append(a)
        raw_block = ""
        idx = 1
        for ss_name, ss_articles in sections.items():
            raw_block += f"\n【{ss_name}】\n"
            for a in ss_articles:
                raw_block += (
                    f"\n[{idx}] 来源：{a['source']}\n"
                    f"标题：{a['title']}\n"
                    f"链接：{a['link']}\n"
                    f"内容：{a['text']}\n"
                )
                idx += 1
    else:
        raw_block = ""
        for i, a in enumerate(articles, 1):
            raw_block += (
                f"\n[{i}] 来源：{a['source']}\n"
                f"标题：{a['title']}\n"
                f"链接：{a['link']}\n"
                f"内容：{a['text']}\n"
            )

    # ── 选择 Prompt ─────────────────────────────────────────
    if chapter_type == "mm":
        prompt = ARTICLE_PROMPT_MM.format(raw_block=raw_block)
    elif chapter_type == "ai":
        prompt = ARTICLE_PROMPT_AI.format(raw_block=raw_block)
    elif chapter_type == "psych":
        prompt = ARTICLE_PROMPT_PSYCH.format(chapter_title=chapter_title, raw_block=raw_block)
    else:
        prompt = f"请总结以下文章内容：\n{raw_block}"

    max_tokens = 4000 if chapter_type == "psych" else 2800
    return call_deepseek(prompt, max_tokens=max_tokens)


def generate_insight(all_summaries: dict[str, str]) -> str:
    """跨章节今日洞察"""
    combined = "\n\n".join(
        f"=== {title} ===\n{content[:800]}"
        for title, content in all_summaries.items()
    )
    prompt = f"""根据以下今日简报四个章节的内容，写一段「今日洞察」。

要求：
- 跨章节找一个共同的底层逻辑或趋势信号
- 不要简单重复各章节内容，要有真正的联结和洞察
- 150字以内，有观点，不说废话
- 用纯文本，不用Markdown或HTML标签

今日内容摘要：
{combined}"""
    return call_deepseek(prompt, max_tokens=300)


# ═══════════════════════════════════════════════════════════════
# 3. 生成封面图
# ═══════════════════════════════════════════════════════════════

def make_cover(chapter_names: list[str], article_count: int) -> bytes:
    """生成黑底白字封面，返回PNG bytes"""
    W, H = 1072, 1448   # Kindle Paperwhite 分辨率
    img  = Image.new("L", (W, H), color=10)   # 近黑背景
    draw = ImageDraw.Draw(img)

    # 优先加载支持中文的 CJK 字体，回退到拉丁字体
    def load_font(size):
        for path in [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",       # Ubuntu: fonts-wqy-zenhei
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
        ]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    font_title  = load_font(90)
    font_sub    = load_font(42)
    font_date   = load_font(38)
    font_ch     = load_font(34)
    font_small  = load_font(26)

    # 顶部细线
    draw.line([(80, 120), (W - 80, 120)], fill=200, width=2)

    # 标签
    draw.text((80, 80), "DAILY BRIEF", font=font_small, fill=120)

    # 主标题
    draw.text((80, 160), "每日简报", font=font_title, fill=240)

    # 日期
    draw.text((80, 310), f"{DATE_STR}  {WEEKDAY}", font=font_date, fill=160)

    # 分隔线
    draw.line([(80, 390), (W - 80, 390)], fill=60, width=1)

    # 章节列表
    y = 440
    for i, name in enumerate(chapter_names, 1):
        draw.text((80, y), f"0{i}  {name}", font=font_ch, fill=180)
        y += 70

    # 底部分隔线
    draw.line([(80, H - 180), (W - 80, H - 180)], fill=60, width=1)

    # 底部统计
    draw.text((80, H - 150), f"{article_count} 篇文章", font=font_small, fill=100)
    draw.text((80, H - 110), "Powered by DeepSeek", font=font_small, fill=80)

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════
# 4. 章节 HTML 模板
# ═══════════════════════════════════════════════════════════════

CHAPTER_CSS = """
body {
  font-family: Georgia, serif;
  font-size: 1em;
  line-height: 1.85;
  margin: 0;
  padding: 1em 1.4em;
  color: #000;
  background: #fff;
}
/* ── 章节标题 ── */
h1.chapter-title {
  font-size: 1.15em;
  font-weight: bold;
  letter-spacing: 0.04em;
  border-bottom: 3px solid #000;
  padding-bottom: 0.45em;
  margin: 0 0 1.8em 0;
}
h2 { font-size: 1em; font-weight: bold; margin: 1em 0 0.3em 0; }
h3 { font-size: 0.95em; font-weight: bold; margin: 0.8em 0 0.2em 0; }
/* ── 文章卡片 ── */
.article {
  margin: 0 0 0.4em 0;
  padding: 0.8em 1em;
  border: 1px solid #bbb;
}
/* ── 文章标题行 ── */
.art-title {
  font-size: 1.04em;
  font-weight: bold;
  line-height: 1.5;
  padding-left: 0.6em;
  border-left: 4px solid #000;
  margin-bottom: 0.55em;
}
.art-note {
  font-weight: normal;
  font-size: 0.84em;
}
/* ── 分节标签（一句话 / 关键信息 / 竞争意义 …） ── */
.section-label {
  font-size: 0.6em;
  font-weight: bold;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #555;
  border-bottom: 1px solid #ddd;
  margin: 0.85em 0 0.2em 0;
  padding-bottom: 0.1em;
}
/* ── 一句话 ── */
.one-line-block {
  font-size: 0.9em;
  font-style: italic;
  margin: 0 0 0.2em 0;
}
/* ── 正文内容 ── */
.section-content {
  font-size: 0.88em;
  line-height: 1.82;
  margin: 0.15em 0;
}
/* ── GitHub star 行 ── */
.star-line {
  font-size: 0.78em;
  margin: 0.2em 0 0.4em 0;
}
/* ── 列表 ── */
ul { margin: 0.2em 0 0.3em 0; padding-left: 1.3em; }
li { font-size: 0.86em; line-height: 1.75; margin: 0.1em 0; }
p  { font-size: 0.9em; line-height: 1.85; margin: 0.25em 0; }
/* ── 文章间虚线分隔 ── */
hr.art-sep {
  border: none;
  border-top: 1px dashed #aaa;
  margin: 1.6em 0;
}
/* ── AI章节子板块粗分隔 ── */
hr.section-sep {
  border: none;
  border-top: 2px solid #000;
  margin: 2.4em 0;
}
"""

COVER_CSS = """
body {
  font-family: Georgia, serif;
  background: #0a0a0a;
  color: #e8e4dc;
  margin: 0;
  padding: 2em 1.5em;
  min-height: 90vh;
}
.cover-label { font-size: 0.65em; letter-spacing: 0.2em; text-transform: uppercase; color: #666; margin-bottom: 1em; }
.cover-title { font-size: 2.5em; font-weight: bold; line-height: 1.2; margin-bottom: 0.3em; }
.cover-date  { font-style: italic; color: #888; margin-bottom: 2em; }
.toc { list-style: none; padding: 0; border-top: 1px solid #333; padding-top: 1.2em; }
.toc li { font-size: 0.85em; padding: 0.3em 0; color: #ccc; }
.toc li .num { color: #555; margin-right: 0.8em; font-size: 0.75em; }
.stats { margin-top: 2em; border-top: 1px solid #222; padding-top: 0.8em; font-size: 0.7em; color: #555; }
"""

INSIGHT_CSS = """
body {
  font-family: Georgia, "Noto Serif SC", serif;
  background: #0a0a0a;
  color: #e8e4dc;
  margin: 0;
  padding: 2em 1.5em;
}
h1 { font-size: 1em; letter-spacing: 0.15em; text-transform: uppercase; color: #666; margin-bottom: 1.5em; }
.insight-text { font-size: 1em; line-height: 1.95; }
.date { margin-top: 2em; font-size: 0.7em; color: #444; }
"""


def make_cover_html(chapter_names: list[str], article_count: int) -> str:
    toc_items = "".join(
        f'<li><span class="num">0{i}</span>{name}</li>'
        for i, name in enumerate(chapter_names, 1)
    )
    return f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><meta charset="utf-8"/><title>封面</title>
<style>{COVER_CSS}</style></head>
<body>
<div class="cover-label">Daily Brief · DeepSeek</div>
<div class="cover-title">每日简报</div>
<div class="cover-date">{DATE_STR}　{WEEKDAY}</div>
<ul class="toc">{toc_items}</ul>
<div class="stats">{article_count} 篇文章　·　预计阅读 35 分钟</div>
</body></html>"""


def make_chapter_html(chapter_title: str, content_html: str, chapter_num: int) -> str:
    """把DeepSeek返回的内容包装进完整HTML页面"""
    # DeepSeek返回的是Markdown，需要基础转换
    content = md_to_html(content_html)
    return f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><meta charset="utf-8"/><title>{chapter_title}</title>
<style>{CHAPTER_CSS}</style></head>
<body>
<h1 class="chapter-title">0{chapter_num}　{chapter_title}</h1>
{content}
</body></html>"""


def make_insight_html(insight_text: str) -> str:
    paras = "".join(f"<p>{p}</p>" for p in insight_text.split("\n") if p.strip())
    return f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><meta charset="utf-8"/><title>今日洞察</title>
<style>{INSIGHT_CSS}</style></head>
<body>
<h1>💡 今日洞察</h1>
<div class="insight-text">{paras}</div>
<div class="date">{DATE_STR}　·　每日简报</div>
</body></html>"""


# ── 结构化 Markdown 解析器 ────────────────────────────────────

# 所有需要渲染为"分节标签"的关键词
_LABELS = frozenset({
    "一句话", "关键信息", "竞争意义", "值得关注",
    "是什么", "能做什么",
    "背景理论", "核心展开", "延伸维度", "延伸思考",
    "表层", "中层", "深层",
})
_LABEL_RE = re.compile(
    r'^(' + '|'.join(re.escape(l) for l in _LABELS) + r')[：:]\s*(.*)',
)


def _inline(t: str) -> str:
    """行内 Markdown → HTML（粗体、斜体）"""
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*',     r'<em>\1</em>',         t)
    return t


def md_to_html(text: str) -> str:
    """结构感知解析器：把 DeepSeek 输出转为分层 HTML。

    识别：
      【标题】     → .art-title（同时开启 .article 卡片）
      一句话：     → .section-label + .one-line-block
      关键信息 等  → .section-label + .section-content / <ul>
      ⭐ …        → .star-line
      · - * 列表  → <ul><li>
      ---          → <hr class="art-sep">（同时关闭当前卡片）
      ═══          → <hr class="section-sep">（AI 子板块分隔）
    """
    lines  = text.split('\n')
    out    = []
    in_art = False   # 是否在 .article 卡片内
    in_ul  = False   # 是否在 <ul> 内

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append('</ul>')
            in_ul = False

    def close_art():
        nonlocal in_art
        if in_art:
            close_ul()
            out.append('</div>')
            in_art = False

    def open_art():
        nonlocal in_art
        out.append('<div class="article">')
        in_art = True

    for line in lines:
        s = line.strip()

        # 空行
        if not s:
            close_ul()
            continue

        # 文章分隔符 ---
        if re.match(r'^-{3,}$', s):
            close_art()
            out.append('<hr class="art-sep"/>')
            continue

        # AI 子板块分隔 ═══
        if re.match(r'^═{3,}$', s):
            close_art()
            out.append('<hr class="section-sep"/>')
            continue

        # 文章标题 【...】
        m = re.match(r'^【(.+?)】(.*)', s)
        if m:
            close_art()
            open_art()
            title = _inline(m.group(1))
            note  = _inline(m.group(2).strip())
            inner = f'【{title}】'
            if note:
                inner += f'<span class="art-note"> {note}</span>'
            out.append(f'<div class="art-title">{inner}</div>')
            continue

        # ⭐ star 行
        if s.startswith('⭐'):
            close_ul()
            out.append(f'<div class="star-line">{_inline(s)}</div>')
            continue

        # 分节标签：一句话：xxx / 关键信息：
        lm = _LABEL_RE.match(s)
        if lm:
            close_ul()
            label   = lm.group(1)
            content = lm.group(2).strip()
            out.append(f'<div class="section-label">{label}</div>')
            if content:
                cls = "one-line-block" if label == "一句话" else "section-content"
                out.append(f'<div class="{cls}">{_inline(content)}</div>')
            continue

        # 项目符号 · - *
        if re.match(r'^[·\-\*] ', s):
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{_inline(s[2:])}</li>')
            continue

        close_ul()

        # Markdown 标题
        if s.startswith('### '):
            out.append(f'<h3>{_inline(s[4:])}</h3>')
            continue
        if s.startswith('## '):
            out.append(f'<h2>{_inline(s[3:])}</h2>')
            continue

        # 默认段落
        out.append(f'<p>{_inline(s)}</p>')

    close_art()
    return '\n'.join(out)


# ═══════════════════════════════════════════════════════════════
# 5. 组装 EPUB
# ═══════════════════════════════════════════════════════════════

def build_epub(summaries: dict[str, str], insight: str, article_count: int) -> bytes:
    """
    手工用zipfile打包EPUB3，绕开ebooklib的lxml nav解析bug。
    EPUB结构：
      mimetype
      META-INF/container.xml
      EPUB/content.opf
      EPUB/nav.xhtml
      EPUB/toc.ncx
      EPUB/style.css
      EPUB/images/cover.png
      EPUB/cover.xhtml
      EPUB/chapter_01.xhtml … chapter_04.xhtml
      EPUB/insight.xhtml
    """
    import io, zipfile

    chapter_names = list(summaries.keys())
    cover_png     = make_cover(chapter_names, article_count)

    # 收集所有页面 (filename, title, html_content)
    pages = []
    pages.append(("cover.xhtml", "封面", make_cover_html(chapter_names, article_count)))
    for i, (ch_title, ch_md) in enumerate(summaries.items(), 1):
        pages.append((f"chapter_{i:02d}.xhtml", ch_title, make_chapter_html(ch_title, ch_md, i)))
    pages.append(("insight.xhtml", "今日洞察", make_insight_html(insight)))

    uid = f"kindle-brief-{DATE_FILE}"

    # ── content.opf ──
    manifest_items = '\n    '.join(
        f'<item id="p{i}" href="{fn}" media-type="application/xhtml+xml"/>'
        for i, (fn, _, __) in enumerate(pages)
    )
    spine_items = '\n    '.join(
        f'<itemref idref="p{i}"/>'
        for i in range(len(pages))
    )
    opf = f"""<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">{uid}</dc:identifier>
    <dc:title>每日简报 · {DATE_STR}</dc:title>
    <dc:language>zh</dc:language>
    <dc:creator>Daily Brief Bot</dc:creator>
    <meta name="cover" content="cover-img"/>
  </metadata>
  <manifest>
    <item id="ncx"        href="toc.ncx"       media-type="application/x-dtbncx+xml"/>
    <item id="nav"        href="nav.xhtml"      media-type="application/xhtml+xml" properties="nav"/>
    <item id="css"        href="style.css"      media-type="text/css"/>
    <item id="cover-img"  href="images/cover.png" media-type="image/png" properties="cover-image"/>
    {manifest_items}
  </manifest>
  <spine toc="ncx">
    {spine_items}
  </spine>
</package>"""

    # ── nav.xhtml ──
    nav_items = '\n      '.join(
        f'<li><a href="{fn}">{title}</a></li>'
        for fn, title, _ in pages
    )
    nav_xhtml = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><meta charset="utf-8"/><title>目录</title></head>
<body>
<nav epub:type="toc" id="toc">
  <h1>每日简报 · {DATE_STR}</h1>
  <ol>
      {nav_items}
  </ol>
</nav>
</body>
</html>"""

    # ── toc.ncx ──
    ncx_points = '\n  '.join(
        f'''<navPoint id="np{i}" playOrder="{i+1}">
    <navLabel><text>{title}</text></navLabel>
    <content src="{fn}"/>
  </navPoint>'''
        for i, (fn, title, _) in enumerate(pages)
    )
    toc_ncx = f"""<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{uid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>每日简报 · {DATE_STR}</text></docTitle>
  <navMap>
  {ncx_points}
  </navMap>
</ncx>"""

    # ── 打包 ──
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # mimetype必须是第一个文件且不压缩
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip",
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", """<?xml version='1.0' encoding='utf-8'?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
        zf.writestr("EPUB/content.opf",  opf)
        zf.writestr("EPUB/nav.xhtml",    nav_xhtml)
        zf.writestr("EPUB/toc.ncx",      toc_ncx)
        zf.writestr("EPUB/style.css",    CHAPTER_CSS)
        zf.writestr("EPUB/images/cover.png", cover_png)
        for fn, _, content in pages:
            zf.writestr(f"EPUB/{fn}", content)

    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════
# 6. 发送到 Kindle
# ═══════════════════════════════════════════════════════════════

def send_to_kindle(epub_bytes: bytes):
    filename = f"daily_brief_{DATE_FILE}.epub"

    msg              = MIMEMultipart()
    msg["From"]      = SENDER_EMAIL
    msg["To"]        = KINDLE_EMAIL
    msg["Subject"]   = "convert"   # Amazon要求

    part = MIMEBase("application", "epub+zip")
    part.set_payload(epub_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

    print(f"[DONE] 已发送 {filename} 到 {KINDLE_EMAIL}")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"[START] {datetime.now().isoformat()}")

    # 1. 抓取
    all_articles = fetch_all()
    total_count  = sum(len(v) for v in all_articles.values())
    if total_count == 0:
        print("[ERROR] 未抓到任何文章，退出")
        return

    # 2. 逐章总结
    summaries = {}
    for ch in CHAPTERS:
        title    = ch["title"]
        articles = all_articles.get(title, [])
        print(f"\n[总结] {title} ({len(articles)} 条)...")
        summaries[title] = summarize_chapter(ch, articles)

    # 3. 跨章洞察
    print("\n[洞察] 生成今日洞察...")
    insight = generate_insight(summaries)

    # 4. 打包 EPUB
    print("\n[EPUB] 组装文件...")
    epub_bytes = build_epub(summaries, insight, total_count)

    # 5. 发送
    print("[发送] 推送到Kindle...")
    send_to_kindle(epub_bytes)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
