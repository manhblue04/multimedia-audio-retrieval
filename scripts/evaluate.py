"""
Đánh giá retrieval trên một sample dataset.

Chạy:
    python scripts/evaluate.py [--samples N]

Output:
  • Acc@1 và P@5 per nhạc cụ
  • Confusion matrix (top-1 prediction)
"""
import sys
import re
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.metrics import confusion_matrix

from audio_service.config import INSTRUMENTS
from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.db.mongo_client import get_all_documents
from audio_service.similarity.similarity_search import find_top_k

ROOT = Path(__file__).resolve().parent.parent


def base_recording_id(fname: str) -> str:
    """Trích recording ID (ví dụ '0393' từ '[flu][cla]0393__2.wav')."""
    m = re.search(r"(\d{4})__", fname)
    return m.group(1) if m else fname


def _format_cm(cm: np.ndarray, labels: list) -> str:
    width = max(len(lbl) for lbl in labels) + 2
    header = " " * width + "".join(f"{lbl:>{width}}" for lbl in labels)
    rows = [header]
    for lbl, row in zip(labels, cm):
        rows.append(f"{lbl:<{width}}" + "".join(f"{v:>{width}}" for v in row))
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=20,
                        help="Số file đánh giá mỗi nhạc cụ")
    args = parser.parse_args()

    mean, scale = load_scaler()
    if mean is None:
        raise SystemExit("scaler.npz chưa tồn tại. Chạy extract_all_features.py trước.")

    dataset = get_all_documents()
    if not dataset:
        raise SystemExit("MongoDB rỗng. Chạy extract_all_features.py trước.")
    print(f"DB size: {len(dataset)} documents")
    print(f"Feature dim: {len(dataset[0]['features'])}D\n")

    retrieval_res = defaultdict(lambda: {"top1": 0, "p5": 0.0, "total": 0})
    ret_true: list = []
    ret_pred: list = []

    for instrument in INSTRUMENTS:
        folder = ROOT / "dataset" / instrument
        if not folder.exists():
            print(f"[WARN] Folder không tồn tại: {folder}")
            continue
        files = sorted(folder.glob("*.wav"))[: args.samples]

        for f in files:
            try:
                info = extract_features(str(f))
                qf = transform_features(info["features"], mean, scale).tolist()

                # Loại same-recording clips để tránh trivial match
                base_id = base_recording_id(f.name)
                top5 = find_top_k(qf, dataset, top_k=10)
                top5_clean = [
                    r for r in top5
                    if base_recording_id(r["file_name"]) != base_id
                ][:5]

                if top5_clean:
                    pred = top5_clean[0]["instrument"]
                    p5 = sum(1 for r in top5_clean if r["instrument"] == instrument) / len(top5_clean)
                    retrieval_res[instrument]["top1"] += int(pred == instrument)
                    retrieval_res[instrument]["p5"] += p5
                    retrieval_res[instrument]["total"] += 1
                    ret_true.append(instrument)
                    ret_pred.append(pred)
            except Exception as e:
                print(f"  ERR {f.name}: {e}")

    # ── Bảng tổng hợp ────────────────────────────────────────────────────
    print(f"{'Instrument':<12} {'Acc@1':>7} {'P@5':>7} {'N':>5}")
    print("-" * 32)
    total_top1 = total_p5 = total_n = 0
    for instr in INSTRUMENTS:
        r = retrieval_res[instr]
        n = r["total"]
        if n == 0:
            continue
        print(f"{instr:<12} {r['top1']/n:>6.1%} {r['p5']/n:>6.1%} {n:>5}")
        total_top1 += r["top1"]
        total_p5 += r["p5"]
        total_n += n

    print("-" * 32)
    if total_n:
        print(f"{'Overall':<12} {total_top1/total_n:>6.1%} {total_p5/total_n:>6.1%} {total_n:>5}")

    # ── Confusion matrix ────────────────────────────────────────────────
    if ret_true:
        cm = confusion_matrix(ret_true, ret_pred, labels=INSTRUMENTS)
        print("\nConfusion Matrix (rows=true, cols=predicted):")
        print(_format_cm(cm, INSTRUMENTS))

    print("\nGhi chú: Retrieval = top-1 cosine similarity, đã loại same-recording clips.")


if __name__ == "__main__":
    main()
