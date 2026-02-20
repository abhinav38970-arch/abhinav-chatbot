import httpx
from bs4 import BeautifulSoup


def parse_page(url):
    """
    Downloads a webpage and extracts meaningful text content.
    """

    print(f"📝Parsing: {url}")

    try:
        response = httpx.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to parse {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    content = []

    # page title
    if soup.title:
        content.append(soup.title.get_text(strip=True))

    # headings
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(strip=True)
        if text:
            content.append(text)

    # paragraphs
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            content.append(text)

    # list items
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text:
            content.append(f"- {text}")

    cleaned_text = "\n".join(content)

    return {
        "url": url,
        "text": cleaned_text
    }
