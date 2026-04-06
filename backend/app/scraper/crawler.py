import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import random
from backend.app.logs.logger import logger

# The starting point for the scout.
BASE_URL = "https://fremontunified.org/washington/"
# Extracts 'fremontunified.org' so we know what our "home" domain is.
DOMAIN = urlparse(BASE_URL).netloc

# A list of allowed sections within the Fremont Unified site that relate to school info.
DISTRICT_SECTIONS = ["about", "students-community", "departments", "services", "calendar", "board", "policies", "transportation", "meals", "safety"]

def normalize_url(url):
    # Remove the "#section" part of a URL so 'page.html#info' becomes just 'page.html'.
    url, _ = urldefrag(url)
    # Remove the trailing slash at the end so 'site.com/' and 'site.com' are treated as the same.
    return url.rstrip("/")

def crawl():
    # A set of URLs we have already finished looking at.
    visited = set()
    # A list of URLs we found but haven't visited yet (the "To-Do" list).
    to_visit = [BASE_URL]

    # Fake browser information so the website doesn't block the scraper.
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}

    # Open a connection to the internet.
    with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
        while to_visit:
            # Take the first URL off the To-Do list.
            url = normalize_url(to_visit.pop(0))

            # If we've already been here, don't go again.
            if url in visited:
                continue

            logger.info(f"Crawling: {url}")

            try:
                # Actually download the page.
                response = client.get(url)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed request: {url} -> {e}")
                continue

            # Mark this URL as finished.
            visited.add(url)

            # Turn the HTML code into a "Soup" object that Python can search.
            soup = BeautifulSoup(response.text, "lxml")

            # Look at every single <a href="..."> link on the page.
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # Convert relative links (like "/events") into full links ("https://site.com/events").
                full_url = normalize_url(urljoin(url, href))
                parsed = urlparse(full_url)

                # CRITICAL: If the link goes to Google or Facebook (not our domain), skip it.
                if parsed.netloc != DOMAIN:
                    continue

                # Split the URL path into parts (e.g., /washington/students -> ['washington', 'students']).
                path_parts = parsed.path.strip("/").split("/")

                if len(path_parts) > 0 and path_parts[0]:
                    first_section = path_parts[0].lower()
                    # Only keep links if they start with 'washington' or an allowed district section.
                    if first_section == "washington" or first_section in DISTRICT_SECTIONS:
                        pass
                    else:
                        continue

                # Skip non-text files that we can't read anyway.
                if full_url.lower().endswith((".jpg", ".png", ".zip", ".mov", ".mp4")):
                    continue

                # If it's a new link we haven't seen yet, add it to the To-Do list.
                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

            # Wait a random amount of time (0.3 to 1.1 seconds) so we don't crash the school's server.
            time.sleep(random.uniform(0.3, 1.1))

    return list(visited)