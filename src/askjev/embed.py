"""Local embeddings (BAAI/bge-small-en-v1.5, 384 dims). Never a gateway model."""
from functools import lru_cache

import numpy as np

from .config import EMBED_MODEL


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(EMBED_MODEL)


def embed(texts: list[str], batch_size: int = 256) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vecs = np.array(list(_model().embed(texts, batch_size=batch_size)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.clip(norms, 1e-9, None)


def to_pg(v: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def question_text(text: str, options=None, state=None) -> str:
    """What gets embedded for a question: text + option labels + an input excerpt (so same-text items differ)."""
    parts = [text]
    if isinstance(options, dict):
        parts.append(" / ".join(str(v or k) for k, v in list(options.items())[:12]))
    elif isinstance(options, list):
        parts.append(" / ".join(str(x) for x in options[:10]))
    if state:
        parts.append(str(state)[:400])
    return "\n".join(parts)
