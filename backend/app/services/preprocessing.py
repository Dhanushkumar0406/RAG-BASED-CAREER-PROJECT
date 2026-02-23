import math
import re
from pathlib import Path
from typing import List

import pandas as pd
from bs4 import BeautifulSoup

RAW_DATA_PATH = Path("dataset/raw/jobs_raw.csv")
PROCESSED_PATH = Path("dataset/processed/jobs_cleaned.csv")


def strip_html(text: str) -> str:
    """Remove HTML tags and extra whitespace, lowercase for normalization."""
    text = text or ""
    cleaned = BeautifulSoup(text, "lxml").get_text(separator=" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def build_document(title: str, skills: str, description: str) -> str:
    parts = [title or "", skills or "", description or ""]
    return " ".join(p.strip() for p in parts if p).strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping word chunks."""
    words = text.split()
    if not words:
        return []
    step = max(chunk_size - overlap, 1)
    chunks = []
    for start in range(0, len(words), step):
        chunk = words[start : start + chunk_size]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        if start + chunk_size >= len(words):
            break
    return chunks


def clean_and_chunk(
    raw_path: Path = RAW_DATA_PATH,
    output_path: Path = PROCESSED_PATH,
    chunk_size: int = 500,
    overlap: int = 50,
) -> pd.DataFrame:
    """Load raw data, clean, build documents, chunk, and save processed CSV."""
    df = pd.read_csv(raw_path)

    # Basic cleaning and normalization
    df["title"] = df["title"].fillna("").astype(str).str.strip().str.lower()
    df["company"] = df["company"].fillna("").astype(str).str.strip().str.lower()
    df["location"] = df["location"].fillna("").astype(str).str.strip()
    df["skills"] = df["skills"].fillna("").astype(str).str.lower()
    df["description_clean"] = df["description"].fillna("").astype(str).apply(strip_html)

    # Remove duplicates on core identifying fields
    df = df.drop_duplicates(subset=["title", "company", "description_clean"])

    # Build document field
    df["document"] = df.apply(
        lambda row: build_document(row["title"], row["skills"], row["description_clean"]),
        axis=1,
    )

    # Explode into chunks
    records = []
    for idx, row in df.iterrows():
        chunks = chunk_text(row["document"], chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            continue
        for i, chunk in enumerate(chunks):
            records.append(
                {
                    "orig_id": idx,
                    "chunk_id": f"{idx}_{i}",
                    "title": row["title"],
                    "company": row["company"],
                    "location": row["location"],
                    "skills": row["skills"],
                    "description_clean": row["description_clean"],
                    "document": row["document"],
                    "chunk_text": chunk,
                }
            )

    processed_df = pd.DataFrame.from_records(records)
    processed_df.to_csv(output_path, index=False)
    print(f"Processed rows: {len(processed_df)} saved to {output_path}")
    return processed_df


if __name__ == "__main__":
    clean_and_chunk()
