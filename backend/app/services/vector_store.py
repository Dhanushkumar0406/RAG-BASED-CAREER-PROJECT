from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

EMBED_PATH = Path("vector_db/embeddings.npy")
META_PATH = Path("vector_db/meta_chunks.csv")
INDEX_DIR = Path("vector_db/faiss_index")
INDEX_PATH = INDEX_DIR / "index.faiss"


def build_index(
    embed_path: Path = EMBED_PATH,
    index_path: Path = INDEX_PATH,
) -> faiss.Index:
    vectors = np.load(embed_path)
    if vectors.ndim != 2:
        raise ValueError("Embeddings should be a 2D array.")

    # Cosine similarity via normalized vectors + inner product index
    faiss.normalize_L2(vectors)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    print(f"FAISS index saved to {index_path} (vectors: {vectors.shape[0]}, dim: {dim})")
    return index


def load_index(index_path: Path = INDEX_PATH) -> faiss.Index:
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found at {index_path}")
    return faiss.read_index(str(index_path))


def similarity_search(
    query: str,
    top_k: int = 5,
    meta_path: Path = META_PATH,
    index_path: Path = INDEX_PATH,
    model_name: str = "all-MiniLM-L6-v2",
) -> List[Tuple[float, dict]]:
    meta = pd.read_csv(meta_path)
    index = load_index(index_path)
    model = SentenceTransformer(model_name)

    vec = model.encode([query])
    vec = np.array(vec, dtype=np.float32)
    faiss.normalize_L2(vec)
    scores, idxs = index.search(vec, top_k)

    results = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx == -1 or idx >= len(meta):
            continue
        row = meta.iloc[int(idx)].to_dict()
        results.append((float(score), row))
    return results


if __name__ == "__main__":
    build_index()
    hits = similarity_search("python developer with cloud experience")
    for score, row in hits:
        print(score, row.get("title"), "-", row.get("company"))
