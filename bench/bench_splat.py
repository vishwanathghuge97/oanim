"""Bench: numpy fallback vs Rust splat. Stays in tmp/."""
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine import _core
import oanim_core as rc

W, H = 960, 540
rng = np.random.default_rng(7)


def bench(n, iters=200):
    xi = rng.integers(0, W, n).astype(np.int32)
    yi = rng.integers(0, H, n).astype(np.int32)
    # correctness: same start, one stamp each
    c1 = np.zeros((H, W), np.float32)
    c2 = np.zeros((H, W), np.float32)
    xs = np.ascontiguousarray(xi)
    ys = np.ascontiguousarray(yi)
    v = np.full(n, 1.15, np.float32)
    rc.splat_add(c1, xs, ys, v)
    np.add.at(c2, (yi, xi), 1.15)
    diff = float(np.abs(c1 - c2).max())
    # glow correctness
    g1 = np.zeros((H, W), np.float32)
    g2 = np.zeros((H, W), np.float32)
    rc.splat_add_glow(g1, xs, ys, 1.15, 0.22)
    np.add.at(g2, (yi, xi), 1.15)
    md = yi + 1 < H
    np.add.at(g2, (yi[md] + 1, xi[md]), 0.22)
    mr = xi + 1 < W
    np.add.at(g2, (yi[mr], xi[mr] + 1), 0.22)
    gdiff = float(np.abs(g1 - g2).max())
    # speed
    t0 = time.perf_counter()
    for _ in range(iters):
        np.add.at(c2, (yi, xi), 1.15)
    t_np = (time.perf_counter() - t0) / iters * 1000
    t0 = time.perf_counter()
    for _ in range(iters):
        rc.splat_add(c1, xs, ys, v)
    t_rs = (time.perf_counter() - t0) / iters * 1000
    print(f"n={n:6d}  numpy={t_np:6.2f}ms  rust={t_rs:6.2f}ms  "
          f"speedup={t_np / max(t_rs, 1e-9):5.1f}x  maxdiff={diff:.1e}/{gdiff:.1e}")
    assert diff < 1e-4 and gdiff < 1e-4, "RUST/NUMPY MISMATCH"


print("HAS_RUST =", _core.HAS_RUST)
for n in (1500, 4000, 10000):
    bench(n)
print("BENCH OK")
