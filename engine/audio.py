"""Audio energy drive for oanim. No new deps: ffmpeg decodes, numpy analyzes.

Usage:
    drive = AudioDrive("voiceover.wav")          # or Drive.sine(bpm=100)
    dots.drift(4.0, drive=drive)
Audio maps to flow strength + stamp brightness (see Scene._draw `energy`).
"""
import subprocess
import numpy as np


def _pcm_mono(path, sr=22050):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr),
           "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    if x.size == 0:
        raise ValueError(f"no audio decoded: {path}")
    return x, sr


class AudioDrive:
    """RMS-energy envelope 0..~1.5 sampled at video time t."""

    def __init__(self, path, sr=22050, win=0.12, gain=1.0):
        x, self.sr = _pcm_mono(path, sr)
        hop = max(1, int(sr * 0.02))
        w = max(1, int(sr * win))
        # RMS envelope, 20ms hops
        n = 1 + (max(0, len(x) - w) // hop)
        env = np.empty(n, np.float32)
        for i in range(n):
            s = x[i * hop:i * hop + w]
            env[i] = float(np.sqrt((s * s).mean()))
        env /= max(1e-6, np.percentile(env, 95))  # beats ~1.0, loud ~1.5
        self.env = np.clip(env, 0, 1.6).astype(np.float32)
        self.hop = hop / sr
        self.gain = float(gain)
        self.dur = len(x) / sr

    def energy(self, t):
        i = int(t / self.hop)
        if i >= len(self.env):
            return 0.0
        return float(self.env[i]) * self.gain


class SineDrive:
    """Dependency-free pulsing drive for tests / music-less videos."""

    def __init__(self, bpm=100.0, base=0.25, amp=0.75):
        self.w = 2 * np.pi * bpm / 60.0
        self.base, self.amp = base, amp

    def energy(self, t):
        return float(self.base + self.amp * (0.5 + 0.5 * np.sin(self.w * t)))
