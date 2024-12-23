from bs4 import BeautifulSoup
import re

def clean_html_text(text: str) -> str:
    """Remove HTML tags and clean up text."""
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text()
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text