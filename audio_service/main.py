"""
Python Audio Service - Flask REST API (v4)
Exposes:
  POST /search   - extract features, sliding-window query, return top-5 + intermediate data
  GET  /status   - DB stats
  GET  /health   - health check

v4 thay đổi so với v3:
  • Sliding-window query: chia file dài thành các cửa sổ 3s (gối 1.5s),
    aggregate max similarity qua tất cả windows → khớp với độ dài IRMAS.
  • OOD detection: nếu best cosine < OOD_THRESHOLD → low_confidence = True.
  • Fix precision_at_5: nhận ground_truth từ form-field, không dùng predicted label.
  • Trả thêm "intermediate" trong response cho visualization trên frontend.
  • Features: 153D (thêm pitch F0 từ pYIN).
"""

import os
import re
import time
import tempfile
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_service.config import (
    QUERY_WINDOW_SEC, HOP_SEC, OOD_THRESHOLD, FEATURE_GROUPS, INSTRUMENTS,
)
from audio_service.feature_extraction.extract_features import extract_features_from_array
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.similarity.similarity_search import compute_precision_at_k
from audio_service.db.mongo_client import get_all_documents, get_count, get_instruments
from audio_service.utils.audio_loader import load_audio

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac", "aiff", "m4a"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _recording_id(filename: str) -> str:
    """Trích recording ID từ tên file IRMAS, ví dụ '0242' từ '004__[cla][nod][cla]0242__1.wav'.
    Dùng để loại bỏ clips trùng recording trong top-5 (tránh 3/5 slot cùng 1 bài nhạc).
    Nếu không match format IRMAS thì trả về tên file gốc."""
    m = re.search(r"(\d{4})__", filename)
    return m.group(1) if m else filename


def _build_windows(y: np.ndarray, sr: int) -> list:
    """
    Chia audio array thành các cửa sổ QUERY_WINDOW_SEC giây, gối HOP_SEC giây.
    Nếu file ngắn hơn 1 window thì dùng toàn bộ.
    Nếu file ngắn nhưng > nửa window, pad bằng zero rồi dùng.
    """
    window_samples = int(QUERY_WINDOW_SEC * sr)
    hop_samples = int(HOP_SEC * sr)

    if len(y) <= window_samples:
        # File ngắn hơn hoặc bằng 1 window — pad nếu cần, dùng toàn bộ
        if len(y) < window_samples:
            y_padded = np.zeros(window_samples, dtype=y.dtype)
            y_padded[:len(y)] = y
            return [y_padded]
        return [y]

    windows = []
    start = 0
    while start + window_samples <= len(y):
        windows.append(y[start:start + window_samples])
        start += hop_samples

    # Thêm window cuối căn-phải nếu còn phần đuôi đủ dài (≥ nửa window)
    remainder = len(y) - start
    if remainder >= window_samples // 2:
        windows.append(y[-window_samples:])

    return windows if windows else [y[:window_samples]]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/status", methods=["GET"])
def status():
    try:
        count = get_count()
        instruments = get_instruments()
        return jsonify({
            "total_documents": count,
            "instruments": instruments,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search", methods=["POST"])
def search():
    # ── Validate file ───────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file format. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    # Optional: ground truth instrument do người dùng chọn (dùng tính precision thật)
    # Gửi kèm trong form-data: ground_truth=clarinet|flute|saxophone|trumpet
    ground_truth = request.form.get("ground_truth", "").strip().lower()
    if ground_truth and ground_truth not in INSTRUMENTS:
        ground_truth = ""

    suffix = "." + file.filename.rsplit(".", 1)[1].lower()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        file.save(tmp_file.name)
        tmp_file.close()

        t0 = time.perf_counter()

        # ── Load audio ──────────────────────────────────────────────────
        y_full, sr = load_audio(tmp_file.name)
        full_duration = round(float(len(y_full)) / sr, 3)

        # ── Sliding-window feature extraction ──────────────────────────
        windows = _build_windows(y_full, sr)
        n_windows = len(windows)

        mean_scaler, scale_scaler = load_scaler()
        has_scaler = (mean_scaler is not None and scale_scaler is not None)

        # Trích raw features và normalized features cho mỗi window
        raw_feature_list = []
        norm_feature_list = []

        for w in windows:
            info = extract_features_from_array(w, sr)
            raw = np.array(info["features"], dtype=np.float64)
            raw_feature_list.append(raw)
            if has_scaler:
                norm = transform_features(raw, mean_scaler, scale_scaler)
            else:
                norm = raw.copy()
            norm_feature_list.append(norm)

        # Mảng numpy [n_windows x feature_dim]
        W = np.array(norm_feature_list, dtype=np.float64)  # shape (n_windows, D)

        # ── Load dataset ────────────────────────────────────────────────
        dataset = get_all_documents()
        if not dataset:
            return jsonify({"error": "Database is empty. Run the feature extraction script first."}), 503

        # ── Retrieval: cosine similarity matrix ─────────────────────────
        # Vì cả W và D đều đã L2-normalize (unit vectors), cosine = dot product
        D = np.array([doc["features"] for doc in dataset], dtype=np.float64)
        # [n_windows x n_docs]
        sim_matrix = W @ D.T

        # Per-doc: max similarity qua tất cả windows
        doc_max_sims = sim_matrix.max(axis=0)           # shape (n_docs,)
        # Per-window: max similarity qua tất cả docs
        window_max_sims = sim_matrix.max(axis=1).tolist()  # shape (n_windows,)

        # Sắp xếp kết quả — dedup theo recording ID để tránh 3/5 slot cùng 1 bài
        sorted_idx = np.argsort(doc_max_sims)[::-1]

        top5 = []
        seen_recordings = set()
        for idx in sorted_idx:
            if len(top5) >= 5:
                break
            doc = dataset[idx]
            rec_id = _recording_id(doc.get("file_name", ""))
            if rec_id in seen_recordings:
                continue
            seen_recordings.add(rec_id)
            top5.append({
                "file_name":   doc.get("file_name", ""),
                "instrument":  doc.get("instrument", "unknown"),
                "duration":    doc.get("duration", 0),
                "sample_rate": doc.get("sample_rate", 22050),
                "similarity":  round(float(doc_max_sims[idx]), 6),
            })

        # ── OOD detection ───────────────────────────────────────────────
        best_sim = top5[0]["similarity"] if top5 else 0.0
        low_confidence = best_sim < OOD_THRESHOLD

        # ── Precision@5 ──────────────────────────────────────────────────
        # Chỉ tính khi có ground truth thật (do người dùng cung cấp).
        # KHÔNG dùng predicted_instrument làm ground truth — tránh circular logic.
        if ground_truth:
            precision_at_5 = compute_precision_at_k(top5, ground_truth, k=5)
        else:
            precision_at_5 = None

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        # ── Intermediate data ───────────────────────────────────────────
        # Dùng window đầu tiên cho visualization (đại diện cho query)
        raw_first = raw_feature_list[0].tolist()
        norm_first = norm_feature_list[0].tolist()

        # Phân phối similarity toàn DB (dùng window có sim cao nhất với mỗi doc)
        # Gửi tất cả để frontend vẽ histogram; sort giảm dần
        all_sims_sorted = []
        for idx in sorted_idx:
            all_sims_sorted.append({
                "similarity": round(float(doc_max_sims[idx]), 4),
                "instrument": dataset[idx].get("instrument", "unknown"),
            })

        # Summary per feature group (mean absolute value) cho bar chart
        def _group_summary(features: list) -> list:
            arr = np.array(features)
            return [
                {
                    "name": g["name"],
                    "raw_abs_mean": round(float(np.mean(np.abs(
                        np.array(raw_first[g["start"]:g["end"]])
                    ))), 4),
                    "norm_abs_mean": round(float(np.mean(np.abs(
                        arr[g["start"]:g["end"]]
                    ))), 4),
                }
                for g in FEATURE_GROUPS
            ]

        intermediate = {
            "raw_features":        raw_first,
            "normalized_features": norm_first,
            "feature_groups":      FEATURE_GROUPS,
            "feature_group_summary": _group_summary(norm_first),
            "windows_count":       n_windows,
            "window_max_similarities": [round(s, 4) for s in window_max_sims],
            "all_similarities":    all_sims_sorted,
        }

        return jsonify({
            "query": {
                "duration":      full_duration,
                "sample_rate":   sr,
                "feature_dim":   len(norm_first),
                "windows_count": n_windows,
            },
            "precision_at_5":  precision_at_5,
            "low_confidence":  low_confidence,
            "ood_threshold":   OOD_THRESHOLD,
            "search_time_ms":  elapsed_ms,
            "total_searched":  len(dataset),
            "results":         top5,
            "intermediate":    intermediate,
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
    finally:
        try:
            os.unlink(tmp_file.name)
        except Exception:
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PYTHON_SERVICE_PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
