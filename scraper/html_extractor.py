"""
HTML parsing and structured content extraction for government scheme pages.
Extracts title, meta tags, scheme headings, text sections, and links to guideline PDFs.
"""

from typing import Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class HtmlExtractor:
    @staticmethod
    def extract_scheme_page(html_content: str, base_url: str = "") -> Dict[str, Any]:
        """
        Parses HTML and extracts structured sections and PDF links.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts and styles
        for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            element.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract headings and main sections
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

        # Collect paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
        cleaned_text = "\n\n".join(paragraphs)

        # Extract PDF links
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().endswith(".pdf") or ".pdf" in href.lower():
                full_url = urljoin(base_url, href) if base_url else href
                link_text = a.get_text(strip=True) or "Download PDF"
                pdf_links.append({"text": link_text, "url": full_url})

        return {
            "title": title,
            "headings": headings,
            "cleaned_text": cleaned_text,
            "pdf_links": pdf_links,
            "total_characters": len(cleaned_text),
        }
