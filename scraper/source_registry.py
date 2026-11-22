"""
Source Registry manager for Civicsaathi.
Maintains approved government domains, rate limits, and provenance metadata.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_CSV = BASE_DIR / "data" / "raw" / "sources_registry.csv"

# Permitted official Indian Government TLDs and domains
PERMITTED_GOV_DOMAINS = {
    "gov.in",
    "nic.in",
    "dbtbharat.gov.in",
    "myscheme.gov.in",
    "scholarships.gov.in",
    "pib.gov.in",
    "indiabudget.gov.in",
    "mospi.gov.in",
    "jansuraksha.gov.in",
    "pmfby.gov.in",
}


class SourceRegistry:
    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or SOURCES_CSV
        self.sources: List[Dict[str, Any]] = []
        self.load_sources()

    def load_sources(self) -> List[Dict[str, Any]]:
        self.sources = []
        if self.registry_file.exists():
            with open(self.registry_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.sources.append(dict(row))
        return self.sources

    def is_permitted_url(self, url: str) -> bool:
        """Check whether the target URL belongs to an approved government domain."""
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            if not hostname:
                return False
            for allowed in PERMITTED_GOV_DOMAINS:
                if hostname == allowed or hostname.endswith("." + allowed):
                    return True
            return False
        except Exception:
            return False

    def get_approved_sources(self) -> List[Dict[str, Any]]:
        return [s for s in self.sources if self.is_permitted_url(s.get("exact_url", ""))]

    def add_source(self, source_ref: str, publisher: str, title: str, url: str, section: str, fields: str) -> Dict[str, Any]:
        """Add a new source with domain validation."""
        is_permitted = self.is_permitted_url(url)
        new_source = {
            "source_ref": source_ref,
            "publisher": publisher,
            "document_or_page_title": title,
            "exact_url": url,
            "publication_or_updated_date": "",
            "access_date": "2026-11-21",
            "relevant_section": section,
            "fields_supported": fields,
            "is_approved": is_permitted,
        }
        self.sources.append(new_source)
        return new_source
