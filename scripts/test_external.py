"""
Test retrieval trên 12 file IRMAS test set (out-of-distribution).

Chạy:
    python scripts/test_external.py

Đọc file từ dataset/test_samples/, query DB, in kết quả chi tiết.
"""
import sys
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.db.mongo_client import get_all_documents
from audio_service.config import QUERY_WINDOW_SEC, HOP_SEC
from audio_service.utils.audio_loader import load_audio
from audio_service.feature_extraction.extract_features import extract_features_from_array

GT_MAP = {"cla": "clarinet", "flu": "flute", "sax": "saxophone", "tru": "trumpet"}
INSTRUMENTS = ["clarinet", "flute", "saxophone", "trumpet"]


def build_windows(y, sr):
    ws = int(QUERY_WINDOW_SEC * sr)
    hs = int(HOP_SEC * sr)
    if len(y) <= ws:
        return [y if len(y) == ws else np.pad(y, (0, ws - len(y)))]
    windows = []
    start = 0
    while start + ws <= len(y):
        windows.append(y[start:start + ws])
        start += hs
    if len(y) - start >= ws // 2:
        windows.append(y[-ws:])
    return windows or [y[:ws]]


def query_db(file_path, dataset, mean, scale):
    y, sr = load_audio(str(file_path))
    windows = build_windows(y, sr)

    norm_vecs = []
    for w in windows:
        info = extract_features_from_array(w, sr)
        nv = transform_features(info["features"], mean, scale)
        norm_vecs.append(nv)

    W = np.array(norm_vecs)
    D = np.array([doc["features"] for doc in dataset])
    sim_matrix = W @ D.T
    doc_max_sims = sim_matrix.max(axis=0)
    sorted_idx = np.argsort(doc_max_sims)[::-1]

    top5 = []
    for idx in sorted_idx:
        if len(top5) >= 5:
            break
        doc = dataset[idx]
        top5.append({
            "instrument": doc["instrument"],
            "file_name":  doc["file_name"],
            "similarity": round(float(doc_max_sims[idx]), 4),
        })
    return top5, round(float(len(y) / sr), 1), len(windows)


def main():
    mean, scale = load_scaler()
    if mean is None:
        raise SystemExit("scaler.npz chưa tồn tại. Chạy extract_all_features.py trước.")

    dataset = get_all_documents()
    print(f"DB: {len(dataset)} documents | Feature dim: {len(dataset[0]['features'])}D\n")

    test_dir = ROOT / "dataset" / "test_samples"
    files = sorted(test_dir.glob("*.wav"))
    if not files:
        raise SystemExit(f"Không tìm thấy file trong {test_dir}")

    print(f"{'':2} {'GT':10} {'File':38} {'Dur':5} {'Win':3} {'Top-1':10} {'P@5':5}  Top-5")
    print("-" * 110)

    stats = defaultdict(lambda: {"top1": 0, "p5": 0.0, "n": 0})
    correct = total = 0

    for f in files:
        code = f.name[1:4]
        gt = GT_MAP.get(code, "unknown")
        if gt == "unknown":
            continue

        try:
            top5, dur, n_win = query_db(f, dataset, mean, scale)
            top1 = top5[0]["instrument"]
            top5_instrs = [r["instrument"] for r in top5]
            p5 = sum(1 for r in top5_instrs if r == gt) / 5
            hit = "✓" if top1 == gt else "✗"

            print(f"{hit}  {gt:10} {f.name[6:44]:<38} {dur:4.1f}s {n_win:2}w  {top1:10} {p5:4.0%}  "
                  f"{', '.join(r[:3] for r in top5_instrs)}")

            stats[gt]["top1"] += int(top1 == gt)
            stats[gt]["p5"] += p5
            stats[gt]["n"] += 1
            if top1 == gt:
                correct += 1
            total += 1
        except Exception as e:
            print(f"✗  {gt:10} {f.name[6:44]:<38} ERR: {e}")

    print("-" * 110)
    print(f"\n{'Instrument':<12} {'Acc@1':>7} {'P@5':>7} {'N':>4}")
    print("-" * 34)
    for instr in INSTRUMENTS:
        s = stats[instr]
        if s["n"] == 0:
            continue
        print(f"{instr:<12} {s['top1']/s['n']:>6.0%} {s['p5']/s['n']:>6.0%} {s['n']:>4}")
    print("-" * 34)
    if total:
        total_p5 = sum(s["p5"] for s in stats.values())
        print(f"{'Overall':<12} {correct/total:>6.0%} {total_p5/total:>6.0%} {total:>4}")


if __name__ == "__main__":
    main()
