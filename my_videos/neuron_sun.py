"""NEURON SUN — void drift -> chase -> neuron flash -> sheet -> scatter -> solar system.

Run:  ./oanim render my_videos/neuron_sun.py --mode preview   # check
      ./oanim render my_videos/neuron_sun.py --mode draft     # keep
      ./oanim render my_videos/neuron_sun.py --mode final     # 1080p
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import engine.api as A
from engine.api import Video, Shape


class Neuron(Shape):
    """A nerve cell: dense soma ball + dendrite arms growing outward."""

    def __init__(self, arms=11, seed=7):
        self.arms, self.seed = arms, seed

    def points(self, n, seed=7):
        rng = np.random.default_rng(seed)
        cx, cy, R = A.W / 2, A.H / 2, min(A.W, A.H)
        pts, ord_ = [], []
        ns = n // 6  # soma first (kept small: dense balls over-bake white)
        a = rng.random(ns) * 2 * np.pi
        r = np.abs(rng.normal(0, R * 0.06, ns))
        pts.append(np.stack([cx + r * np.cos(a),
                             cy + r * np.sin(a) * 0.9], axis=1))
        ord_.append(np.zeros(ns, np.float32))
        rest, per, rem = n - ns, (n - ns) // self.arms, (n - ns) % self.arms
        for k in range(self.arms):
            m = per + (1 if k < rem else 0)
            ang = 2 * np.pi * k / self.arms + rng.normal(0, 0.2)
            L = R * rng.uniform(0.16, 0.28)
            steps = np.linspace(0, 1, m).astype(np.float32)
            th = ang + np.cumsum(rng.normal(0, 0.06, m)) * 0.5
            rr = steps * L
            pts.append(np.stack([cx + rr * np.cos(th) + rng.normal(0, 2, m),
                                 cy + rr * np.sin(th) * 0.9 + rng.normal(0, 2, m)],
                                axis=1))
            ord_.append(steps * 0.9 + 0.1)  # arms grow outward after soma
        self.order = np.ascontiguousarray(np.concatenate(ord_).astype(np.float32))
        return np.ascontiguousarray(np.concatenate(pts).astype(np.float32))


class PlaneSheet(Shape):
    """A flat sheet of dots — top edge reveals first, like unrolling."""

    def __init__(self, seed=8):
        self.seed = seed

    def points(self, n, seed=8):
        rng = np.random.default_rng(seed)
        cx, cy = A.W / 2, A.H / 2
        w, h = A.W * 0.72, min(A.H * 0.30, 200 * min(A.W, A.H) / 540.0)
        xs = rng.uniform(cx - w / 2, cx + w / 2, n)
        ys = rng.uniform(cy - h / 2, cy + h / 2, n) + rng.normal(0, 2.5, n)
        self.order = np.ascontiguousarray(
            ((ys - (cy - h / 2)) / h).astype(np.float32))
        return np.ascontiguousarray(np.stack([xs, ys], axis=1).astype(np.float32))


class SunSystem(Shape):
    """A sun (dense ball) + ring dust + 3 planets, revealed inside-out."""

    def __init__(self, seed=9):
        self.seed = seed

    def points(self, n, seed=9):
        rng = np.random.default_rng(seed)
        cx, cy, R = A.W / 2, A.H / 2, min(A.W, A.H)
        pts, ord_ = [], []
        nsun = int(n * 0.45)  # the sun
        a = rng.random(nsun) * 2 * np.pi
        r = np.sqrt(rng.random(nsun)) * R * 0.10
        pts.append(np.stack([cx + r * np.cos(a),
                             cy + r * np.sin(a) * 0.95], axis=1))
        ord_.append(np.full(nsun, rng.random(nsun) * 0.2, np.float32))
        rings = [(0.19, 0.10, 0.30), (0.28, 0.075, 0.55), (0.37, 0.055, 0.80)]
        per = (n - nsun) // len(rings)
        for i, (rr, share, base) in enumerate(rings):
            m = per + ((n - nsun) % len(rings) if i == 0 else 0)
            mring = int(m * (1 - share))
            # thin ring dust
            a = rng.random(mring) * 2 * np.pi
            r = rr * R + rng.normal(0, R * 0.008, mring)
            pts.append(np.stack([cx + r * np.cos(a),
                                 cy + r * np.sin(a) * 0.95], axis=1))
            ord_.append(np.full(mring, base, np.float32))
            # the planet: small dense ball sitting on the ring
            mp = m - mring
            pa = rng.uniform(0, 2 * np.pi)
            px, py = cx + rr * R * np.cos(pa), cy + rr * R * np.sin(pa) * 0.95
            pr = R * (0.030 - i * 0.005)
            a = rng.random(mp) * 2 * np.pi
            r = np.sqrt(rng.random(mp)) * pr
            pts.append(np.stack([px + r * np.cos(a),
                                 py + r * np.sin(a)], axis=1))
            ord_.append(np.full(mp, base + 0.1, np.float32))
        self.order = np.ascontiguousarray(np.concatenate(ord_).astype(np.float32))
        return np.ascontiguousarray(np.concatenate(pts).astype(np.float32))


class NeuronSun(Video):
    dots = 1800
    seed = 7

    def build(self):
        self.drift(5.0)                          # void wandering
        self.follow(Neuron(arms=11), 3.0)        # gather + chase into neuron
        self.rest(1.2)                           # neuron flash
        self.grow(PlaneSheet(), 2.4, wave=1.0)   # dissolve to sheet
        self.rest(0.8)
        self.burst(1.2)                          # burst
        self.grow(SunSystem(), 3.0, wave=1.0)    # solar system
        self.rest(1.5)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="oanim neuron_sun")
    ap.add_argument("--out", default="neuron_sun.mp4")
    ap.add_argument("--mode", default="draft",
                    choices=["preview", "draft", "final", "short"])
    a = ap.parse_args()
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), a.out))
    NeuronSun(save=out, mode=a.mode).run()
