"""
Offline batch script: dataset → extract features → save to MongoDB + CSV.

Usage:
  python scripts/extract_all_features.py [--dataset-dir DATASET_DIR] [--workers N]

IRMAS folder mapping:
  cla → clarinet
  flu → flute
  sax → saxophone
  tru → trumpet
"""

import os
import sys
import csv
import time
import argparse
import numpy as np
import concurrent.futures
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sklearn.preprocessing import StandardScaler

from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import save_scaler, normalize_features
from audio_service.db.mongo_client import insert_document, get_count

IRMAS_MAP = {
    "clarinet": "clarinet",
    "flute": "flute",
    "saxophone": "saxophone",
    "trumpet": "trumpet",
}

AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aiff", ".m4a"}


def collect_files(dataset_dir: str) -> list:
    files = []
    for folder_name, instrument_name in IRMAS_MAP.items():
        folder_path = Path(dataset_dir) / folder_name
        if not folder_path.exists():
            print(f"[WARN] Folder not found: {folder_path}")
            continue
        for fp in sorted(folder_path.iterdir()):
            if fp.suffix.lower() in AUDIO_EXTENSIONS:
                files.append((str(fp), instrument_name, fp.name))
    return files


def process_one(args):
    """Extract features only - no DB insert. Returns data for scaler fit + insert."""
    file_path, instrument, file_name = args
    try:
        info = extract_features(file_path)
        return ("ok", instrument, file_name, info["features"], info["duration"], info["sample_rate"], file_path)
    except Exception as e:
        return ("err", instrument, file_name, str(e), None, None, None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default=str(ROOT / "dataset"),
        help="Path to the dataset root directory",
    )
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument(
        "--csv-out",
        default=str(ROOT / "features" / "audio_features.csv"),
        help="Path to output CSV file",
    )
    args = parser.parse_args()

    files = collect_files(args.dataset_dir)
    total = len(files)
    print(f"Found {total} audio files across {len(IRMAS_MAP)} instruments")

    if total == 0:
        print("No files found. Check --dataset-dir path.")
        return

    t0 = time.time()
    ok_count = 0
    err_count = 0
    csv_rows = []

    collected = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_one, f): f for f in files}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            if result[0] == "ok":
                collected.append(result[1:])  # instrument, fname, features, duration, sr, file_path
                ok_count += 1
                if i % 50 == 0 or i == total:
                    elapsed = time.time() - t0
                    print(f"[{i}/{total}] OK: {result[2]} | {elapsed:.1f}s elapsed")
            else:
                err_count += 1
                print(f"[{i}/{total}] ERR: {result[2]} → {result[3]}")

    if not collected:
        print("No data collected. Aborting.")
        return

    # Step 1: Fit StandardScaler on raw features
    X_raw = np.array([c[2] for c in collected], dtype=np.float64)
    scaler = StandardScaler()
    scaler.fit(X_raw)
    save_scaler(scaler.mean_, scaler.scale_)
    print(f"\nFitted StandardScaler, saved to features/scaler.npz")

    # Step 2: Apply StandardScaler + L2 normalize (unit-norm for cosine similarity)
    X_norm = normalize_features(X_raw, scaler.mean_, scaler.scale_)

    # Insert into MongoDB
    for i, c in enumerate(collected):
        instrument, fname, _, duration, sr, file_path = c
        doc = {
            "file_name": fname,
            "instrument": instrument,
            "duration": duration,
            "sample_rate": sr,
            "features": X_norm[i].tolist(),
            "file_path": file_path,
        }
        insert_document(doc)

    # Write CSV
    csv_path = Path(args.csv_out)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    feature_len = X_norm.shape[1]
    header = ["file_name", "instrument"] + [f"f{i}" for i in range(feature_len)]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i, c in enumerate(collected):
            row = [c[1], c[0]] + X_norm[i].tolist()
            writer.writerow(row)
    print(f"CSV saved to: {csv_path}")

    elapsed_total = time.time() - t0
    print(f"\nDone in {elapsed_total:.1f}s")
    print(f"  Success: {ok_count} / {total}")
    print(f"  Errors : {err_count}")
    print(f"  MongoDB count: {get_count()}")


if __name__ == "__main__":
    main()
