import numpy as np
import librosa
from audio_service.utils.audio_loader import load_audio, get_duration


N_MFCC = 13


def extract_features(file_path: str) -> dict:
    """
    Extract a ~41-dimensional raw feature vector from an audio file.
    Normalization (StandardScaler + L2) is applied separately at index time.

    Features:
      - MFCC (13 × mean + std = 26)
      - Spectral Centroid  (mean + std = 2)
      - Spectral Bandwidth (mean + std = 2)
      - RMS Energy         (mean + std = 2)
      - Zero Crossing Rate (mean + std = 2)
      - Spectral Contrast  (7 bands × mean = 7)
    Total ≈ 41 features
    """
    y, sr = load_audio(file_path)

    # MFCC - 13 coefficients, mean + std = 26
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    # Spectral Centroid - mean + std = 2
    spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    sc_mean = np.mean(spec_centroid)
    sc_std = np.std(spec_centroid)

    # Spectral Bandwidth - mean + std = 2
    spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    sb_mean = np.mean(spec_bandwidth)
    sb_std = np.std(spec_bandwidth)

    # RMS Energy - mean + std = 2
    rms = librosa.feature.rms(y=y)
    rms_mean = np.mean(rms)
    rms_std = np.std(rms)

    # Zero Crossing Rate - mean + std = 2
    zcr = librosa.feature.zero_crossing_rate(y=y)
    zcr_mean = np.mean(zcr)
    zcr_std = np.std(zcr)

    # Spectral Contrast - 7 bands, mean = 7
    spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    sc_contrast_mean = np.mean(spec_contrast, axis=1)

    feature_vector = np.concatenate([
        mfcc_mean,
        mfcc_std,
        [sc_mean, sc_std],
        [sb_mean, sb_std],
        [rms_mean, rms_std],
        [zcr_mean, zcr_std],
        sc_contrast_mean,
    ])

    try:
        duration = get_duration(file_path)
    except Exception:
        duration = float(len(y)) / sr

    return {
        "features": feature_vector.tolist(),
        "duration": round(duration, 3),
        "sample_rate": sr,
    }
