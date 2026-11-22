"""
PDF text extractor for official scheme operational guidelines.
Uses pypdf to extract pages, metadata, and clean text locally without external APIs.
"""

import io
from typing import Dict, Any, List
from pypdf import PdfReader


class PdfExtractor:
    @staticmethod
    def extract_from_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extracts clean text and page-wise passages from PDF byte data.
        """
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        pages_content: List[Dict[str, Any]] = []
        full_text_list = []

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned = "\n".join([line.strip() for line in page_text.splitlines() if line.strip()])
            pages_content.append({
                "page_number": idx + 1,
                "text": cleaned,
                "char_count": len(cleaned),
            })
            full_text_list.append(cleaned)

        metadata = reader.metadata or {}
        return {
            "total_pages": total_pages,
            "metadata": {
                "title": getattr(metadata, "title", None),
                "author": getattr(metadata, "author", None),
                "creator": getattr(metadata, "creator", None),
            },
            "pages": pages_content,
            "full_text": "\n\n--- Page Break ---\n\n".join(full_text_list),
        }

    @staticmethod
    def extract_from_file(file_path: str) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            return PdfExtractor.extract_from_bytes(f.read())
