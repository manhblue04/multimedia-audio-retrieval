"""
Cấu hình tập trung cho audio_service (spec v5).

Mọi hằng số dùng chung giữa feature extraction, classifier và scripts đều khai
báo ở đây để tránh "magic numbers" rải rác trong code.

v5 so với v4:
  • Bỏ Chroma STFT (24 dims) và Tonnetz (6 dims) — 2 nhóm này mã hoá hoà âm
    của bài nhạc đệm, không phải đặc tính nhạc cụ. Với file query từ bên ngoài
    (solo, không nhạc đệm) chúng trở thành noise chủ động làm giảm retrieval.
  • FEATURE_DIM: 153 → 123.
  • Pitch F0 dịch lên [119..122].

SAU KHI SỬA FILE NÀY, BẮT BUỘC PHẢI CHẠY LẠI:
    python scripts/extract_all_features.py
"""

# ── Audio loading ────────────────────────────────────────────────────────
SAMPLE_RATE = 22050         # mono, 22.05 kHz — đồng bộ với audio_loader.load_audio()

# ── MFCC / Feature extraction ─────────────────────────────────────────────
N_MFCC = 20

# Tổng số chiều của feature vector "thô" trả về từ _compute_features().
# Phải khớp chính xác với phần concat ở extract_features._compute_features().
#
#   MFCC mean+std (20+20)         = 40     [0..39]
#   Delta MFCC mean+std (20+20)   = 40     [40..79]
#   Delta-Delta MFCC mean (20)    = 20     [80..99]
#   Spectral Centroid mean+std    = 2      [100..101]
#   Spectral Bandwidth mean+std   = 2      [102..103]
#   Spectral Rolloff mean+std     = 2      [104..105]
#   Spectral Flatness mean+std    = 2      [106..107]
#   RMS Energy mean+std           = 2      [108..109]
#   Zero Crossing Rate mean+std   = 2      [110..111]
#   Spectral Contrast mean (7)    = 7      [112..118]
#   Pitch F0 mean+std+range       = 3      [119..121]
#   Voiced ratio                  = 1      [122]
#   ─────────────────────────────────────
#   TỔNG                          = 123
#
#   (Đã bỏ: Chroma STFT 24 dims + Tonnetz 6 dims = 30 dims không mang thông
#    tin nhạc cụ với file query từ bên ngoài domain IRMAS)
FEATURE_DIM = 123

# ── Feature groups — dùng cho visualization trung gian ───────────────────
# Mỗi group: {"name": str, "start": int, "end": int}  (end exclusive)
FEATURE_GROUPS = [
    {"name": "MFCC mean",          "start": 0,   "end": 20},
    {"name": "MFCC std",           "start": 20,  "end": 40},
    {"name": "Δ MFCC mean",        "start": 40,  "end": 60},
    {"name": "Δ MFCC std",         "start": 60,  "end": 80},
    {"name": "ΔΔ MFCC mean",       "start": 80,  "end": 100},
    {"name": "Spectral Centroid",  "start": 100, "end": 102},
    {"name": "Spectral Bandwidth", "start": 102, "end": 104},
    {"name": "Spectral Rolloff",   "start": 104, "end": 106},
    {"name": "Spectral Flatness",  "start": 106, "end": 108},
    {"name": "RMS Energy",         "start": 108, "end": 110},
    {"name": "ZCR",                "start": 110, "end": 112},
    {"name": "Spectral Contrast",  "start": 112, "end": 119},
    {"name": "Pitch F0",           "start": 119, "end": 123},
]

# ── Sliding window / query ───────────────────────────────────────────────
# Dataset IRMAS gồm các đoạn 3s nên window 3s là phù hợp.
QUERY_WINDOW_SEC = 3.0
HOP_SEC = 1.5

# ── Out-of-Distribution detection ────────────────────────────────────────
# Nếu cosine similarity cao nhất trong toàn bộ DB < ngưỡng này,
# hệ thống báo low_confidence = True.
OOD_THRESHOLD = 0.50

# ── Nhãn nhạc cụ ─────────────────────────────────────────────────────────
INSTRUMENTS = ["clarinet", "flute", "saxophone", "trumpet"]
