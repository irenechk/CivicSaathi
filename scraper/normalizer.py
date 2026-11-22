"""
Text and record normalizer for Civicsaathi.
Collapses redundant whitespace, normalizes currency representations, and cleans category tags.
"""

import re
from typing import Dict, Any, List


class Normalizer:
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Collapse multi-spaces and excessive newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @staticmethod
    def normalize_currency(amount_str: str) -> str:
        """Standardize Indian Rupee representations (Rs, INR, ₹)."""
        if not amount_str:
            return ""
        text = amount_str.replace("₹", "INR ").replace("Rs.", "INR ").replace("Rs", "INR ")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def normalize_tags(tags: List[str]) -> List[str]:
        """Convert list of tags into lowercased snake_case identifiers."""
        normalized = []
        for tag in tags:
            clean = tag.strip().lower().replace(" ", "_").replace("-", "_")
            if clean and clean not in normalized:
                normalized.append(clean)
        return normalized
