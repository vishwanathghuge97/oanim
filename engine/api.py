"""oanim — living titles for storytellers. CPU-only, numpy+Pillow."""
import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from engine._core import splat, step_form, HAS_RUST

W, H, FPS = 960, 540, 30

# oanim render modes: small preview -> draft -> full-HD final + vertical Short
MODES = {
    "preview": {"w": 640, "h": 360, "fps": 15},
    "draft": {"w": 960, "h": 540, "fps": 30},
    "final": {"w": 1920, "h": 1080, "fps": 30},
    "short": {"w": 720, "h": 1280, "fps": 30},  # 9:16 vertical
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


class Text:
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
        self._rand = rng.uniform(0, 0.55, n).astype(np.float32)

    def drift(self, duration=1.8):
        def fn(state, t, dt):
            v = flow_field(self.pos, t)
            self.vel += v * 0.35 * dt
            self.vel *= 0.93
            sp = np.linalg.norm(self.vel, axis=1, keepdims=True)
            self.vel *= np.minimum(1.0, 420.0 / np.maximum(sp, 1e-6))
            self.pos += self.vel * dt
            state["flow_w"] = 1.0
            state["text_alpha"] = 0.0
        return _Phase("drift", duration, fn)

    def form(self, text, duration=2.4, sweep=1.1):
        if text.mask_np is None:
            text.render_mask()
        self.text = text
        self.targets = text.sample_targets(self.n, seed=self.seed)
        # sweep left->right + random: letters crystallize in order, not all at once
        xs = self.targets[:, 0]
        nx = ((xs - xs.min()) / max(1.0, xs.max() - xs.min())).astype(np.float32)
        self._nx = np.ascontiguousarray(nx)
        self._sweep = sweep
        self._form_dur = duration

        def fn(state, t, dt, _t0=[None]):
            if _t0[0] is None:
                _t0[0] = t  # phase start time
            ts = t - _t0[0]
            # Fused kernel (Rust, numpy fallback): flow + spring + integrate.
            mean_act, dist = step_form(
                self.pos, self.vel, self.targets, self._nx, self._rand,
                ts, t, dt, self._sweep, self._form_dur)
            # convergence-driven text reveal: ghost only when dust arrives
            # 0 far -> 1 close, smooth
            closeness = float(np.clip((130.0 - dist) / 85.0, 0.0, 1.0))
            closeness = closeness * closeness * (3 - 2 * closeness)
            p = ts / max(1e-6, self._form_dur)
            prog = float(p * p * (3 - 2 * p)) if p < 1 else 1.0
            # require BOTH progress and actual arrival
            alpha = min(prog, closeness) * 0.95
            state["flow_w"] = float(
                1.0 - smoothstep(0.0, self._form_dur * 0.6, ts) * 0.95)
            state["text_alpha"] = alpha
            state["mean_act"] = float(mean_act)
        return _Phase("form", duration, fn)

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
                 mode="draft", encoder="cpu", thumbnail=True):
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
        # fade: faster mid-settle so trails don't smear letters
        mean_act = self.state.get("mean_act", 0.0)
        fade = 0.90 if mean_act < 0.7 else 0.84
        self.canvas *= fade
        if p is not None:
            xi = np.clip(p.pos[:, 0].astype(np.int32), 0, self.w - 1)
            yi = np.clip(p.pos[:, 1].astype(np.int32), 0, self.h - 1)
            b = 1.15 if mean_act < 0.7 else 0.5
            g = 0.22 if frame % 2 == 0 else 0.0
            splat(self.canvas, xi, yi, b, glow=g)
        np.clip(self.canvas, 0, 4, out=self.canvas)
        glow = np.clip(self.canvas / 3.0, 0, 1)
        rgb = np.zeros((self.h, self.w, 3), np.float32)
        rgb[..., 0] = 10 + glow * (40 + 215 * glow)
        rgb[..., 1] = 14 + glow * (150 + 105 * glow)
        rgb[..., 2] = 20 + glow * (160 + 95 * glow)
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
        # soft text UNDER particles: emerges from dust instead of popping over
        a = float(self.state.get("text_alpha", 0.0))
        if a > 0.01 and self.text_obj is not None and self.text_obj.mask is not None:
            m = (self.text_obj.mask_np.astype(np.float32) / 255.0 * a * 255).astype(np.uint8)
            solid = Image.new("RGB", (self.w, self.h), (228, 238, 250))
            img = Image.composite(solid, img, Image.fromarray(m, "L"))
            # re-add particle sparkle on top so letters keep texture
            img_np = np.asarray(img).astype(np.float32)
            spark = (glow * (1 - a * 0.55))[..., None] * np.array([120, 200, 210], np.float32)
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
