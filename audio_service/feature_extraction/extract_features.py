"""
Trích xuất feature vector 123 chiều cho bài toán nhận dạng nhạc cụ hơi
(clarinet, flute, saxophone, trumpet) — spec v5.

Thay đổi so với v4 (153D):
  • Bỏ Chroma STFT mean+std (24 dims) và Tonnetz mean (6 dims).
    Lý do: hai nhóm này mã hoá hoà âm của bài nhạc đang phát, không phải
    đặc tính nhạc cụ. IRMAS files có nhạc đệm (piano/guitar/bass) nên
    Chroma/Tonnetz phản ánh key/chord của bài nhạc, không phải timbre nhạc cụ.
    Với file query từ ngoài (solo, không đệm), các chiều này là nhiễu thuần.
  • FEATURE_DIM: 153 → 123. Pitch F0 dịch lên [119..122].

Hai entry-point (extract_features từ file, extract_features_from_array từ
np.ndarray) đều dùng chung _compute_features() để đảm bảo thứ tự và logic
KHÔNG BAO GIỜ lệch nhau — scaler phụ thuộc trực tiếp vào thứ tự này.

SAU KHI SỬA FILE NÀY, BẮT BUỘC PHẢI CHẠY LẠI:
    python scripts/extract_all_features.py   (rebuild 123D features + scaler mới)
"""
import numpy as np
import librosa

from audio_service.config import N_MFCC, FEATURE_DIM
from audio_service.utils.audio_loader import load_audio, get_duration


def _compute_features(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Trích 153-dim raw feature vector từ audio array.

    THỨ TỰ FEATURE TRONG VECTOR LÀ HỢP ĐỒNG VỚI scaler.npz và classifier.pkl —
    KHÔNG được thay đổi mà không re-run extract_all_features.py + train_classifier.py.
    """
    # ── MFCC (n=20): mean + std ────────────────────────────────────────
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    # ── Delta MFCC: mean + std ─────────────────────────────────────────
    # Tốc độ thay đổi âm sắc (articulation) — tách clarinet ↔ saxophone.
    delta = librosa.feature.delta(mfcc)
    delta_mean = np.mean(delta, axis=1)
    delta_std = np.std(delta, axis=1)

    # ── Delta-Delta MFCC: mean only ────────────────────────────────────
    # Gia tốc thay đổi — bắt onset/offset (trumpet sắc, flute mềm).
    delta2 = librosa.feature.delta(mfcc, order=2)
    delta2_mean = np.mean(delta2, axis=1)

    # ── Spectral Centroid: mean + std ──────────────────────────────────
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)
    sc_mean = float(np.mean(sc)); sc_std = float(np.std(sc))

    # ── Spectral Bandwidth: mean + std ─────────────────────────────────
    sb = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    sb_mean = float(np.mean(sb)); sb_std = float(np.std(sb))

    # ── Spectral Rolloff: mean + std ───────────────────────────────────
    # Tần số mà 85% năng lượng nằm bên dưới — trumpet "sáng" → rolloff cao.
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    rolloff_mean = float(np.mean(rolloff)); rolloff_std = float(np.std(rolloff))

    # ── Spectral Flatness: mean + std ──────────────────────────────────
    # Tonal vs noisy — flute breathy → flatness cao.
    flatness = librosa.feature.spectral_flatness(y=y)
    flatness_mean = float(np.mean(flatness)); flatness_std = float(np.std(flatness))

    # ── RMS Energy: mean + std ─────────────────────────────────────────
    rms = librosa.feature.rms(y=y)
    rms_mean = float(np.mean(rms)); rms_std = float(np.std(rms))

    # ── Zero Crossing Rate: mean + std ─────────────────────────────────
    zcr = librosa.feature.zero_crossing_rate(y=y)
    zcr_mean = float(np.mean(zcr)); zcr_std = float(np.std(zcr))

    # ── Spectral Contrast (7 bands): mean only ─────────────────────────
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = np.mean(contrast, axis=1)

    # ── Pitch F0 via pYIN (4 dims) ─────────────────────────────────────
    # pYIN: probabilistic YIN — ổn định hơn YIN với âm thanh nhạc cụ hơi.
    # fmin/fmax bao phủ toàn bộ dải nhạc cụ hơi bộ hơi:
    #   C2 (~65 Hz)  = dưới dải trumpet thấp nhất
    #   C7 (~2093 Hz) = trên dải flute cao nhất
    f0, voiced_flag, _voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),   # ~65 Hz
        fmax=librosa.note_to_hz("C7"),   # ~2093 Hz
        sr=sr,
    )
    # Lọc các frame có voiced=True và f0 hợp lệ (không NaN)
    valid_mask = voiced_flag & ~np.isnan(f0)
    voiced_f0 = f0[valid_mask]

    if len(voiced_f0) > 0:
        f0_mean = float(np.mean(voiced_f0))
        f0_std = float(np.std(voiced_f0))
        f0_range = float(np.max(voiced_f0) - np.min(voiced_f0))
    else:
        # Không phát hiện được pitch (file quá nhiễu hoặc không tonal)
        f0_mean = 0.0
        f0_std = 0.0
        f0_range = 0.0

    # Tỷ lệ frame có pitch — phân biệt âm tonal (flute/trumpet ~0.9)
    # vs breathy (flute đặc biệt ở các nốt thấp ~0.6-0.7)
    voiced_ratio = float(np.mean(voiced_flag.astype(np.float32)))

    vec = np.concatenate([
        mfcc_mean, mfcc_std,                      # 40   [0..39]
        delta_mean, delta_std,                    # 40   [40..79]
        delta2_mean,                              # 20   [80..99]
        [sc_mean, sc_std],                        # 2    [100..101]
        [sb_mean, sb_std],                        # 2    [102..103]
        [rolloff_mean, rolloff_std],              # 2    [104..105]
        [flatness_mean, flatness_std],            # 2    [106..107]
        [rms_mean, rms_std],                      # 2    [108..109]
        [zcr_mean, zcr_std],                      # 2    [110..111]
        contrast_mean,                            # 7    [112..118]
        [f0_mean, f0_std, f0_range, voiced_ratio] # 4    [119..122]
    ])  # tổng = 123

    assert len(vec) == FEATURE_DIM, (
        f"Feature dim mismatch: got {len(vec)}, expected {FEATURE_DIM}. "
        f"Kiểm tra lại thứ tự concat trong _compute_features()."
    )
    return vec


def extract_features(file_path: str) -> dict:
    """Trích feature từ file âm thanh trên đĩa."""
    y, sr = load_audio(file_path)
    vec = _compute_features(y, sr)
    try:
        duration = get_duration(file_path)
    except Exception:
        duration = float(len(y)) / sr
    return {
        "features": vec.tolist(),
        "duration": round(duration, 3),
        "sample_rate": sr,
    }


def extract_features_from_array(y: np.ndarray, sr: int) -> dict:
    """
    Trích feature từ numpy array đã load sẵn.
    Dùng cho sliding-window query — tránh load file nhiều lần.
    """
    vec = _compute_features(y, sr)
    return {
        "features": vec.tolist(),
        "duration": round(float(len(y)) / sr, 3),
        "sample_rate": sr,
    }
