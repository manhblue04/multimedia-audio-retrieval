import librosa
import numpy as np


def load_audio(file_path: str, sr: int = 22050, duration: float = None):
    """Load an audio file and return the signal and sample rate."""
    y, sr = librosa.load(file_path, sr=sr, duration=duration, mono=True)
    return y, sr


def get_duration(file_path: str) -> float:
    """Return duration of audio file in seconds."""
    return librosa.get_duration(path=file_path)
