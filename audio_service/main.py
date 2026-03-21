"""
Python Audio Service - Flask REST API
Exposes:
  POST /search   - extract features from uploaded audio, return top-5
  GET  /status   - DB stats
  GET  /health   - health check
"""

import os
import time
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure package imports work when run from project root
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_service.feature_extraction.extract_features import extract_features
from audio_service.feature_extraction.scaler_utils import load_scaler, transform_features
from audio_service.similarity.similarity_search import find_top_k, compute_precision_at_k
from audio_service.db.mongo_client import get_all_documents, get_count, get_instruments
from audio_service.classifier.instrument_classifier import predict_instrument, is_available as classifier_available

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac", "aiff", "m4a"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file format. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    suffix = "." + file.filename.rsplit(".", 1)[1].lower()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        file.save(tmp_file.name)
        tmp_file.close()

        t0 = time.perf_counter()

        # Extract features from query file
        query_info = extract_features(tmp_file.name)
        query_features = query_info["features"]

        # Normalize query with same scaler as dataset (for external input generalization)
        mean, scale = load_scaler()
        if mean is not None and scale is not None:
            query_features = transform_features(query_features, mean, scale).tolist()

        # Load all stored features from DB
        dataset = get_all_documents()

        if len(dataset) == 0:
            return jsonify({"error": "Database is empty. Run the feature extraction script first."}), 503

        # Find top-5 by cosine similarity (retrieval)
        top5 = find_top_k(query_features, dataset, top_k=5)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Instrument identification: use SVM classifier if available,
        # otherwise fall back to top-1 retrieval result
        if classifier_available():
            clf_result = predict_instrument(query_features)
            predicted_instrument = clf_result["instrument"]
            confidence = clf_result["confidence"]
            probabilities = clf_result["probabilities"]
        else:
            predicted_instrument = top5[0]["instrument"] if top5 else "unknown"
            confidence = top5[0]["similarity"] if top5 else 0.0
            probabilities = {}

        precision_at_5 = compute_precision_at_k(top5, predicted_instrument, k=5)

        return jsonify({
            "query": {
                "duration": query_info["duration"],
                "sample_rate": query_info["sample_rate"],
                "feature_dim": len(query_features),
            },
            "predicted_instrument": predicted_instrument,
            "confidence": confidence,
            "probabilities": probabilities,
            "precision_at_5": precision_at_5,
            "search_time_ms": elapsed_ms,
            "total_searched": len(dataset),
            "results": top5,
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
