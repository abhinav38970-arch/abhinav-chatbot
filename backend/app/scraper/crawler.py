import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import random
from backend.app.logs.logger import logger

BASE_URL = "https://fremontunified.org/washington/"
DOMAIN = urlparse(BASE_URL).netloc

# district sections we want to allow
DISTRICT_SECTIONS = [
    "about",
    "students-community",
    "departments",
    "services",
    "calendar",
    "board",
    "policies",
    "transportation",
    "meals",
    "safety",
]


def normalize_url(url):
    """Removes fragments (#section) and trailing slashes."""
    url, _ = urldefrag(url)
    return url.rstrip("/")


def crawl():
    visited = set()
    to_visit = [BASE_URL]

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive",
    }

    with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
        while to_visit:
            url = normalize_url(to_visit.pop(0))

            if url in visited:
                continue

            logger.info(f"Crawling: {url}")

            try:
                response = client.get(url)
                logger.info(f"Status: {response.status_code}")
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed request: {url} -> {e}")
                continue

            visited.add(url)
            logger.info(f"Visited count: {len(visited)}")

            soup = BeautifulSoup(response.text, "lxml")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = normalize_url(urljoin(url, href))
                parsed = urlparse(full_url)

                if parsed.netloc != DOMAIN:
                    continue

                if "/cdn-cgi/" in full_url:
                    continue

                path_parts = parsed.path.strip("/").split("/")

                if len(path_parts) > 0 and path_parts[0]:
                    first_section = path_parts[0].lower()

                    if first_section == "washington":
                        pass
                    elif first_section in DISTRICT_SECTIONS:
                        pass
                    else:
                        continue

                if full_url.lower().endswith(
                    (".doc", ".docx", ".jpg", ".png", ".zip")
                ):
                    continue

                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)
                    logger.info(f"Queued URL: {full_url}")

            # 🔥 HUMAN-LIKE RANDOM DELAY (FASTER + STEALTHIER)
            time.sleep(random.uniform(0.3, 1.1))

    logger.info(f"Crawling complete. Total visited: {len(visited)}")
    return list(visited)