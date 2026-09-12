"""Mini CPU-only organic motion core. No GPU, no numba, numpy+Pillow only."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 960, 540, 30


def _load_font(size):
    for path in ("/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Bold.otf",
                 "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
                 "/usr/share/fonts/adwaita-sans-fonts/AdwaitaSans-Regular.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_text_targets(text, w=W, h=H, n_targets=1500, seed=7):
    """Render text mask, return (targets[N,2] float xy, mask uint8, pil_image)."""
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    # auto-fit big centered title
    size = 170
    font = _load_font(size)
    for _ in range(6):
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        if tw <= w * 0.86 or size <= 60:
            break
        size -= 18
        font = _load_font(size)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1] - 20), text, fill=255, font=font)
    # subtitle with readable font
    sub = _load_font(26)
    sub_text = "O R G A N I C   M O T I O N"
    sb = d.textbbox((0, 0), sub_text, font=sub)
    stw = sb[2] - sb[0]
    d.text(((w - stw) / 2 - sb[0], h / 2 + 95), sub_text, fill=150, font=sub)
    mask = np.asarray(img)
    ys, xs = np.nonzero(mask > 100)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(xs), size=n_targets)
    targets = np.stack([xs[idx], ys[idx]]).astype(np.float32).T
    # wider jitter so 1500 particles don't stack on same pixels
    targets += rng.normal(0, 3.0, targets.shape).astype(np.float32)
    return targets, mask, img


def flow_field(pos, t):
    """Analytic curl-ish field, vectorized. pos [N,2], t seconds -> vel [N,2]."""
    x = pos[:, 0]
    y = pos[:, 1]
    vx = np.sin(y * 0.012 + t * 0.9) + 0.5 * np.sin((x + y) * 0.006 - t * 0.6)
    vy = np.cos(x * 0.011 - t * 0.7) + 0.5 * np.cos((x - y) * 0.007 + t * 0.5)
    return np.stack([vx, vy], axis=1).astype(np.float32) * 55.0  # px/sec


def render_frame(canvas, pos, targets, mask_img, frame, total, t):
    """canvas: float32 HxW trail buffer (mutated). Returns RGB uint8 frame."""
    # 1) fade trails: stronger fade late so settled text doesn't blow out
    canvas *= 0.90 if t < 3.0 else 0.82
    # 2) stamp particles (dimmer late to avoid stacking blowout)
    xi = np.clip(pos[:, 0].astype(np.int32), 0, W - 1)
    yi = np.clip(pos[:, 1].astype(np.int32), 0, H - 1)
    b = 1.2 if t < 3.0 else 0.55
    np.add.at(canvas, (yi, xi), b)
    if frame % 2 == 0:
        np.add.at(canvas, (np.clip(yi + 1, 0, H - 1), xi), 0.25)
        np.add.at(canvas, (yi, np.clip(xi + 1, 0, W - 1)), 0.25)
    np.clip(canvas, 0, 4, out=canvas)
    # 3) colormap: bg #0a0e14, trails teal->white
    glow = np.clip(canvas / 3.0, 0, 1)
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[..., 0] = 10 + glow * (40 + 215 * glow)       # R
    rgb[..., 1] = 14 + glow * (150 + 105 * glow)      # G teal->white
    rgb[..., 2] = 20 + glow * (160 + 95 * glow)       # B
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    # 4) sharp text fades in last 2s (spring-settled feel)
    if t > 2.6:
        a = min(1.0, (t - 2.6) / 1.2)
        txt = Image.new("RGB", (W, H), (10, 14, 20))
        td = ImageDraw.Draw(txt)
        # reuse mask as text luminance
        m = (np.asarray(mask_img).astype(np.float32) / 255.0 * a * 255).astype(np.uint8)
        white = Image.new("RGB", (W, H), (235, 245, 255))
        img = Image.composite(white, img, Image.fromarray(m, "L"))
    # 5) letterbox + timecode-safe vignette text
    d = ImageDraw.Draw(img)
    d.text((16, H - 24), f"oanim demo1  {t:4.1f}s  cpu-only  960x540@{FPS}", fill=(120, 140, 160))
    return np.asarray(img)
