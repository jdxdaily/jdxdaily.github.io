"""Generate sitemap.xml from the static files on disk.

Discovers:
- Top-level pages   (index, news, stocks, archive, about)
- Dated news pages  (news/YYYY-MM-DD.html)
- Briefing editions (briefings/YYYY-MM-DD/{concise,standard,in-depth}.html)

Skips:
- prototypes/    (design explorations, not for search)
- Anything starting with a dot
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import html
import sys

SITE_URL = "https://jdxdaily.github.io"
ROOT = Path(__file__).resolve().parents[1]


def url_for(rel: Path) -> str:
    """Convert a repo-relative Path to a canonical URL."""
    # Index page should just be the root URL
    if rel.name == "index.html" and rel.parent == Path("."):
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{rel.as_posix()}"


def lastmod(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return ts.strftime("%Y-%m-%d")


def discover() -> list[tuple[Path, str, float]]:
    """Returns (path, change-freq, priority) for each indexable page."""
    pages: list[tuple[Path, str, float]] = []

    # Top-level pages
    for name in ("index.html", "news.html", "stocks.html", "archive.html", "about.html"):
        p = ROOT / name
        if p.exists():
            pages.append((p, "daily" if name in {"index.html", "news.html"} else "weekly", 1.0 if name == "index.html" else 0.8))

    # Dated news pages
    news_dir = ROOT / "news"
    if news_dir.exists():
        for p in sorted(news_dir.glob("*.html")):
            pages.append((p, "never", 0.6))

    # Briefings
    briefings_dir = ROOT / "briefings"
    if briefings_dir.exists():
        for day_dir in sorted(briefings_dir.iterdir()):
            if not day_dir.is_dir() or day_dir.name.startswith("."):
                continue
            for edition in ("concise.html", "standard.html", "in-depth.html"):
                p = day_dir / edition
                if p.exists():
                    pages.append((p, "never", 0.7))

    return pages


def build_xml(pages: list[tuple[Path, str, float]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, changefreq, priority in pages:
        rel = path.relative_to(ROOT)
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(url_for(rel))}</loc>")
        lines.append(f"    <lastmod>{lastmod(path)}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority:.1f}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> None:
    pages = discover()
    xml = build_xml(pages)
    out = ROOT / "sitemap.xml"
    out.write_text(xml, encoding="utf-8")
    print(f"  Wrote sitemap.xml — {len(pages)} URL(s)", flush=True)


if __name__ == "__main__":
    main()
