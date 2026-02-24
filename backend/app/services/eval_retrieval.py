"""
Quick retrieval evaluation utility.

Usage:
    python -m app.services.eval_retrieval "python developer aws"

What it does:
    - Loads FAISS index + metadata.
    - Runs sample queries (provided CLI args or defaults).
    - Prints top-k hits with scores, title, company, skills.
    - Computes a simple keyword precision metric based on query term overlap.
"""

from __future__ import annotations

import sys
from typing import Iterable, List

import pandas as pd

from .rag_pipeline import RagPipeline


DEFAULT_QUERIES = [
    "senior backend engineer python aws",
    "frontend react typescript remote",
    "data scientist machine learning",
    "devops kubernetes terraform",
]


def keyword_precision(query: str, hits: List[dict]) -> float:
    """Toy metric: proportion of hits whose chunk_text contains any query term."""
    terms = {t.lower() for t in query.split() if len(t) > 2}
    if not hits:
        return 0.0
    matched = 0
    for h in hits:
        text = (h.get("chunk_text") or "").lower()
        if any(t in text for t in terms):
            matched += 1
    return matched / len(hits)


def run_eval(queries: Iterable[str]) -> None:
    pipeline = RagPipeline()
    for q in queries:
        context, hits = pipeline.retrieve(q)
        prec = keyword_precision(q, hits)
        print(f"\nQuery: {q}")
        print(f"Top {len(hits)} hits | keyword_precision: {prec:.2f}")
        for h in hits:
            print(
                f"  {h.get('score'):.3f} | {h.get('title')} | {h.get('company')} | {h.get('skills')}"
            )


if __name__ == "__main__":
    queries = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_QUERIES
    run_eval(queries)
