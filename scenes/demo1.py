"""Demo1: curl-flow particles -> spring settle into GROWTH. CPU only, tmp inside project."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import imageio.v2 as imageio

from engine.mini import W, H, FPS, make_text_targets, flow_field, render_frame

DUR = 5.0
N = 1500
SEED = 7
OUT = os.path.join(os.path.dirname(__file__), "..", "demo1.mp4")
OUT = os.path.abspath(OUT)
TMP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tmp"))

os.makedirs(TMP, exist_ok=True)

rng = np.random.default_rng(SEED)
targets, mask_arr, mask_img = make_text_targets("GROWTH", n_targets=N)

# start scattered off-screen edges for natural inflow
pos = np.stack([rng.uniform(0, W, N), rng.uniform(0, H, N)]).astype(np.float32).T
vel = np.zeros_like(pos)
canvas = np.zeros((H, W), np.float32)

total = int(DUR * FPS)
dt = 1.0 / FPS

writer = imageio.get_writer(OUT, fps=FPS, codec="libx264", quality=8, macro_block_size=2,
                            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])

for f in range(total):
    t = f / FPS
    # phase weights: flow early, attract ramps in, spring settle late
    attract = 0.15 + max(0.0, (t - 0.8)) * 1.1      # grows over time
    if t > 3.0:  # strong spring settle with slight overshoot
        attract = 14.0
    damp = 0.92 if t < 3.0 else 0.86

    v_flow = flow_field(pos, t)
    # attraction to assigned letter pixel
    to_t = targets - pos
    vel += (v_flow * 0.35 + to_t * attract) * dt
    vel *= damp
    # speed cap keeps it silky, not jittery
    sp = np.linalg.norm(vel, axis=1, keepdims=True)
    vel *= np.minimum(1.0, 420.0 / np.maximum(sp, 1e-6))
    pos += vel * dt
    # soft contain
    pos[:, 0] = np.clip(pos[:, 0], -20, W + 20)
    pos[:, 1] = np.clip(pos[:, 1], -20, H + 20)

    frame = render_frame(canvas, pos, targets, mask_img, f, total, t)
    writer.append_data(frame)
    if f % 30 == 0:
        print(f"[{f}/{total}] t={t:.1f}s", flush=True)

writer.close()
print("WROTE", OUT)
