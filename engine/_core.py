"""oanim Rust fast path with numpy fallback.

Users never import this directly — Scene._draw uses it.
Disable with OANIM_CORE=off (forces numpy, for debugging).
"""
import os
import numpy as np

try:
    if os.environ.get("OANIM_CORE", "on").lower() in ("off", "0", "no"):
        raise ImportError("OANIM_CORE=off")
    import oanim_core as _rc
    HAS_RUST = True
except Exception:
    _rc = None
    HAS_RUST = False


def splat(canvas, xi, yi, b, glow=0.0):
    """Add brightness b at (xi, yi); glow g to right/down neighbours."""
    if HAS_RUST:
        xs = np.ascontiguousarray(xi, dtype=np.int32)
        ys = np.ascontiguousarray(yi, dtype=np.int32)
        c = np.ascontiguousarray(canvas, dtype=np.float32)
        if canvas is not c:
            canvas[:] = c
        if glow:
            _rc.splat_add_glow(c, xs, ys, float(b), float(glow))
        else:
            v = np.full(xs.shape, float(b), dtype=np.float32)
            _rc.splat_add(c, xs, ys, v)
        if canvas is not c:
            canvas[:] = c
        return
    # numpy fallback (identical math: OOB neighbours skipped, not wrapped)
    np.add.at(canvas, (yi, xi), b)
    if glow:
        h, w = canvas.shape
        md = yi + 1 < h
        np.add.at(canvas, (yi[md] + 1, xi[md]), glow)
        mr = xi + 1 < w
        np.add.at(canvas, (yi[mr], xi[mr] + 1), glow)
