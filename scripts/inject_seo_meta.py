"""Retrofit meta tags + JSON-LD onto existing dated news and briefing pages.

For each file:
- Extracts the page title and headline (h1)
- Builds full meta tag block (description, OG, Twitter, canonical)
- Builds JSON-LD (NewsArticle for briefings, WebPage for news pulse)
- Injects both before </head>
- Idempotent (skips if og:url already present)
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import html as h
import json
import re
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
SITE = "https://jdxdaily.github.io"
OG_IMG = f"{SITE}/assets/og-default.png"


def extract(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else None


def text_only(html_str: str) -> str:
    # crude tag stripper for descriptions
    return re.sub(r"<[^>]+>", "", html_str).strip()


def make_meta(url: str, title: str, desc: str, og_type: str) -> str:
    desc = h.escape(desc)
    title_esc = h.escape(title)
    return (
        f'<meta name="description" content="{desc}">\n'
        f'<link rel="canonical" href="{url}">\n'
        f'<meta property="og:type" content="{og_type}">\n'
        f'<meta property="og:site_name" content="JDX">\n'
        f'<meta property="og:title" content="{title_esc}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta property="og:image" content="{OG_IMG}">\n'
        f'<meta property="og:image:width" content="1200">\n'
        f'<meta property="og:image:height" content="630">\n'
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{title_esc}">\n'
        f'<meta name="twitter:description" content="{desc}">\n'
        f'<meta name="twitter:image" content="{OG_IMG}">'
    )


def make_ld_article(headline: str, date_str: str, url: str, desc: str) -> str:
    obj = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": headline,
        "description": desc,
        "datePublished": f"{date_str}T09:00:00+08:00",
        "dateModified":  f"{date_str}T09:00:00+08:00",
        "author":    {"@type": "Organization", "name": "JDX"},
        "publisher": {
            "@type": "Organization",
            "name": "JDX",
            "logo": {"@type": "ImageObject", "url": OG_IMG},
        },
        "image": OG_IMG,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def inject(path: Path, meta_html: str, ld_html: str | None) -> bool:
    text = path.read_text(encoding="utf-8")
    if "og:url" in text:
        return False
    payload = meta_html + ("\n" + ld_html if ld_html else "") + "\n"
    text = text.replace("</head>", payload + "</head>", 1)
    path.write_text(text, encoding="utf-8")
    return True


def process_briefing(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    # /briefings/YYYY-MM-DD/edition.html
    date_str = path.parent.name
    edition = path.stem
    url = f"{SITE}/briefings/{date_str}/{edition}.html"

    title_tag = extract(text, r"<title>([^<]+)</title>") or f"{edition.title()} — JDX Briefing"
    h1 = extract(text, r'<h1[^>]*>(.+?)</h1>') or title_tag
    h1 = text_only(h1)
    deck = extract(text, r'<p class="deck">(.+?)</p>')
    desc = text_only(deck) if deck else (
        f"{edition.title()} edition of the JDX US market briefing for {date_str}."
    )
    desc = desc[:200].rstrip()

    meta = make_meta(url, title_tag, desc, "article")
    ld   = make_ld_article(h1, date_str, url, desc)
    return inject(path, meta, ld)


def process_news(path: Path) -> bool:
    # /news/YYYY-MM-DD.html
    date_str = path.stem
    url = f"{SITE}/news/{date_str}.html"
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        display = d.strftime("%-d %B %Y")
    except ValueError:
        display = date_str
    title = f"Market Pulse — JDX · {display}"
    desc = (
        f"Market Pulse for {display} — the most market-moving stories of the day, "
        "impact-rated and filtered for US equities."
    )
    meta = make_meta(url, title, desc, "website")
    return inject(path, meta, None)


def main() -> None:
    n = 0
    for p in sorted((ROOT / "briefings").glob("*/*.html")):
        if process_briefing(p):
            print(f"  {p.relative_to(ROOT)}")
            n += 1
    for p in sorted((ROOT / "news").glob("*.html")):
        if process_news(p):
            print(f"  {p.relative_to(ROOT)}")
            n += 1
    print(f"\nDone. {n} file(s) updated.")


if __name__ == "__main__":
    main()
