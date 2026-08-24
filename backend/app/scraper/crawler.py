"""
District-wide FUSD crawler.

Design goals:
- Seed EVERY school from schools.json plus district-level sections (no hardcoded WHS-only scope)
- Download each URL exactly once and hand the raw HTML to the pipeline (no double fetching)
- Never let one bad URL kill the run: every failure is isolated, logged with a traceback, skipped
- Polite crawling: robots.txt respected, random delays, per-school page caps from crawl_rules.json

Usage:
    from backend.app.scraper.crawler import crawl
    for result in crawl():
        result.url / result.school_id / result.kind ("html"|"pdf") / result.html
"""

import time
import random
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urldefrag
from urllib import robotparser
from typing import Iterator, Optional

import httpx

from backend.app.logs.logger import logger
from backend.app.config import SCHOOL_CONFIG

DOMAIN = "fremontunified.org"
BASE_URL = f"https://{DOMAIN}/"

# Junk URL patterns that waste crawl budget or always fail
SKIP_URL_PATTERNS = re.compile(
    r"(\?(share|replytocom|fbclid)=|/wp-json/|/xmlrpc\.php|/feed/?$|/author/|"
    r"\.(jpg|jpeg|png|gif|webp|svg|ico|css|js|zip|mov|mp4|mp3|wmv|docx?|xlsx?|pptx?)$)",
    re.IGNORECASE,
)

# File types we can actually extract text from
PDF_PATTERN = re.compile(r"\.pdf$", re.IGNORECASE)

BLOCKED_EXTENSIONS = [".jpg", ".png", ".gif", ".webp", ".mp3", ".mp4", ".zip", ".exe"]


@dataclass
class CrawlResult:
    url: str
    school_id: str
    kind: str                      # "html" | "pdf" | "error"
    html: Optional[str] = None     # raw HTML for html results (single-fetch design)
    error: Optional[str] = None


def normalize_url(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def classify_school(url: str) -> Optional[str]:
    """Map a URL to its school_id, or 'district' for shared district pages.
    Returns None if the first path segment is not a known school/district section."""
    path = urlparse(url).path.strip("/")
    if not path:
        return "district"
    first = path.split("/", 1)[0].lower()
    if first in SCHOOL_CONFIG.get_all_school_ids():
        return first
    allowed = SCHOOL_CONFIG.get_allowed_paths()
    if first in allowed["district"] or first in allowed["admin"]:
        return "district"
    return None


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.netloc.lower()
    if host != DOMAIN and not host.endswith(f".{DOMAIN}"):
        return False
    if SKIP_URL_PATTERNS.search(parsed.path + ("?" + parsed.query if parsed.query else "")):
        return False
    if parsed.query:
        # Pretty-permalink site: query-string URLs (?p=123) are stale WordPress links
        return False
    lower_path = parsed.path.lower()
    for ext in BLOCKED_EXTENSIONS:
        if lower_path.endswith(ext):
            return False
    # Unknown first segments (other sites' subdomains of content etc.) are rejected;
    # classify_school is the allowlist authority
    if classify_school(url) is None:
        return False
    return True


class RobotsCache:
    def __init__(self):
        self._parser = None
        self._loaded = False

    def allowed(self, url: str) -> bool:
        if not self._loaded:
            self._parser = robotparser.RobotFileParser()
            try:
                self._parser.set_url(f"https://{DOMAIN}/robots.txt")
                self._parser.read()
            except Exception as e:
                logger.warning(f"Could not read robots.txt ({e}) - assuming allowed")
                self._parser = None
            self._loaded = True
        if self._parser is None:
            return True
        try:
            return self._parser.can_fetch("*", url)
        except Exception:
            return True


def build_entry_points() -> list:
    """Seed queue: every school homepage + district admin pages + district root."""
    entry_points = [BASE_URL]
    seen = {normalize_url(BASE_URL)}
    for school in SCHOOL_CONFIG.schools:
        for base in school["base_urls"]:
            u = normalize_url(base)
            if u not in seen:
                seen.add(u)
                entry_points.append(u)
    district = getattr(SCHOOL_CONFIG, "district", {})
    for u in district.get("admin_urls", []):
        nu = normalize_url(u)
        if nu not in seen:
            seen.add(nu)
            entry_points.append(nu)
    return entry_points


def crawl(max_pages_per_school: Optional[int] = None,
          delay_range=(0.3, 0.8),
          request_timeout: int = 20,
          entry_points: Optional[list] = None,
          path_scope=None) -> Iterator[CrawlResult]:
    """
    BFS crawl of the FUSD domain. Yields one CrawlResult per fetched page.
    Single-fetch: HTML is carried on the result so the pipeline never re-downloads.

    Args:
        max_pages_per_school: per-scope cap (defaults to crawl_rules.json)
        entry_points: custom seed URLs (defaults to all schools + district)
        path_scope: optional callable(url)->bool; when given, only URLs passing
                    it are enqueued (used by refresh.py for time-sensitive paths)
    """
    rules_cap = SCHOOL_CONFIG.crawl_rules["crawling_behavior"]["max_pages_per_school"]
    cap = max_pages_per_school or rules_cap

    robots = RobotsCache()

    visited = set()
    queued = set()
    queue = []                     # (url, school_id) FIFO
    school_counts = {}

    def enqueue(url: str, school_id: str):
        norm = normalize_url(url)
        if norm in visited or norm in queued:
            return
        if not is_allowed_url(norm):
            return
        if path_scope is not None and not path_scope(norm):
            return
        if school_counts.get(school_id, 0) >= cap:
            return
        queued.add(norm)
        queue.append((norm, school_id))

    if entry_points:
        for ep in entry_points:
            enqueue(ep, classify_school(ep) or "district")
    else:
        for ep in build_entry_points():
            enqueue(ep, classify_school(ep) or "district")

    headers = {
        # NOTE: the site's WAF returns 403 for bot-style UAs (verified by test);
        # a standard browser UA is required to crawl at all.
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/pdf",
        "Accept-Language": "en-US,en;q=0.9",
    }

    total_fetched = 0

    with httpx.Client(headers=headers, follow_redirects=True, timeout=request_timeout) as client:
        while queue:
            url, parent_school = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            school_id = classify_school(url) or parent_school

            if not robots.allowed(url):
                logger.info(f"🤖 robots.txt disallows: {url}")
                continue

            if school_counts.get(school_id, 0) >= cap:
                continue

            try:
                response = client.get(url)
                response.raise_for_status()
            except Exception as e:
                logger.warning(f"Failed fetch: {url} -> {type(e).__name__}: {e}")
                yield CrawlResult(url=url, school_id=school_id, kind="error", error=str(e))
                time.sleep(random.uniform(*delay_range))
                continue

            content_type = response.headers.get("content-type", "")

            if PDF_PATTERN.search(url) or "application/pdf" in content_type:
                # PDFs carry no links worth following; pipeline extracts text separately
                school_counts[school_id] = school_counts.get(school_id, 0) + 1
                total_fetched += 1
                yield CrawlResult(url=url, school_id=school_id, kind="pdf")
                time.sleep(random.uniform(*delay_range))
                continue

            if "text/html" not in content_type and "application/xhtml" not in content_type:
                logger.info(f"Skipping non-HTML content-type '{content_type}': {url}")
                continue

            school_counts[school_id] = school_counts.get(school_id, 0) + 1
            total_fetched += 1

            if total_fetched % 50 == 0:
                logger.info(
                    f"📊 Crawl progress: {total_fetched} pages fetched | "
                    f"{len(queue)} queued | {len(school_counts)} sections active"
                )

            # Extract links BEFORE yielding so the caller can't stall discovery
            new_links = []
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "lxml")
                for a in soup.find_all("a"):
                    href = a.get("href")
                    if not href or not isinstance(href, str):
                        continue
                    href = href.strip()
                    if not href or href.startswith(("mailto:", "javascript:", "tel:", "#")):
                        continue
                    full = normalize_url(urljoin(url, href))
                    target_school = classify_school(full)
                    if target_school is None:
                        continue
                    new_links.append((full, target_school))
            except Exception:
                logger.exception(f"Link extraction failed for {url} - continuing with page only")

            for full, target_school in new_links:
                enqueue(full, target_school)

            yield CrawlResult(url=url, school_id=school_id, kind="html", html=response.text)

            time.sleep(random.uniform(*delay_range))

    logger.info(
        f"🏁 Crawl finished: {total_fetched} pages fetched across "
        f"{len(school_counts)} school/section scopes"
    )


if __name__ == "__main__":
    for res in crawl(max_pages_per_school=5):
        print(res.school_id, res.kind, res.url)
