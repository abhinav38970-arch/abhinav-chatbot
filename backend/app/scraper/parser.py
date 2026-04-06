import httpx
import random
import time
import re
from bs4 import BeautifulSoup
from backend.app.logs.logger import logger

# Setup a persistent internet connection with browser-like headers.
client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://fremontunified.org/washington/"
    },
    follow_redirects=True,
    timeout=20,
)

def parse_page(url):
    logger.info(f"Parsing page: {url}")
    
    try:
        # Download the specific page.
        response = client.get(url)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Parse failed: {url} -> {e}")
        return None

    # Load HTML into BeautifulSoup.
    soup = BeautifulSoup(response.text, "lxml")

    # DELETE repetitive sections: This removes the Top Menu, Bottom Footer, and Sidebars.
    # This prevents the 68,000 lines of junk from entering your database.
    for junk in soup.find_all(["nav", "footer", "header", "aside", "form"]):
        junk.decompose()
    
    # Target specific CSS classes often used for menus on the FUSD site.
    for menu_junk in soup.find_all(class_=re.compile("menu|sidebar|nav|sub-menu|widget")):
        menu_junk.decompose()

    # Find the "Meat" of the page. Most school sites put real info in <main> or a content div.
    # This ensures we get text inside tables and the (+) accordion boxes.
    main_area = soup.find("main") or soup.find(id="content") or soup.find(class_="entry-content")
    
    if main_area:
        # Extract text from the main area. Use "\n" so words in tables don't run together.
        cleaned_text = main_area.get_text(separator="\n", strip=True)
    else:
        # If there is no clear 'main' area, just get all remaining text.
        cleaned_text = soup.get_text(separator="\n", strip=True)

    # Get the Page Title so the AI knows what this info is about.
    title = soup.title.get_text(strip=True) if soup.title else "Untitled Page"
    
    # Format the data clearly for the database.
    final_output = f"TITLE: {title}\nURL: {url}\nCONTENT:\n{cleaned_text}"

    return {"url": url, "text": final_output}