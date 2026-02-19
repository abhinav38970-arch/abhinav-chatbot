import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time

BASE_URL = "https://fremontunified.org/washington/"
DOMAIN = urlparse(BASE_URL).netloc


def normalize_url(url):
    """
    Removes fragments (#section) and trailing slashes
    to avoid duplicate pages.
    """
    url, _ = urldefrag(url)  # remove #fragment
    return url.rstrip("/")


def crawl():
    visited = set()
    to_visit = [BASE_URL]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:

        while to_visit:
            url = normalize_url(to_visit.pop(0))

            if url in visited:
                continue

            print(f"Crawling: {url}")

            try:
                response = client.get(url)
                print("Status:", response.status_code)
                response.raise_for_status()
            except Exception as e:
                print(f"Failed: {url} -> {e}")
                continue

            visited.add(url)

            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a", href=True):
                href = link["href"]

                full_url = normalize_url(urljoin(url, href))
                parsed = urlparse(full_url)

                # stay inside domain
                if parsed.netloc != DOMAIN:
                    continue

                # skip cloudflare & system paths
                if "/cdn-cgi/" in full_url:
                    continue

                # skip files
                if full_url.lower().endswith(
                    (".doc", ".docx", ".jpg", ".png", ".zip")
                ):
                    continue

                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

            time.sleep(1)  # be respectful

    return list(visited)
