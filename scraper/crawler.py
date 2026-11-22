"""
Polite, rate-limited government webpage and document crawler.
Adheres strictly to scraping rules:
- Respects rate limits and timeouts
- Avoids hammering servers
- Logs failures rather than crashing
- Does not bypass CAPTCHAs or logins
"""

import time
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from scraper.source_registry import SourceRegistry


class GovernmentCrawler:
    def __init__(self, user_agent: str = "CivicsaathiBot/1.0 (+https://civicsaathi.org/bot)", rate_limit_delay: float = 1.0):
        self.user_agent = user_agent
        self.rate_limit_delay = rate_limit_delay
        self.registry = SourceRegistry()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        })

    def fetch_url(self, url: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Safely fetch an approved government URL.
        Returns dictionary with status_code, content, content_type, and error.
        """
        if not self.registry.is_permitted_url(url):
            return {
                "success": False,
                "url": url,
                "status_code": 403,
                "error": "URL domain is not in the approved government domain registry.",
                "content": None,
                "content_type": None,
            }

        try:
            # Respect rate limit
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            content_type = response.headers.get("Content-Type", "")

            if response.status_code == 200:
                return {
                    "success": True,
                    "url": url,
                    "status_code": 200,
                    "content": response.content,
                    "text": response.text if "text" in content_type or "html" in content_type else "",
                    "content_type": content_type,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "url": url,
                    "status_code": response.status_code,
                    "content": None,
                    "content_type": content_type,
                    "error": f"HTTP {response.status_code}",
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "url": url,
                "status_code": None,
                "content": None,
                "content_type": None,
                "error": str(e),
            }
