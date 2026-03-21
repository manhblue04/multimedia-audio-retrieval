"""
Train a SVM classifier on normalized audio features.
Saves model to features/classifier.pkl.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
import joblib

from audio_service.db.mongo_client import get_all_documents

ROOT = Path(__file__).resolve().parent.parent
CLASSIFIER_PATH = ROOT / "features" / "classifier.pkl"
LABEL_ENCODER_PATH = ROOT / "features" / "label_encoder.pkl"

print("Loading features from DB...")
docs = get_all_documents()
print(f"  {len(docs)} documents loaded")

X = np.array([d["features"] for d in docs], dtype=np.float64)
y_str = np.array([d["instrument"] for d in docs])

le = LabelEncoder()
y = le.fit_transform(y_str)
print(f"  Classes: {list(le.classes_)}")

# Cross-validate first
print("\nCross-validating SVM (5-fold)...")
clf = SVC(kernel="rbf", C=10, gamma="scale", probability=True)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
print(f"  CV Accuracy: {scores.mean():.1%} ± {scores.std():.1%}")

# Train on full dataset
print("\nTraining final classifier on full dataset...")
clf.fit(X, y)

# Save
joblib.dump(clf, CLASSIFIER_PATH)
joblib.dump(le, LABEL_ENCODER_PATH)
print(f"  Saved classifier to: {CLASSIFIER_PATH}")
print(f"  Saved label encoder to: {LABEL_ENCODER_PATH}")
print("\nDone.")
