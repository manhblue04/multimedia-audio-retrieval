"""
Evaluate retrieval accuracy on a sample of dataset files.
For each query, exclude all clips from the same base recording to avoid trivial matches.
"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import defaultdict
from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.db.mongo_client import get_all_documents
from audio_service.similarity.similarity_search import find_top_k
from audio_service.classifier.instrument_classifier import predict_instrument, is_available as clf_available

ROOT = Path(__file__).resolve().parent.parent
INSTRUMENTS = ["clarinet", "flute", "saxophone", "trumpet"]
SAMPLES_PER_INSTRUMENT = 20

mean, scale = load_scaler()
assert mean is not None, "Run extract_all_features.py first to generate scaler.npz"

dataset = get_all_documents()
print(f"DB size: {len(dataset)} documents\n")


def base_recording_id(fname: str) -> str:
    """Extract the recording ID (e.g. '0393' from '[flu][cla]0393__2.wav')."""
    m = re.search(r'(\d{4})__', fname)
    return m.group(1) if m else fname


retrieval_res = defaultdict(lambda: {"top1": 0, "p5": 0, "total": 0})
svm_res = defaultdict(lambda: {"correct": 0, "total": 0})

use_svm = clf_available()

for instrument in INSTRUMENTS:
    folder = ROOT / "dataset" / instrument
    files = sorted(folder.glob("*.wav"))[:SAMPLES_PER_INSTRUMENT]

    for f in files:
        try:
            info = extract_features(str(f))
            qf = transform_features(info["features"], mean, scale).tolist()

            # Retrieval: cosine similarity, exclude same recording
            base_id = base_recording_id(f.name)
            top5 = find_top_k(qf, dataset, top_k=5, exclude_file=None)
            top5_clean = [r for r in top5 if base_recording_id(r["file_name"]) != base_id][:5]
            if top5_clean:
                retrieval_pred = top5_clean[0]["instrument"]
                p5 = sum(1 for r in top5_clean if r["instrument"] == instrument) / len(top5_clean)
                retrieval_res[instrument]["top1"] += int(retrieval_pred == instrument)
                retrieval_res[instrument]["p5"] += p5
                retrieval_res[instrument]["total"] += 1

            # SVM prediction
            if use_svm:
                svm_pred = predict_instrument(qf)["instrument"]
                svm_res[instrument]["correct"] += int(svm_pred == instrument)
                svm_res[instrument]["total"] += 1

        except Exception as e:
            print(f"  ERR {f.name}: {e}")

print(f"{'':12} {'--- Retrieval ---':^20} {'--- SVM ---':^13}")
print(f"{'Instrument':<12} {'Acc@1':>7} {'P@5':>7}   {'Acc':>7} {'N':>5}")
print("-" * 45)
total_ret = total_p5 = total_svm = total_n = 0
for instr in INSTRUMENTS:
    r = retrieval_res[instr]
    s = svm_res[instr]
    n = r["total"]
    if n == 0:
        continue
    ret_acc = r["top1"] / n
    p5 = r["p5"] / n
    svm_acc = s["correct"] / s["total"] if s["total"] else 0
    print(f"{instr:<12} {ret_acc:>6.1%} {p5:>6.1%}   {svm_acc:>6.1%} {n:>5}")
    total_ret += r["top1"]; total_p5 += r["p5"]
    total_svm += s["correct"]; total_n += n

svm_total_correct = sum(svm_res[i]["correct"] for i in INSTRUMENTS)
svm_total_n = sum(svm_res[i]["total"] for i in INSTRUMENTS)
print("-" * 45)
print(f"{'Overall':<12} {total_ret/total_n:>6.1%} {total_p5/total_n:>6.1%}   {svm_total_correct/svm_total_n:>6.1%} {total_n:>5}")
print()
print("Retrieval = top-1 cosine similarity (excluding same recording)")
print("SVM (above) = on training data [optimistic] | CV = 79.5% [honest]")
