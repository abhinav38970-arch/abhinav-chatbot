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

def convert_html_table_to_markdown(table):
    """
    Convert HTML table to Markdown format
    """
    rows = table.find_all('tr')
    if not rows:
        return None
    
    # Extract headers
    headers = []
    header_row = rows[0]
    for header in header_row.find_all(['th', 'td']):
        headers.append(header.get_text(strip=True))
    
    # Extract data rows
    data_rows = []
    for row in rows[1:]:
        row_data = []
        for cell in row.find_all(['th', 'td']):
            row_data.append(cell.get_text(strip=True))
        data_rows.append(row_data)
    
    # Create markdown table
    markdown_table = []
    markdown_table.append('| ' + ' | '.join(headers) + ' |')
    markdown_table.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    
    for row_data in data_rows:
        markdown_table.append('| ' + ' | '.join(row_data) + ' |')
    
    return '\n'.join(markdown_table)

def extract_image_alt_text(soup):
    """
    Extract alt text from images for contextual awareness
    """
    alt_texts = []
    for img in soup.find_all('img'):
        alt_text = img.get('alt', '').strip()
        if alt_text:
            alt_texts.append(f"IMAGE: {alt_text}")
    return '\n'.join(alt_texts) if alt_texts else None

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
    
    # TASK 2: Extract HTML tables and convert to Markdown
    table_markdowns = []
    if main_area:
        tables = main_area.find_all('table')
        for table in tables:
            markdown_table = convert_html_table_to_markdown(table)
            if markdown_table:
                table_markdowns.append(markdown_table)
    
    # TASK 2: Extract image alt texts
    image_context = extract_image_alt_text(soup)
    
    if main_area:
        # Extract text from the main area. Use "\n" so words in tables don't run together.
        cleaned_text = main_area.get_text(separator="\n", strip=True)
    else:
        # If there is no clear 'main' area, just get all remaining text.
        cleaned_text = soup.get_text(separator="\n", strip=True)

    # Get the Page Title so the AI knows what this info is about.
    title = soup.title.get_text(strip=True) if soup.title else "Untitled Page"
    
    # Format the data clearly for the database.
    final_output = f"TITLE: {title}\nURL: {url}\n"
    
    if table_markdowns:
        final_output += "TABLES:\n\n" + "\n\n".join(table_markdowns) + "\n\n"
    
    if image_context:
        final_output += "IMAGES:\n" + image_context + "\n\n"
    
    final_output += "CONTENT:\n" + cleaned_text

    return {"url": url, "text": final_output}