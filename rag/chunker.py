"""
Document chunker for Civicsaathi RAG pipeline.
Splits long government guidelines and scheme descriptions into structured passages
while preserving section headings and metadata.
"""

from typing import List, Dict, Any


class DocumentChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits text by double newlines (paragraphs) or sliding word window.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[Dict[str, Any]] = []

        current_chunk_words: List[str] = []
        chunk_index = 0

        for p in paragraphs:
            words = p.split()
            if len(current_chunk_words) + len(words) <= self.chunk_size:
                current_chunk_words.extend(words)
            else:
                if current_chunk_words:
                    chunk_text = " ".join(current_chunk_words)
                    chunk_meta = dict(metadata)
                    chunk_meta["chunk_id"] = f"{metadata.get('doc_id', 'doc')}_c{chunk_index}"
                    chunk_meta["chunk_index"] = chunk_index
                    chunks.append({"text": chunk_text, "metadata": chunk_meta})
                    chunk_index += 1

                    # Retain overlap words
                    current_chunk_words = current_chunk_words[-self.chunk_overlap:] + words
                else:
                    current_chunk_words = words

        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            chunk_meta = dict(metadata)
            chunk_meta["chunk_id"] = f"{metadata.get('doc_id', 'doc')}_c{chunk_index}"
            chunk_meta["chunk_index"] = chunk_index
            chunks.append({"text": chunk_text, "metadata": chunk_meta})

        return chunks
