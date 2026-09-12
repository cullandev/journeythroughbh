#!/usr/bin/env python3
"""
Stitch the shared header/footer around each page in src/pages/ and write
finished HTML into public/. Output is committed, so deploying needs no build.

    python scripts/build.py          # regenerate public/*.html and sitemap.xml
    python scripts/build.py --check  # exit 1 if public/ is out of date

Page source format (src/pages/name.html):

    title: About
    description: One sentence for search engines.
    path: /about
    scripts: faq        (optional, comma-separated: nav is always included)
    noindex: true       (optional)
    ---
    <body markup>
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "pages"
OUT = ROOT / "public"
SITE = "https://journeythroughbh.org"
NAME = "Journey Through Behavioral Health"

NAV = [
    ("/", "Home"),
    ("/about", "About"),
    ("/services", "Services"),
    ("/what-to-expect", "What to expect"),
    ("/fees", "Fees &amp; insurance"),
    ("/faq", "FAQ"),
]

LOGO = (
    '<img class="mark" src="/images/logo-mark-small.png" width="112" height="105" alt="">'
    f'<img class="wordmark" src="/images/wordmark.webp" width="720" height="115" alt="{NAME}">'
)


def head(meta):
    canonical = SITE + (meta["path"] if meta["path"] != "/" else "/")
    title = NAME if meta["path"] == "/" else f'{meta["title"]} · {NAME}'
    robots = '<meta name="robots" content="noindex">\n' if meta.get("noindex") == "true" else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{meta['description']}">
<link rel="canonical" href="{canonical}">
{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta['description']}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/images/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="theme-color" content="#f7f3ea">
<link rel="icon" href="/images/icon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/images/icon-180.png">
<link rel="stylesheet" href="/css/site.css">
</head>"""


def header(current):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    cur = ' aria-current="page"' if current == "/contact" else ""
    items.append(f'<li class="nav-cta"><a href="/contact"{cur}>Contact</a></li>')
    return f"""<body>
<a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/">{LOGO}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
    <nav class="site-nav" id="site-nav" aria-label="Main">
      <ul>
        {chr(10).join(items)}
      </ul>
    </nav>
  </div>
</header>
<main id="main" tabindex="-1">"""


def footer(scripts):
    year = date.today().year
    tags = "".join(f'\n<script src="/js/{s}.js" defer></script>' for s in ["nav"] + scripts)
    return f"""</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="crisis" role="note">
      <strong>This site is not for emergencies.</strong>
      If you are in crisis, call or text <a href="tel:988">988</a> (Suicide &amp; Crisis Lifeline) or call 911.
      <a href="/crisis">More crisis resources</a>
    </div>
    <div>
      <h2>Contact</h2>
      <ul>
        <li><a href="/contact">Book a free 15-minute consultation</a></li>
        <li><mark class="todo">TODO: phone</mark></li>
        <li><mark class="todo">TODO: public email</mark></li>
        <li>Online across Connecticut &middot; in person in <mark class="todo">TODO: town</mark></li>
      </ul>
    </div>
    <div>
      <h2>Practice</h2>
      <ul>
        <li><a href="/about">About</a></li>
        <li><a href="/fees">Fees &amp; insurance</a></li>
        <li><a href="/privacy">Privacy policy</a></li>
        <li><a href="/notice-of-privacy-practices">Notice of Privacy Practices</a></li>
        <li><a href="/crisis">Crisis resources</a></li>
      </ul>
    </div>
    <p class="fine">&copy; {year} {NAME}.
      <mark class="todo">TODO: Clinician name</mark>, LCSW &middot;
      Licensed Clinical Social Worker, Connecticut, license <mark class="todo">TODO: number</mark>.
      No cookies, no trackers.</p>
  </div>
</footer>{tags}
</body>
</html>
"""


def parse(text):
    front, _, body = text.partition("\n---\n")
    meta = {}
    for line in front.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    for required in ("title", "description", "path"):
        if required not in meta:
            raise SystemExit(f"missing '{required}' in page front matter")
    return meta, body.strip() + "\n"


def render(src):
    meta, body = parse(src.read_text(encoding="utf-8"))
    scripts = [s.strip() for s in meta.get("scripts", "").split(",") if s.strip()]
    return meta, head(meta) + "\n" + header(meta["path"]) + "\n" + body + footer(scripts)


def sitemap(pages):
    today = date.today().isoformat()
    urls = "".join(
        f"  <url><loc>{SITE}{p if p != '/' else '/'}</loc><lastmod>{today}</lastmod></url>\n"
        for p in pages
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'


def main(check=False):
    stale = []
    indexed = []
    for src in sorted(SRC.glob("*.html")):
        meta, html = render(src)
        out = OUT / ("index.html" if meta["path"] == "/" else src.name)
        if meta.get("noindex") != "true" and src.name != "404.html":
            indexed.append(meta["path"])
        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != html:
                stale.append(out.name)
        else:
            out.write_text(html, encoding="utf-8", newline="\n")
            print(f"wrote {out.relative_to(ROOT)}")
    sm = sitemap(indexed)
    sm_path = OUT / "sitemap.xml"
    if check:
        existing = sm_path.read_text(encoding="utf-8") if sm_path.exists() else ""
        # Ignore lastmod differences when checking.
        strip = lambda s: re.sub(r"<lastmod>.*?</lastmod>", "", s)
        if strip(existing) != strip(sm):
            stale.append("sitemap.xml")
        if stale:
            print("out of date: " + ", ".join(stale))
            sys.exit(1)
        print("public/ is up to date")
    else:
        sm_path.write_text(sm, encoding="utf-8", newline="\n")
        print("wrote public/sitemap.xml")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
