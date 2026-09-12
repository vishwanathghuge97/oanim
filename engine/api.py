"""oanim — living titles for storytellers. CPU-only, numpy+Pillow."""
import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from engine._core import splat, splat_vals, step_form, HAS_RUST

W, H, FPS = 960, 540, 30

# oanim render modes: small preview -> draft -> full-HD final + vertical Short
MODES = {
    "preview": {"w": 640, "h": 360, "fps": 15},
    "draft": {"w": 960, "h": 540, "fps": 30},
    "final": {"w": 1920, "h": 1080, "fps": 30},
    "short": {"w": 720, "h": 1280, "fps": 30},  # 9:16 vertical
}

# Color themes: (bg, ramp0, ramp1, solid_text, spark). ramps blend glow->white.
THEMES = {
    "ink":   {"bg": (10, 14, 20), "r0": (40, 150, 160), "r1": (255, 255, 255),
              "solid": (228, 238, 250), "spark": (120, 200, 210)},
    "ember": {"bg": (16, 8, 6), "r0": (200, 70, 20), "r1": (255, 236, 210),
              "solid": (255, 240, 228), "spark": (255, 150, 70)},
    "bone":  {"bg": (12, 12, 14), "r0": (120, 120, 130), "r1": (250, 250, 245),
              "solid": (245, 245, 240), "spark": (200, 200, 195)},
    "moss":  {"bg": (6, 12, 8), "r0": (40, 140, 70), "r1": (235, 255, 235),
              "solid": (225, 245, 225), "spark": (120, 220, 130)},
}


def smoothstep(a, b, x):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    x = np.asarray(x, dtype=np.float32)
    denom = np.maximum(1e-6, b - a)
    t = np.clip((x - a) / denom, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _load_font(size, weight="Light"):
    # Light/Thin matches dust aesthetics: thin strokes let particle texture show.
    for path in (f"/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-{weight}.otf",
                 "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Light.otf",
                 "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Light.otf",
                 "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _blur3(img):
    """One separable 3-tap blur pass ([1,2,1]/4 along each axis)."""
    t = img.copy()
    t[:, 1:-1] = (img[:, :-2] + 2 * img[:, 1:-1] + img[:, 2:]) * 0.25
    t[1:-1, :] = (t[:-2, :] + 2 * t[1:-1, :] + t[2:, :]) * 0.25
    return t


def _ss01(a, b, x):
    t = np.clip((x - a) / max(1e-6, b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _draw_tracked(d, center_x, y, text, font, fill, tracking=10):
    """Draw text with letter-spacing, return total width. Pillow has no tracking."""
    widths = []
    for ch in text:
        bb = d.textbbox((0, 0), ch, font=font)
        widths.append(bb[2] - bb[0])
    total = sum(widths) + tracking * (len(text) - 1)
    x = center_x - total / 2
    for ch, cw in zip(text, widths):
        bb = d.textbbox((0, 0), ch, font=font)
        d.text((x - bb[0], y), ch, fill=fill, font=font)
        x += cw + tracking
    return total


class Targets:
    """Anything particles can form: text, blooms, branches, DLA clusters.
    Subclasses provide sample_targets(); order attr (0..1) optionally sets
    reveal sequence (default: left-to-right sweep). mask None = no solid text."""

    mask = None
    mask_np = None
    order = None

    def render_mask(self):
        return None

    def sample_targets(self, n, seed=7):
        raise NotImplementedError


class Bloom(Targets):
    """Phyllotaxis spiral bloom. Center-out growth, no text."""

    def __init__(self, scale=0.40, jitter=2.0, seed=7):
        self.scale, self.jitter, self.seed = scale, jitter, seed

    def sample_targets(self, n, seed=7):
        rng = np.random.default_rng(seed)
        i = np.arange(n, dtype=np.float32)
        ga = np.pi * (3.0 - np.sqrt(5.0))
        r = np.sqrt((i + 0.5) / n) * min(W, H) * self.scale
        th = i * ga
        x = W / 2 + r * np.cos(th) + rng.normal(0, self.jitter, n)
        y = H / 2 + r * np.sin(th) * 0.62 + rng.normal(0, self.jitter, n)
        self.order = np.ascontiguousarray((i / max(1, n - 1)).astype(np.float32))
        return np.ascontiguousarray(np.stack([x, y], axis=1).astype(np.float32))


class Branch(Targets):
    """Recursive branching tree grown from bottom-center. Depth-ordered reveal."""

    def __init__(self, depth=9, spread=0.55, shrink=0.74, seed=7):
        self.depth, self.spread, self.shrink, self.seed = depth, spread, shrink, seed

    def sample_targets(self, n, seed=7):
        rng = np.random.default_rng(seed)
        segs = []  # (x0,y0,x1,y1,depth)
        stack = [(W / 2, H * 0.96, -np.pi / 2, H * 0.30, 0)]
        while stack:
            x, y, ang, ln, d = stack.pop()
            x1, y1 = x + np.cos(ang) * ln, y + np.sin(ang) * ln
            segs.append((x, y, x1, y1, d))
            if d < self.depth:
                for s in (-1, 1):
                    na = ang + s * (self.spread * (0.6 + 0.8 * rng.random()))
                    stack.append((x1, y1, na, ln * self.shrink * (0.85 + 0.3 * rng.random()), d + 1))
        segs = np.array(segs, dtype=np.float32)
        maxd = max(1.0, segs[:, 4].max())
        # trunk-first weighting: thick base, delicate tips
        wgt = (maxd - segs[:, 4] + 2.0)
        per = np.maximum(1, (n * wgt / wgt.sum()).astype(int))
        pts, ord_ = [], []
        for (x0, y0, x1, y1, d), k in zip(segs, per):
            f = rng.random(k).astype(np.float32)
            pts.append(np.stack([x0 + (x1 - x0) * f, y0 + (y1 - y0) * f], axis=1))
            ord_.append(np.full(k, d / maxd, np.float32))
        pts = np.concatenate(pts)[:n]
        ord_ = np.concatenate(ord_)[:n]
        if len(pts) < n:  # pad with jittered copies
            pad = rng.integers(0, len(pts), n - len(pts))
            pts = np.concatenate([pts, pts[pad] + rng.normal(0, 2, (len(pad), 2))])
            ord_ = np.concatenate([ord_, ord_[pad]])
        self.order = np.ascontiguousarray(ord_.astype(np.float32))
        return np.ascontiguousarray(pts.astype(np.float32))


class DLA(Targets):
    """Diffusion-limited aggregation cluster (lightning/coral). Stick-ordered."""

    def __init__(self, sticks=2200, seed=7):
        self.sticks, self.seed = sticks, seed

    def sample_targets(self, n, seed=7):
        rng = np.random.default_rng(seed)
        gw, gh = 288, 162
        grid = np.zeros((gh, gw), bool)
        cx, cy = gw // 2, gh // 2
        grid[cy, cx] = True
        pts = []
        radius = 3.0
        batch = 500
        stuck = 0
        guard = 0
        while stuck < self.sticks and guard < 600:
            guard += 1
            r0 = radius + 6.0
            a = rng.random(batch) * 2 * np.pi
            px = (cx + r0 * np.cos(a)).astype(int).clip(1, gw - 2)
            py = (cy + r0 * np.sin(a)).astype(int).clip(1, gh - 2)
            live = np.ones(batch, bool)
            for _ in range(150):
                if not live.any():
                    break
                step = rng.integers(0, 4, batch)
                dx = np.where(step == 0, 1, np.where(step == 1, -1, 0))
                dy = np.where(step == 2, 1, np.where(step == 3, -1, 0))
                px[live] = (px[live] + dx[live]).clip(1, gw - 2)
                py[live] = (py[live] + dy[live]).clip(1, gh - 2)
                # kill strays far outside (classic DLA)
                far = (px - cx) ** 2 + (py - cy) ** 2 > (3 * r0 + 20) ** 2
                live[far] = False
                lx = px[live]
                ly = py[live]
                hit = grid[ly - 1, lx] | grid[ly + 1, lx] | grid[ly, lx - 1] | grid[ly, lx + 1]
                idx = np.nonzero(live)[0][hit]
                new = [(px[j], py[j]) for j in idx if not grid[py[j], px[j]]]
                for jx, jy in new:
                    grid[jy, jx] = True
                    pts.append((jx, jy))
                if new:
                    dd = max((jx - cx) ** 2 + (jy - cy) ** 2 for jx, jy in new)
                    radius = max(radius, float(np.sqrt(dd)) + 2.0)
                live[idx] = False
                stuck += len(new)
                if stuck >= self.sticks:
                    break
        if not pts:  # degenerate fallback: small disc
            a = rng.random(max(n, 64)) * 2 * np.pi
            r = rng.random(max(n, 64)) * 8
            pts = list(zip((cx + r * np.cos(a)).astype(int),
                           (cy + r * np.sin(a)).astype(int)))
        pts = np.array(pts, dtype=np.float32)
        sx, sy = W / gw, H / gh
        pts[:, 0] *= sx
        pts[:, 1] *= sy
        order = np.linspace(0, 1, len(pts)).astype(np.float32)
        if len(pts) >= n:
            sel = np.linspace(0, len(pts) - 1, n).astype(int)
            pts, order = pts[sel], order[sel]
        else:
            pad = rng.integers(0, len(pts), n - len(pts))
            pts = np.concatenate([pts, pts[pad] + rng.normal(0, 2, (len(pad), 2))])
            order = np.concatenate([order, order[pad]])
        self.order = np.ascontiguousarray(order)
        return np.ascontiguousarray(pts.astype(np.float32))


class Text(Targets):
    """What the particles will become. User only sets strings."""

    def __init__(self, title, subtitle="ORGANIC MOTION", seed=7,
                 weight="Light", tracking=14):
        self.title = title
        self.subtitle = subtitle
        self.seed = seed
        self.weight = weight      # Thin / ExtraLight / Light / Regular
        self.tracking = tracking  # airy letter-spacing for organic feel
        self.mask = None      # L image
        self.mask_np = None
        self.targets = None   # filled on demand per particle count
        self.sub_mask = None  # subtitle-only L image (crisp support line in ink mode)
        self.sub_mask_np = None

    def render_mask(self, w=None, h=None):
        w = w or W
        h = h or H
        img = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(img)
        # Thin needs bigger size to hold same visual weight -> start 190
        size = 190
        font = _load_font(size, self.weight)
        for _ in range(8):
            # measure with tracking
            widths = [(d.textbbox((0, 0), ch, font=font)[2]
                       - d.textbbox((0, 0), ch, font=font)[0]) for ch in self.title]
            total = sum(widths) + self.tracking * (len(self.title) - 1)
            if total <= w * 0.86 or size <= 60:
                break
            size -= 14
            font = _load_font(size, self.weight)
        bb = d.textbbox((0, 0), "Ag", font=font)
        cap_h = bb[3] - bb[1]
        _draw_tracked(d, w / 2, h / 2 - cap_h / 2 - 30, self.title,
                      font, 255, tracking=self.tracking)
        sub = _load_font(24, self.weight)
        _draw_tracked(d, w / 2, h / 2 + 90, self.subtitle,
                      sub, 150, tracking=10)
        self.mask = img
        self.mask_np = np.asarray(img)
        # subtitle-only mask: thin support lines can't bake legibly from
        # sparse particle ink, so ink mode composites this crisply instead.
        sub_img = Image.new("L", (w, h), 0)
        ds = ImageDraw.Draw(sub_img)
        _draw_tracked(ds, w / 2, h / 2 + 90, self.subtitle,
                      sub, 200, tracking=10)
        self.sub_mask = sub_img
        self.sub_mask_np = np.asarray(sub_img)
        return img

    def sample_targets(self, n, seed=7):
        if self.mask_np is None:
            self.render_mask()
        ys, xs = np.nonzero(self.mask_np > 100)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(xs), size=n)
        t = np.ascontiguousarray(
            np.stack([xs[idx], ys[idx]]).T, dtype=np.float32)
        t += rng.normal(0, 3.0, t.shape).astype(np.float32)
        self.targets = t
        return t


def flow_field(pos, t, scale=55.0):
    x, y = pos[:, 0], pos[:, 1]
    vx = np.sin(y * 0.012 + t * 0.9) + 0.5 * np.sin((x + y) * 0.006 - t * 0.6)
    vy = np.cos(x * 0.011 - t * 0.7) + 0.5 * np.cos((x - y) * 0.007 + t * 0.5)
    return np.stack([vx, vy], axis=1).astype(np.float32) * scale


class _Phase:
    def __init__(self, name, duration, fn):
        self.name = name
        self.duration = duration
        self.fn = fn  # fn(state, t_global, dt)


class FlowParticles:
    """The only thing users animate. drift() then form() = natural morph."""

    def __init__(self, n=1500, seed=7):
        self.n = n
        self.seed = seed
        rng = np.random.default_rng(seed)
        # C-contiguous float32: required by the Rust kernels (no .T views).
        self.pos = np.ascontiguousarray(
            np.stack([rng.uniform(0, W, n),
                      rng.uniform(0, H, n)]).T, dtype=np.float32)
        self.vel = np.zeros((n, 2), dtype=np.float32)
        self.targets = None
        self.t0 = None       # per-particle activation time (set in form())
        self.text = None
        self._nx = None
        self._rand = rng.uniform(0, 0.55, n).astype(np.float32)

    def drift(self, duration=1.8, drive=None):
        def fn(state, t, dt):
            e = float(drive.energy(t)) if drive is not None else 0.0
            v = flow_field(self.pos, t) * (1.0 + 1.6 * e)
            self.vel += v * 0.35 * dt
            self.vel *= 0.93 ** (dt * 30)  # fps-independent damping
            sp = np.linalg.norm(self.vel, axis=1, keepdims=True)
            self.vel *= np.minimum(1.0, (420.0 + 300.0 * e) / np.maximum(sp, 1e-6))
            self.pos += self.vel * dt
            state["flow_w"] = 1.0
            state["text_alpha"] = 0.0
            state["energy"] = e
        return _Phase("drift", duration, fn)

    def form(self, text, duration=2.4, sweep=1.1, k=46.0, c=7.2, drive=None):
        if text.mask_np is None:
            text.render_mask()
        self.text = text
        self.targets = text.sample_targets(self.n, seed=self.seed)
        # Reveal order: target-provided (growth sequence) or left-to-right sweep.
        if getattr(text, "order", None) is not None and len(text.order) == self.n:
            nx = text.order.astype(np.float32)
        else:
            xs = self.targets[:, 0]
            nx = ((xs - xs.min()) / max(1.0, xs.max() - xs.min())).astype(np.float32)
        self._nx = np.ascontiguousarray(nx)
        self._sweep = sweep
        self._form_dur = duration
        self._form_k = float(k)
        self._form_c = float(c)
        self._drive = drive
        # Capture per-call copies: a second form() must not retarget this phase.
        _targ, _nx, _sw, _dur = self.targets, self._nx, sweep, duration
        _k, _c, _drv = float(k), float(c), drive

        def fn(state, t, dt, _t0=[None]):
            if _t0[0] is None:
                _t0[0] = t  # phase start time
                state["ink_reset"] = True  # new target set: clear baked ink
            ts = t - _t0[0]
            e = float(_drv.energy(t)) if _drv is not None else 0.0
            # Fused kernel (Rust, numpy fallback): flow + spring + integrate.
            mean_act, dist = step_form(
                self.pos, self.vel, _targ, _nx, self._rand,
                ts, t, dt, _sw, _dur,
                k=_k, c=_c, boost=1.0 + 1.2 * e,
                damp=0.985 ** (dt * 30))  # fps-independent damping
            # convergence-driven text reveal: ghost only when dust arrives
            # 0 far -> 1 close, smooth
            closeness = float(np.clip((130.0 - dist) / 85.0, 0.0, 1.0))
            closeness = closeness * closeness * (3 - 2 * closeness)
            p = ts / max(1e-6, _dur)
            prog = float(p * p * (3 - 2 * p)) if p < 1 else 1.0
            # require BOTH progress and actual arrival
            alpha = min(prog, closeness) * 0.95
            state["flow_w"] = float(
                1.0 - smoothstep(0.0, _dur * 0.6, ts) * 0.95)
            state["text_alpha"] = alpha
            state["mean_act"] = float(mean_act)
            state["energy"] = e
        return _Phase("form", duration, fn)

    def flock(self, text, duration=3.0, sweep=1.0, drive=None,
              radius=26.0, sep=90.0, ali=0.9):
        """Boids that stream toward the target shape: separation + alignment
        on a uniform grid, weak spring home, living flow. Accepts Text/Targets."""
        if text.mask_np is None:
            text.render_mask()
        self.text = text
        self.targets = text.sample_targets(self.n, seed=self.seed)
        if getattr(text, "order", None) is not None and len(text.order) == self.n:
            nx = text.order.astype(np.float32)
        else:
            xs = self.targets[:, 0]
            nx = ((xs - xs.min()) / max(1.0, xs.max() - xs.min())).astype(np.float32)
        self._nx = np.ascontiguousarray(nx)
        self._sweep = sweep
        self._form_dur = duration
        # Capture per-call copies (same retarget hazard as form() had):
        # a later form()/flock() must not redirect this phase mid-render.
        _targ, _nx, _sw, _dur, _drv = self.targets, self._nx, sweep, duration, drive
        _radius, _sep, _ali = float(radius), float(sep), float(ali)

        def fn(state, t, dt, _t0=[None]):
            if _t0[0] is None:
                _t0[0] = t
                state["ink_reset"] = True  # new target set: clear baked ink
            ts = t - _t0[0]
            e = float(_drv.energy(t)) if _drv is not None else 0.0
            act = smoothstep(_nx * _sw + self._rand,
                             _nx * _sw + self._rand + 1.0,
                             np.full(self.n, ts, np.float32))
            flow_w = float(1.0 - smoothstep(0.0, _dur * 0.7, ts) * 0.6)
            # --- grid-hash neighbours (same-cell separation + alignment) ---
            cell = np.floor(self.pos / _radius).astype(np.int32)
            key = (cell[:, 0] + 64) * 512 + (cell[:, 1] + 64)
            ord_ = np.argsort(key)
            sp_, sv_ = self.pos[ord_], self.vel[ord_]
            _, _, cnt = np.unique(key[ord_], return_index=True, return_counts=True)
            cid = np.repeat(np.arange(len(cnt)), cnt)
            sump = np.zeros_like(sp_)
            sumv = np.zeros_like(sv_)
            np.add.at(sump, cid, sp_)
            np.add.at(sumv, cid, sv_)
            mp, mv = sump / cnt[cid, None], sumv / cnt[cid, None]
            away = sp_ - mp
            d = np.maximum(1.0, np.linalg.norm(away, axis=1, keepdims=True))
            crowd = np.minimum(1.0, (cnt[cid, None] - 1) / 5.0)
            f = (away / d) * crowd * _sep + (mv - sv_) * _ali
            f = f[np.argsort(ord_)]  # back to particle order
            # --- home spring + flow ---
            to_t = _targ - self.pos
            v_flow = flow_field(self.pos, t) * flow_w * (1.0 + e)
            k = 10.0
            self.vel += (v_flow * 0.5 + to_t * (k * act[:, None])
                         + f - self.vel * (3.0 * act[:, None] + 0.5)) * dt
            sp = np.linalg.norm(self.vel, axis=1, keepdims=True)
            self.vel *= np.minimum(1.0, 380.0 / np.maximum(sp, 1e-6))
            self.pos += self.vel * dt
            dist = float(np.linalg.norm(to_t, axis=1).mean())
            closeness = float(np.clip((150.0 - dist) / 100.0, 0.0, 1.0))
            closeness = closeness * closeness * (3 - 2 * closeness)
            p = ts / max(1e-6, _dur)
            prog = float(p * p * (3 - 2 * p)) if p < 1 else 1.0
            state["text_alpha"] = min(prog, closeness) * 0.9
            state["mean_act"] = 0.4
            state["energy"] = e
        return _Phase("flock", duration, fn)

    def scatter(self, duration=1.6, sweep=0.8, power=300.0, drive=None):
        """Reverse of form: letters burst back into flow. Needs form() first
        (uses its targets); otherwise bursts from screen center."""
        cx, cy = W / 2, H / 2

        def fn(state, t, dt, _t0=[None]):
            if _t0[0] is None:
                _t0[0] = t
            ts = t - _t0[0]
            e = float(drive.energy(t)) if drive is not None else 0.0
            if self.targets is not None:
                nx = self._nx if self._nx is not None else np.zeros(self.n, np.float32)
            else:
                nx = np.zeros(self.n, np.float32)
            rel = 1.0 - smoothstep(nx * sweep + self._rand * 0.5,
                                   nx * sweep + self._rand * 0.5 + 0.8,
                                   np.full(self.n, ts, np.float32))
            dx = self.pos[:, 0] - cx
            dy = self.pos[:, 1] - cy
            d = np.maximum(1.0, np.sqrt(dx * dx + dy * dy))
            v = flow_field(self.pos, t) * (1.2 + e)
            self.vel += ((v * 0.4
                          + np.stack([dx / d, dy / d], axis=1) * (power * rel)[:, None]
                          - self.vel * (2.0 * rel[:, None] + 0.4)) * dt)
            self.pos += self.vel * dt
            p = ts / max(1e-6, duration)
            state["text_alpha"] = max(0.0, state.get("text_alpha", 0.0) - dt / max(0.3, duration * 0.5))
            state["mean_act"] = 0.25
            state["energy"] = e
            _ = p
        return _Phase("scatter", duration, fn)

    def settle_jitter(self, t):
        # tiny breathing so final frame feels alive, not frozen
        return np.sin(t * 2.0 + self._rand * 6.28) * 0.35


class Camera:
    """2.5D crop-zoom camera. Cheap: one Pillow crop+resize per frame (~2ms)."""

    def __init__(self):
        self.z0, self.z1 = 1.0, 1.0
        self.shake = 0.0  # px amplitude of handheld

    def push_in(self, z0=1.0, z1=1.08):
        self.z0, self.z1 = z0, z1
        return self

    def pull_out(self, z0=1.08, z1=1.0):
        self.z0, self.z1 = z0, z1
        return self

    def handheld(self, amp=2.0):
        self.shake = amp
        return self

    def get(self, t, total):
        p = min(1.0, t / max(1e-6, total))
        # smooth ease for zoom so move feels cinematic, not linear
        e = p * p * (3 - 2 * p)
        z = self.z0 + (self.z1 - self.z0) * e
        dx = (np.sin(t * 1.3) + 0.5 * np.sin(t * 2.7 + 1.0)) * self.shake
        dy = (np.cos(t * 1.1 + 0.5) + 0.5 * np.sin(t * 2.3)) * self.shake
        return z, float(dx), float(dy)


class Scene:
    """User subclasses this and writes construct() with self.play() calls."""

    def __init__(self, out="demo2.mp4", fps=None, w=None, h=None,
                 mode="draft", encoder="cpu", thumbnail=True,
                  theme="ink", motion_blur=0.0, reveal="ink",
                  ink_gain=1.0, ink_sharp=0.45, ink_sigma=9.0):
        global W, H, FPS
        if mode in MODES:
            m = MODES[mode]
            w = w or m["w"]
            h = h or m["h"]
            fps = fps or m["fps"]
        w = w or W
        h = h or H
        fps = fps or FPS
        # publish dims globally so FlowParticles/Text created in construct() follow
        W, H, FPS = w, h, fps
        self.out = os.path.abspath(out)
        self.fps = fps
        self.w, self.h = w, h
        self.mode = mode
        self.encoder = encoder
        self.thumbnail = thumbnail
        self.theme = THEMES.get(theme, THEMES["ink"])
        self.motion_blur = float(motion_blur)  # 0 off, ~0.5-1 streaky tails
        self.reveal = reveal  # ink (baked by particles) | dots | solid (mask)
        self.ink_gain = float(ink_gain)
        self.ink_sharp = float(ink_sharp)  # smoothstep center for ink->solid
        self.ink_sigma = float(ink_sigma)  # deposit radius in draft-px (540p);
        # auto-scaled by resolution so one default holds preview->final
        self.ink_sigma_eff = float(ink_sigma) * (min(w, h) / 540.0)
        self.ink = np.zeros((h, w), np.float32)  # persistent, never fades
        self.phases = []
        self.canvas = np.zeros((h, w), np.float32)
        self.state = {"text_alpha": 0.0, "flow_w": 1.0}
        self.particles = None
        self.text_obj = None
        self.camera = None
        self._total = 0.0

    def attach_camera(self, cam):
        self.camera = cam
        return cam

    def play(self, phase):
        self.phases.append(phase)
        return phase

    def hold(self, duration=1.0):
        def fn(state, t, dt):
            # almost still: strong damping + breathing
            if self.particles is not None and self.particles.targets is not None:
                to_t = self.particles.targets - self.particles.pos
                self.particles.vel += (to_t * 18.0 - self.particles.vel * 7.5) * dt
                self.particles.pos += self.particles.vel * dt
                self.particles.pos[:, 0] += self.particles.settle_jitter(t) * dt * 8
            state["text_alpha"] = min(0.95, state.get("text_alpha", 0.9) + dt * 0.15)
        return _Phase("hold", duration, fn)

    def construct_and_render(self):
        self.construct()
        return self.render()

    # -- rendering (users never touch this) --
    def _apply_camera(self, img, t):
        if self.camera is None:
            return img
        z, dx, dy = self.camera.get(t, self._total or 1.0)
        if abs(z - 1.0) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05:
            return img
        cw, ch = self.w / z, self.h / z
        cx, cy = self.w / 2 + dx, self.h / 2 + dy
        box = (int(cx - cw / 2), int(cy - ch / 2),
               int(cx + cw / 2), int(cy + ch / 2))
        # clamp inside frame
        box = (max(0, box[0]), max(0, box[1]),
               min(self.w, box[2]), min(self.h, box[3]))
        if box[2] - box[0] < 8 or box[3] - box[1] < 8:
            return img
        return img.crop(box).resize((self.w, self.h), Image.BILINEAR)

    def _draw(self, t, frame):
        p = self.particles
        th = self.theme
        # energy drive (audio): brighter stamps + longer trails on beats
        e = float(self.state.get("energy", 0.0))
        # fade: faster mid-settle so trails don't smear letters
        mean_act = self.state.get("mean_act", 0.0)
        fade = 0.90 if mean_act < 0.7 else 0.84
        self.canvas *= fade
        if p is not None:
            xi = np.clip(p.pos[:, 0].astype(np.int32), 0, self.w - 1)
            yi = np.clip(p.pos[:, 1].astype(np.int32), 0, self.h - 1)
            b = (1.15 if mean_act < 0.7 else 0.5) * (1.0 + 0.8 * e)
            g = 0.22 if frame % 2 == 0 else 0.0
            splat(self.canvas, xi, yi, b, glow=g)
            if self.motion_blur > 0 and hasattr(p, "vel"):
                tx = np.clip((p.pos[:, 0] - p.vel[:, 0] * (1 / max(1, self.fps))
                               * 1.5 * self.motion_blur).astype(np.int32),
                              0, self.w - 1)
                ty = np.clip((p.pos[:, 1] - p.vel[:, 1] * (1 / max(1, self.fps))
                               * 1.5 * self.motion_blur).astype(np.int32),
                              0, self.h - 1)
                splat(self.canvas, tx, ty, b * 0.45)
        np.clip(self.canvas, 0, 4, out=self.canvas)
        glow = np.clip(self.canvas / 3.0, 0, 1)
        bg = np.array(th["bg"], np.float32)
        r0 = np.array(th["r0"], np.float32) - bg
        r1 = np.array(th["r1"], np.float32) - bg - r0
        rgb = bg[None, None, :] + glow[..., None] * (r0[None, None, :] + glow[..., None] * r1[None, None, :])
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
        # soft text UNDER particles: emerges from dust instead of popping over
        a = float(self.state.get("text_alpha", 0.0))
        phase = self.state.get("phase", "")
        if self.state.pop("ink_reset", False):
            self.ink.fill(0)  # new form/flock target: don't ghost the old shape
        if self.reveal == "dots":
            a = 0.0
        if self.reveal == "ink" and p is not None and p.targets is not None:
            if phase == "scatter":
                self.ink *= 0.90  # letters dissolve with the burst
            elif phase in ("form", "flock", "hold"):
                # bake only while shaping: drift flybys must not pre-ghost letters
                d2 = ((p.pos - p.targets) ** 2).sum(axis=1)
                w = (np.exp(-d2 / (2 * self.ink_sigma_eff ** 2)).astype(np.float32)
                     * self.ink_gain)
                splat_vals(self.ink, xi, yi, w)
                # saturating cap: threshold stays valid across modes/densities
                np.clip(self.ink, 0, 1, out=self.ink)
            if self.ink.max() > 1e-3:
                bl = _blur3(_blur3(_blur3(self.ink)))
                m_ink = (_ss01(self.ink_sharp - 0.25, self.ink_sharp + 0.25,
                               np.clip(bl, 0, 1)) * 255).astype(np.uint8)
                solid = Image.new("RGB", (self.w, self.h), th["solid"])
                img = Image.composite(solid, img, Image.fromarray(m_ink, "L"))
                # re-add particle sparkle on top so letters keep texture
                img_np = np.asarray(img).astype(np.float32)
                ink_a = _ss01(0.02, 0.2, np.clip(bl, 0, 1))
                spark = (glow * (1 - ink_a * 0.55))[..., None] * np.array(th["spark"], np.float32)
                img_np += spark * 0.55
                img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8), "RGB")
            # crisp subtitle under the baked title: support line stays legible
            # (alpha is closeness-gated in form(), so no pop; dots mode zeroes a)
            sub_m = getattr(self.text_obj, "sub_mask_np", None)
            if a > 0.01 and sub_m is not None:
                sm = (sub_m.astype(np.float32) / 255.0 * a * 255).astype(np.uint8)
                solid = Image.new("RGB", (self.w, self.h), th["solid"])
                img = Image.composite(solid, img, Image.fromarray(sm, "L"))
        elif a > 0.01 and self.text_obj is not None and self.text_obj.mask is not None:
            m = (self.text_obj.mask_np.astype(np.float32) / 255.0 * a * 255).astype(np.uint8)
            solid = Image.new("RGB", (self.w, self.h), th["solid"])
            img = Image.composite(solid, img, Image.fromarray(m, "L"))
            # re-add particle sparkle on top so letters keep texture
            img_np = np.asarray(img).astype(np.float32)
            spark = (glow * (1 - a * 0.55))[..., None] * np.array(th["spark"], np.float32)
            img_np += spark * 0.55
            img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8), "RGB")
        d = ImageDraw.Draw(img)
        d.text((16, self.h - 24), f"oanim  {t:4.1f}s  {self.mode}", fill=(120, 140, 160))
        img = self._apply_camera(img, t)
        return np.asarray(img)

    def _write_thumbnail(self, last_frame):
        try:
            base, _ = os.path.splitext(self.out)
            Image.fromarray(last_frame).save(base + ".png")
            print("THUMB", base + ".png")
        except Exception as e:
            print("thumb skip:", e)

    def _maybe_vaapi(self):
        """Transcode CPU mp4 -> VAAPI mp4 offloading encode to 680M."""
        if self.encoder != "vaapi":
            return self.out
        dev = "/dev/dri/renderD128"
        if not os.path.exists(dev):
            print("vaapi device missing, keeping cpu encode")
            return self.out
        base, _ = os.path.splitext(self.out)
        va = base + ".vaapi.mp4"
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-vaapi_device", dev, "-i", self.out,
               "-vf", "format=nv12,hwupload",
               "-c:v", "h264_vaapi", "-qp", "23",
               "-movflags", "+faststart", va]
        try:
            subprocess.run(cmd, check=True, cwd=os.path.dirname(self.out) or ".")
            print("VAAPI", va)
            return va
        except Exception as e:
            print("vaapi fallback:", e)
            return self.out

    def render(self):
        import imageio.v2 as imageio
        os.makedirs(os.path.dirname(self.out) or ".", exist_ok=True)
        self._total = sum(p.duration for p in self.phases)
        self.canvas.fill(0)  # fresh buffers every render (repeat-safe)
        self.ink.fill(0)
        w = imageio.get_writer(self.out, fps=self.fps, codec="libx264",
                               quality=8, macro_block_size=2,
                               ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
        dt = 1.0 / self.fps
        t, frame = 0.0, 0
        # find particles + text refs
        for ph in self.phases:
            fn = ph.fn
            # duck-type: FlowParticles phases close over self; grab via defaults is hard,
            # so user sets scene.particles explicitly in construct()
            pass
        for ph in self.phases:
            steps = int(ph.duration * self.fps)
            for _ in range(steps):
                self.state["phase"] = ph.name
                ph.fn(self.state, t, dt)
                fr = self._draw(t, frame)
                w.append_data(fr)
                last = fr
                t += dt
                frame += 1
                if frame % 30 == 0:
                    print(f"[{frame}] t={t:.1f}s phase={ph.name}", flush=True)
        w.close()
        print("WROTE", self.out)
        if self.thumbnail:
            try:
                self._write_thumbnail(last)
            except Exception as e:
                print("thumb skip:", e)
        return self._maybe_vaapi()

    def render_loop(self, blend=0.6):
        """Render, then crossfade tail into head for a seamless ambient loop."""
        out = self.render()
        import imageio.v2 as imageio
        r = imageio.get_reader(out)
        frames = [f for f in r]
        r.close()
        k = min(len(frames) - 1, max(2, int(blend * self.fps)))
        for i in range(k):
            a = (i + 1) / (k + 1)
            frames[i] = (frames[i].astype(np.float32) * a
                         + frames[len(frames) - k + i].astype(np.float32) * (1 - a)
                         ).astype(np.uint8)
        frames = frames[:-k] if k else frames
        w = imageio.get_writer(out, fps=self.fps, codec="libx264",
                               quality=8, macro_block_size=2,
                               ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
        for f in frames:
            w.append_data(f)
        w.close()
        print("LOOP", out, f"({len(frames)} frames, {blend}s xfade)")
        return out
