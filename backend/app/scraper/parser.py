import httpx
import random
import time
from bs4 import BeautifulSoup
from backend.app.logs.logger import logger


client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive",
    },
    follow_redirects=True,
    timeout=20,
)

def human_delay():
    """Random delay to mimic human browsing."""
    delay = random.uniform(1.2, 3.8)
    logger.debug(f"Sleeping {delay:.2f}s to mimic human browsing")
    time.sleep(delay)

def parse_page(url):
    """Downloads webpage and extracts meaningful text."""

    logger.info(f"Parsing page: {url}")

    human_delay()

    try:
        response = client.get(url)
        logger.info(f"Status: {response.status_code}")
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Parse failed: {url} -> {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    logger.info("HTML downloaded successfully")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    content = []

    if soup.title:
        content.append(soup.title.get_text(strip=True))

    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(strip=True)
        if text:
            content.append(text)

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            content.append(text)

    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text:
            content.append(f"- {text}")

    cleaned_text = "\n".join(content)

    logger.info(f"Extracted {len(cleaned_text)} characters")

    return {"url": url, "text": cleaned_text}
