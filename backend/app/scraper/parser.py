import httpx
import random
import time
import re
from bs4 import BeautifulSoup
from backend.app.logs.logger import logger

client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://fremontunified.org/washington/"
    },
    follow_redirects=True,
    timeout=20,
)

def table_to_markdown(table):
    """Converts an HTML table into a clean Markdown string."""
    rows = table.find_all("tr")
    if not rows:
        return ""
    
    markdown_rows = []
    for i, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        cell_text = [cell.get_text(strip=True) for cell in cells]
        
        # Create the row string
        markdown_rows.append("| " + " | ".join(cell_text) + " |")
        
        # If this was the header row, add the separator line
        if i == 0 and len(cells) > 0:
            markdown_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
            
    return "\n" + "\n".join(markdown_rows) + "\n"

def parse_page(url):
    logger.info(f"Parsing page: {url}")
    try:
        response = client.get(url)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Parse failed: {url} -> {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # CLEANUP: Remove nav, footer, etc.
    for junk in soup.find_all(["nav", "footer", "header", "aside", "form"]):
        junk.decompose()
    for menu_junk in soup.find_all(class_=re.compile("menu|sidebar|nav|sub-menu|widget")):
        menu_junk.decompose()

    main_area = soup.find("main") or soup.find(id="content") or soup.find(class_="entry-content")
    
    if main_area:
        # --- NEW: TABLE PROCESSING ---
        # Find all tables and replace them with Markdown versions
        for table in main_area.find_all("table"):
            md_table = table_to_markdown(table)
            table.replace_with(md_table)
        
        cleaned_text = main_area.get_text(separator="\n", strip=True)
    else:
        cleaned_text = soup.get_text(separator="\n", strip=True)

    title = soup.title.get_text(strip=True) if soup.title else "Untitled Page"
    
    # Format the data clearly
    final_output = f"TITLE: {title}\nURL: {url}\nCONTENT:\n{cleaned_text}"

    return {"url": url, "text": final_output}