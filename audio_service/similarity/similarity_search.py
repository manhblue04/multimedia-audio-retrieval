import numpy as np
from typing import List, Dict


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def find_top_k(
    query_features: List[float],
    dataset: List[Dict],
    top_k: int = 5,
    exclude_file: str = None,
) -> List[Dict]:
    """
    Find the top-K most similar audio files by cosine similarity.

    Each item in `dataset` must have:
      - "features": List[float]
      - "file_name": str
      - "instrument": str
      - "duration": float
      - "sample_rate": int
      - "_id" (optional)
    """
    query_vec = np.array(query_features, dtype=np.float64)

    results = []
    for doc in dataset:
        fname = doc.get("file_name", "")
        if exclude_file and fname == exclude_file:
            continue
        db_vec = np.array(doc["features"], dtype=np.float64)
        score = cosine_similarity(query_vec, db_vec)
        results.append({
            "file_name": fname,
            "instrument": doc.get("instrument", "unknown"),
            "duration": doc.get("duration", 0),
            "sample_rate": doc.get("sample_rate", 22050),
            "similarity": round(score, 6),
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def compute_precision_at_k(top_k_results: List[Dict], query_instrument: str, k: int = 5) -> float:
    """Compute Precision@K: fraction of top-K results matching query instrument."""
    if not top_k_results:
        return 0.0
    relevant = sum(1 for r in top_k_results[:k] if r["instrument"] == query_instrument)
    return round(relevant / min(k, len(top_k_results)), 4)
