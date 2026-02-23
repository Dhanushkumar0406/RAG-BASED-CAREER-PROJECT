from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

PROCESSED_PATH = Path("dataset/processed/jobs_cleaned.csv")
EMBED_PATH = Path("vector_db/embeddings.npy")
META_PATH = Path("vector_db/meta_chunks.csv")


def generate_embeddings(
    processed_path: Path = PROCESSED_PATH,
    embed_path: Path = EMBED_PATH,
    meta_path: Path = META_PATH,
    model_name: str = "all-MiniLM-L6-v2",
) -> Tuple[np.ndarray, pd.DataFrame]:
    df = pd.read_csv(processed_path)
    if df.empty:
        raise ValueError("Processed dataset is empty; run preprocessing first.")

    model = SentenceTransformer(model_name)
    vectors = model.encode(
        df["chunk_text"].tolist(), batch_size=64, show_progress_bar=True
    )
    vectors = np.array(vectors, dtype=np.float32)

    np.save(embed_path, vectors)
    df.to_csv(meta_path, index=False)

    print(f"Saved embeddings to {embed_path} with shape {vectors.shape}")
    print(f"Saved metadata to {meta_path}")
    return vectors, df


if __name__ == "__main__":
    generate_embeddings()
