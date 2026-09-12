"""Bench: fused step_form Rust vs numpy. Tolerance parity (1e-3), not bit-exact:
vectorized numpy and sequential Rust round floats differently (~1e-7/step)."""
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine import _core
import oanim_core as rc

assert _core.HAS_RUST, "build the extension first (sh rust-core/rebuild.sh)"


def make(n, seed=11):
    rng = np.random.default_rng(seed)
    pos = np.ascontiguousarray(rng.uniform(0, 960, (n, 2)).astype(np.float32))
    vel = np.zeros((n, 2), dtype=np.float32)
    tgt = np.ascontiguousarray(rng.uniform(100, 860, (n, 2)).astype(np.float32))
    nx = np.ascontiguousarray(rng.uniform(0, 1, n).astype(np.float32))
    rnd = np.ascontiguousarray(rng.uniform(0, 0.55, n).astype(np.float32))
    return pos, vel, tgt, nx, rnd


def run_rust(n, steps=78, seed=11):
    pos, vel, tgt, nx, rnd = make(n, seed)
    t = 1.6
    t0 = time.perf_counter()
    for s in range(steps):
        ts = s / 30.0
        _core.step_form(pos, vel, tgt, nx, rnd, ts, t, 1 / 30, 0.9, 2.6)
        t += 1 / 30
    dt = (time.perf_counter() - t0) / steps * 1000
    return pos, vel, dt


def run_numpy(n, steps=78, seed=11):
    import os as _os
    _os.environ["OANIM_CORE"] = "off"
    import importlib
    import engine._core as core_np
    importlib.reload(core_np)
    assert not core_np.HAS_RUST
    pos, vel, tgt, nx, rnd = make(n, seed)
    t = 1.6
    t0 = time.perf_counter()
    for s in range(steps):
        ts = s / 30.0
        core_np.step_form(pos, vel, tgt, nx, rnd, ts, t, 1 / 30, 0.9, 2.6)
        t += 1 / 30
    dt = (time.perf_counter() - t0) / steps * 1000
    return pos, vel, dt


print("n      rust/step  numpy/step  speedup  max|dpos|  max|dvel|")
for n in (1500, 4000, 10000):
    pr, vr, tr = run_rust(n)
    pn, vn, tn = run_numpy(n)
    dp = float(np.abs(pr - pn).max())
    dv = float(np.abs(vr - vn).max())
    print(f"{n:<7d}{tr:6.2f}ms    {tn:6.2f}ms     {tn / max(tr, 1e-9):5.1f}x   "
          f"{dp:.2e}   {dv:.2e}")
    assert dp < 1e-3 and dv < 1e-3, "PARITY FAIL"
print("STEP BENCH OK")
