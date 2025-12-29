#!/usr/bin/env python3
"""
Scrape Noveum docs into NoveumDocsData/processed/docs.json.

This is intentionally an independent script so you can refresh docs whenever you want.

Crawler behavior:
- starts from https://noveum.ai/en/docs (default)
- stays on the same host
- follows links under allowed prefixes (default: /docs and /en/docs)
- strips fragments/query params to reduce duplicates
- skips common asset extensions
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@dataclass
class Page:
    url: str
    title: str
    text: str


SKIP_EXT = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".css",
    ".js",
    ".map",
    ".pdf",
    ".zip",
)


def canonicalize(url: str) -> str:
    p = urlparse(url)
    p = p._replace(fragment="", query="")
    return urlunparse(p)


def extract_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"

    # Drop script/style/nav/footer-like noise
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text("\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


def discover_links(base_url: str, html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        out.add(canonicalize(urljoin(base_url, href)))
    return out


def is_allowed(url: str, host: str, allowed_prefixes: List[str]) -> bool:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    if p.netloc != host:
        return False
    if any(p.path.lower().endswith(ext) for ext in SKIP_EXT):
        return False
    return any(p.path.startswith(prefix) for prefix in allowed_prefixes)


def chunk_text(title: str, url: str, text: str, max_chars: int = 2500, overlap: int = 200):
    chunks = []
    start = 0
    cid = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(
                {
                    "chunk_id": f"{url}#{cid}",
                    "url": url,
                    "title": title,
                    "section_path": "",
                    "content": chunk,
                    "content_hash": f"scrape-{hash(chunk)}",
                }
            )
            cid += 1
        start = end - overlap
        if start < 0:
            start = 0
        if end == len(text):
            break
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Noveum docs into docs.json")
    parser.add_argument("--start-url", default="https://noveum.ai/en/docs")
    parser.add_argument(
        "--out",
        default=str(repo_root() / "NoveumDocsData" / "processed" / "docs.json"),
        help="Output JSON path",
    )
    parser.add_argument(
        "--allowed-prefix",
        action="append",
        default=None,
        help="Allowed path prefix (repeatable). Default: /docs and /en/docs",
    )
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    start_url = canonicalize(args.start_url)
    host = urlparse(start_url).netloc
    allowed_prefixes = args.allowed_prefix or ["/docs", "/en/docs"]

    seen: Set[str] = set()
    queue: List[str] = [start_url]
    pages: List[Page] = []

    session = requests.Session()
    session.headers.update({"User-Agent": "NovaBotDocsScraper/0.2"})

    while queue and len(pages) < args.max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = session.get(url, timeout=args.timeout)
        except Exception:
            continue
        if resp.status_code != 200:
            continue

        title, text = extract_text(resp.text)
        if text:
            pages.append(Page(url=url, title=title, text=text))

        for link in discover_links(url, resp.text):
            if is_allowed(link, host, allowed_prefixes) and link not in seen:
                queue.append(link)

        time.sleep(args.sleep)

    chunks = []
    for p in pages:
        chunks.extend(chunk_text(p.title, p.url, p.text))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    print(f"✅ Scraped {len(pages)} pages into {len(chunks)} chunks")
    print(f"✅ Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


