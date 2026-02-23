"""
RAG pipeline glue code (retrieval only, no generation yet).

Flow:
    user question -> embed -> FAISS search -> top-k chunks -> merged context_text
"""

from pathlib import Path
import sys
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# Paths reuse existing artifacts produced in earlier phases.
EMBED_PATH = Path("vector_db/embeddings.npy")
META_PATH = Path("vector_db/meta_chunks.csv")
INDEX_PATH = Path("vector_db/faiss_index/index.faiss")
MODEL_NAME = "all-MiniLM-L6-v2"


def _load_index(index_path: Path = INDEX_PATH) -> faiss.Index:
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {index_path}. Build it via vector_store.build_index()."
        )
    return faiss.read_index(str(index_path))


def _load_meta(meta_path: Path = META_PATH) -> pd.DataFrame:
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Metadata CSV not found at {meta_path}. Generate via embedding_service.generate_embeddings()."
        )
    return pd.read_csv(meta_path)


class RagPipeline:
    """Lightweight retriever that returns concatenated context (no LLM)."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        index_path: Path = INDEX_PATH,
        meta_path: Path = META_PATH,
        top_k: int = 5,
    ):
        self.model = SentenceTransformer(model_name)
        self.index = _load_index(index_path)
        self.meta = _load_meta(meta_path)
        self.top_k = top_k

    def retrieve(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Return merged context text and per-hit metadata with scores."""
        vec = self.model.encode([question])
        vec = np.array(vec, dtype=np.float32)
        faiss.normalize_L2(vec)

        scores, idxs = self.index.search(vec, self.top_k)

        hits = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1 or idx >= len(self.meta):
                continue
            row = self.meta.iloc[int(idx)].to_dict()
            row["score"] = float(score)
            hits.append(row)

        context_text = "\n\n".join(hit["chunk_text"] for hit in hits if "chunk_text" in hit)
        return context_text, hits


if __name__ == "__main__":
    pipeline = RagPipeline()
    sample_q = "python developer with cloud and devops experience"
    context, hits = pipeline.retrieve(sample_q)
    print("Top hits (score, title, company):")
    for h in hits:
        print(f"{h['score']:.3f} | {h.get('title')} | {h.get('company')}")
    preview = context[:500].encode("utf-8", errors="ignore")
    sys.stdout.buffer.write(b"\nContext preview:\n" + preview + b"...\n")
