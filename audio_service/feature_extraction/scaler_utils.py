"""
Two-step normalization for audio features:
  1. StandardScaler: zero-mean, unit-variance per dimension
  2. L2 normalize: each sample vector becomes unit-norm (required for cosine similarity)

Why both?
  - StandardScaler removes the scale difference between feature types
    (e.g. MFCC values ~[-500, 500] vs RMS ~[0, 0.05]).
  - L2 normalization ensures cosine similarity measures the true angle between
    feature vectors, not their magnitudes.
"""
import numpy as np
from pathlib import Path

SCALER_PATH = Path(__file__).resolve().parents[2] / "features" / "scaler.npz"


def save_scaler(mean: np.ndarray, scale: np.ndarray, path: Path = None):
    path = path or SCALER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, mean=mean, scale=scale)


def load_scaler(path: Path = None) -> tuple:
    path = path or SCALER_PATH
    if not path.exists():
        return None, None
    data = np.load(path)
    return data["mean"], data["scale"]


def normalize_features(features, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """
    Apply StandardScaler then L2 normalization to a feature vector or matrix.
    features: list, 1-D array (single sample), or 2-D array (N × D)
    Returns: normalized numpy array of same shape.
    """
    arr = np.array(features, dtype=np.float64)
    # Step 1 – StandardScaler (per-dimension centering + scaling)
    scale_safe = np.where(scale == 0, 1.0, scale)
    arr = (arr - mean) / scale_safe
    # Step 2 – L2 normalization (per-sample)
    if arr.ndim == 1:
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
    else:
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        arr = arr / norms
    return arr


# Keep old name for backward compatibility with main.py
def transform_features(features, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return normalize_features(features, mean, scale)
