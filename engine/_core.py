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


def _sstep(a, b, x):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    x = np.asarray(x, dtype=np.float32)
    t = np.clip((x - a) / np.maximum(1e-6, b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _flow_field(pos, t, scale=55.0):
    x, y = pos[:, 0], pos[:, 1]
    vx = np.sin(y * 0.012 + t * 0.9) + 0.5 * np.sin((x + y) * 0.006 - t * 0.6)
    vy = np.cos(x * 0.011 - t * 0.7) + 0.5 * np.cos((x - y) * 0.007 + t * 0.5)
    return np.stack([vx, vy], axis=1).astype(np.float32) * scale


def _as_f32_c(a):
    a = np.ascontiguousarray(a, dtype=np.float32)
    return a


def step_form(pos, vel, targets, nx, rand, ts, t_glob, dt, sweep, form_dur,
              k=46.0, c=7.2):
    """One fused morph step, in place. Returns (mean_act, mean_dist)."""
    if HAS_RUST:
        P = _as_f32_c(pos)
        V = _as_f32_c(vel)
        T = _as_f32_c(targets)
        X = _as_f32_c(nx)
        R = _as_f32_c(rand)
        out = _rc.step_form(P, V, T, X, R, float(ts), float(t_glob), float(dt),
                            float(sweep), float(form_dur), float(k), float(c))
        for dst, src in ((pos, P), (vel, V)):
            if dst is not src:
                dst[:] = src
        return float(out[0]), float(out[1])
    # numpy fallback (same math as the pre-Rust inline version)
    t0 = nx * sweep + rand
    act = _sstep(t0, t0 + 0.7, np.full(pos.shape[0], ts, np.float32))
    flow_w = float(1.0 - _sstep(0.0, form_dur * 0.6, ts) * 0.95)
    v_flow = _flow_field(pos, t_glob) * flow_w
    to_t = targets - pos
    vel += (v_flow * 0.35 + to_t * (k * act[:, None])
            - vel * (c * act[:, None])) * dt
    vel *= 0.985
    sp = np.linalg.norm(vel, axis=1, keepdims=True)
    cap = 460 - 260 * float(np.mean(act))
    vel *= np.minimum(1.0, cap / np.maximum(sp, 1e-6))
    pos += vel * dt
    return float(np.mean(act)), float(np.linalg.norm(to_t, axis=1).mean())


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
