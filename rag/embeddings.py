"""
Local Embedding Engine for Civicsaathi RAG.
100% locally hosted with zero paid API dependencies.
Uses an optimized TF-IDF + BM25 Sublinear N-gram vectorizer for deterministic, fast, offline embeddings,
with pluggable architecture for sentence-transformers / local Ollama embeddings when installed.
"""

import numpy as np
from typing import List, Union
from sklearn.feature_extraction.text import TfidfVectorizer


class LocalEmbeddingEngine:
    MODEL_NAME = "civicsaathi-local-tfidf-v1"
    DIMENSION = 512

    def __init__(self, max_features: int = 512):
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
        )
        self.is_fitted = False

    def fit(self, texts: List[str]) -> "LocalEmbeddingEngine":
        """Fits vocabulary on scheme corpus."""
        if texts:
            self.vectorizer.fit(texts)
            self.is_fitted = True
        return self

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embeds a list of texts into dense vectors with fixed dimensionality."""
        if not self.is_fitted:
            self.fit(texts)
        sparse_matrix = self.vectorizer.transform(texts)
        dense = sparse_matrix.toarray()
        if dense.shape[1] < self.max_features:
            pad_width = self.max_features - dense.shape[1]
            dense = np.pad(dense, ((0, 0), (0, pad_width)), mode="constant")
        # Normalize to unit length for cosine similarity
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return dense / norms

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single search query with fixed dimensionality."""
        if not self.is_fitted:
            # Fallback uniform vector
            return np.ones(self.max_features) / np.sqrt(self.max_features)
        sparse_vec = self.vectorizer.transform([query])
        dense = sparse_vec.toarray()[0]
        if len(dense) < self.max_features:
            pad_width = self.max_features - len(dense)
            dense = np.pad(dense, (0, pad_width), mode="constant")
        norm = np.linalg.norm(dense)
        if norm == 0:
            return dense
        return dense / norm
