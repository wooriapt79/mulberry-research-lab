"""
koda_preprocessor.py — Mulberry Pi ARS Voice Preprocessor
Extracted from re-eul/mulberry-demo app.py (lines 354-383)
CTO: Koda | Issue: mulberry-research-lab#163

Pipeline:
    audio (float64 ndarray) → denoise → bandpass 300-3400Hz → float64 ndarray
"""

try:
    import noisereduce as nr
    from scipy import signal as scipy_signal
    KODA_AVAILABLE = True
except ImportError:
    KODA_AVAILABLE = False


class KodaPreprocessor:
    """
    Koda's Voice Preprocessing Layer (CPU, no GPU required)
    Front-layer for Whisper ASR — Telephone-band optimized

    Stage 1: Stationary Noise Reduction  (noisereduce)
    Stage 2: Bandpass Filter 300-3400 Hz (scipy Butterworth 4th order)

    Usage:
        koda = KodaPreprocessor(sr=16000)
        cleaned = koda.process(audio_array.astype('float64'))
    """

    def __init__(self, sr: int = 16000):
        self.sr = sr

    def denoise(self, audio):
        if not KODA_AVAILABLE:
            return audio
        return nr.reduce_noise(y=audio, sr=self.sr, stationary=True, prop_decrease=0.8)

    def bandpass(self, audio):
        if not KODA_AVAILABLE:
            return audio
        nyquist = self.sr / 2
        low, high = 300 / nyquist, 3400 / nyquist
        b, a = scipy_signal.butter(4, [low, high], btype='band')
        return scipy_signal.filtfilt(b, a, audio)

    def process(self, audio):
        """Denoise + Bandpass. Peak normalization is handled by the caller pipeline."""
        audio = self.denoise(audio)
        audio = self.bandpass(audio)
        return audio


if __name__ == "__main__":
    import numpy as np
    import soundfile as sf
    import sys

    if len(sys.argv) < 2:
        print("Usage: python koda_preprocessor.py <input.wav> [output.wav]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "koda_output.wav"

    audio, sr = sf.read(in_path, dtype='float64')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    koda = KodaPreprocessor(sr=sr)
    result = koda.process(audio)

    peak = abs(result).max()
    if peak > 0:
        result = result / peak * 0.95

    sf.write(out_path, result.astype('float32'), sr)
    print(f"Done: {out_path} (sr={sr}Hz, samples={len(result)})")
