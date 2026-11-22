"""
Deduplicator and overlap detector for Civicsaathi Scheme Knowledge Base.
Detects potential duplicates, acronym overlaps, and merged legacy schemes.
"""

import re
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher


class Deduplicator:
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """Returns sequence matcher similarity ratio between two titles."""
        s1 = re.sub(r"[^a-zA-Z0-9\s]", "", str1.lower()).strip()
        s2 = re.sub(r"[^a-zA-Z0-9\s]", "", str2.lower()).strip()
        seq_ratio = SequenceMatcher(None, s1, s2).ratio()

        # Token set overlap
        t1 = set(s1.split())
        t2 = set(s2.split())
        token_ratio = len(t1.intersection(t2)) / max(len(t1.union(t2)), 1)

        # Substring / Acronym check
        substr_boost = 0.8 if (s1 in s2 or s2 in s1) and min(len(s1), len(s2)) >= 3 else 0.0

        return max(seq_ratio, token_ratio, substr_boost)

    @staticmethod
    def find_potential_duplicates(
        new_scheme_name: str,
        existing_schemes: List[Dict[str, Any]],
        threshold: float = 0.75,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Check whether a new scheme title or acronym closely matches existing records.
        """
        duplicates = []
        for scheme in existing_schemes:
            name = scheme.get("scheme_name", "")
            ratio = Deduplicator.calculate_similarity(new_scheme_name, name)
            if ratio >= threshold:
                duplicates.append((scheme, round(ratio, 3)))
                continue

            # Also check alternate names / acronyms
            for alt in scheme.get("alternate_names", []):
                alt_ratio = Deduplicator.calculate_similarity(new_scheme_name, alt)
                if alt_ratio >= threshold:
                    duplicates.append((scheme, round(alt_ratio, 3)))
                    break

        return sorted(duplicates, key=lambda x: x[1], reverse=True)
