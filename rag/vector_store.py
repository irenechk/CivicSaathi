"""
Local Vector Store and Metadata Index for Civicsaathi.
Stores embeddings and chunk metadata in local memory and SQLite.
Supports metadata filtering (state, category, beneficiary, verification status).
"""

import numpy as np
from typing import List, Dict, Any, Optional
from rag.embeddings import LocalEmbeddingEngine


class LocalVectorStore:
    def __init__(self, embedding_engine: Optional[LocalEmbeddingEngine] = None):
        self.embedding_engine = embedding_engine or LocalEmbeddingEngine()
        self.chunks: List[Dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Add chunks to index and compute local embeddings."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        self.embedding_engine.fit(texts)
        new_vectors = self.embedding_engine.embed_documents(texts)

        if self.vectors is None:
            self.vectors = new_vectors
            self.chunks = list(chunks)
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])
            self.chunks.extend(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        state_filter: Optional[str] = None,
        verification_filter: Optional[str] = None,
        benefit_type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Cosine similarity search with optional metadata filtering.
        """
        if self.vectors is None or len(self.chunks) == 0:
            return []

        query_vec = self.embedding_engine.embed_query(query)
        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.vectors, query_vec)

        # Apply metadata filters
        valid_indices = []
        for idx, chunk in enumerate(self.chunks):
            meta = chunk.get("metadata", {})
            if state_filter and state_filter.lower() != "all":
                c_state = meta.get("state_or_ut", "all").lower()
                if c_state != "all" and state_filter.lower() not in c_state:
                    continue
            if verification_filter and meta.get("verification_status") != verification_filter:
                continue
            if benefit_type_filter:
                b_types = meta.get("benefit_types", [])
                if benefit_type_filter not in b_types:
                    continue
            valid_indices.append((idx, scores[idx]))

        # Sort by similarity score descending
        valid_indices.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in valid_indices[:top_k]:
            item = dict(self.chunks[idx])
            item["score"] = float(score)
            results.append(item)

        return results
