"""Quick end-to-end test of the search pipeline."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.db.mongo_client import get_all_documents, get_count
from audio_service.similarity.similarity_search import find_top_k, compute_precision_at_k

ROOT = Path(__file__).resolve().parent.parent
test_file = next((ROOT / "dataset" / "flute").glob("*.wav"))
print(f"Query file: {test_file.name}")

info = extract_features(str(test_file))
query_features = info["features"]

mean, scale = load_scaler()
if mean is not None and scale is not None:
    query_features = transform_features(query_features, mean, scale).tolist()
    print("Applied scaler normalization")
print(f"Feature dim: {len(query_features)}, duration: {info['duration']}s")

dataset = get_all_documents()
print(f"DB size: {len(dataset)} documents")

top5 = find_top_k(query_features, dataset, top_k=5, exclude_file=test_file.name)
precision = compute_precision_at_k(top5, "flute")

print(f"\nTop 5 results:")
for i, r in enumerate(top5, 1):
    print(f"  {i}. [{r['instrument']:10}] {r['file_name']} — similarity: {r['similarity']:.4f}")

predicted = top5[0]["instrument"] if top5 else "unknown"
print(f"\nPredicted (top-1): {predicted}  (ground truth: flute)")
print(f"Precision@5: {precision}")
print(f"Correct: {predicted == 'flute'}")
