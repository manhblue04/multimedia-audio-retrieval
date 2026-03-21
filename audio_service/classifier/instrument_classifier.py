"""
SVM-based instrument classifier.
Loaded once at startup, used to predict instrument from normalized features.
"""
import numpy as np
from pathlib import Path

CLASSIFIER_PATH = Path(__file__).resolve().parents[2] / "features" / "classifier.pkl"
LABEL_ENCODER_PATH = Path(__file__).resolve().parents[2] / "features" / "label_encoder.pkl"

_clf = None
_le = None


def _load():
    global _clf, _le
    if _clf is None:
        import joblib
        _clf = joblib.load(CLASSIFIER_PATH)
        _le = joblib.load(LABEL_ENCODER_PATH)


def predict_instrument(normalized_features: list) -> dict:
    """
    Predict instrument from a normalized feature vector.
    Uses argmax(predict_proba) so that instrument and confidence are always consistent.
    (SVC.predict uses decision_function which can differ from predict_proba due to Platt scaling.)
    """
    _load()
    x = np.array(normalized_features, dtype=np.float64).reshape(1, -1)
    probas = _clf.predict_proba(x)[0]
    pred_idx = int(np.argmax(probas))
    instrument = _le.inverse_transform([pred_idx])[0]
    prob_dict = {str(cls): round(float(p), 4) for cls, p in zip(_le.classes_, probas)}
    return {
        "instrument": instrument,
        "confidence": round(float(probas[pred_idx]), 4),
        "probabilities": prob_dict,
    }


def is_available() -> bool:
    return CLASSIFIER_PATH.exists() and LABEL_ENCODER_PATH.exists()
