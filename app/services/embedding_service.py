"""
Embedding service wrapping a SentenceTransformer model.

The model is **lazy-loaded** on first use so that the FastAPI application can
start serving health checks immediately without waiting for a large model
download.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

import os

from app.config import EMBEDDING_MODEL, HF_ENDPOINT
from app.exceptions import ModelUnavailableError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Thin wrapper around ``SentenceTransformer`` that:

    * Defers model loading until :meth:`encode` is first called.
    * Always returns **L2-normalised** float32 vectors, so cosine similarity
      reduces to a dot product.
    * Raises :class:`ModelUnavailableError` when loading fails.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model: Optional[object] = None

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` once the underlying model has been loaded."""
        return self._model is not None

    def _load_model(self) -> None:
        """Import and instantiate the SentenceTransformer (called once)."""
        if self._model is not None:
            return
        try:
            # Allow overriding the Hugging Face endpoint via environment
            # (e.g. HF_ENDPOINT=https://hf-mirror.com for regions where
            # huggingface.co is unreachable).
            if "HF_ENDPOINT" not in os.environ and HF_ENDPOINT:
                os.environ["HF_ENDPOINT"] = HF_ENDPOINT

            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as exc:
            logger.exception("Failed to load embedding model %s", self.model_name)
            raise ModelUnavailableError(
                message=f"无法加载 Embedding 模型 {self.model_name}：{exc}"
            ) from exc

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Generate normalised embedding vectors for *texts*.

        Returns a ``(len(texts), dim)`` float32 array whose rows are
        L2-normalised.
        """
        self._load_model()
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)


# ---------------------------------------------------------------------------
# Module-level singleton — shared across all requests.
# ---------------------------------------------------------------------------

embedding_service = EmbeddingService()
