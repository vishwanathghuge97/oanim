# oanim session log — chronological context for AI agents (and the human)

## 2026-09-12 — Project birth + first demos (CPU-only engine)

* Goal set: programmatic animation tool for YouTube that feels natural but uncommon
  (not generic fade/slide). Niche locked: **organic-cinematic living titles**, not math
  (Manim) or clean explainers (Motion Canvas/Remotion).
* Hardware: ThinkBook 14 G7, Ryzen 7 7735HS (8c/16t), Radeon 680M iGPU, 16GB RAM,
  Fedora 44 Wayland. **No dGPU.** Mesa 26.1.8 has **no VAAPI encode profiles**
  (h264/hevc/av1_vaapi all fail with "No usable encoding profile") → CPU libx264 path.
* Stack: Python 3.14 `.venv` (project-local) + numpy + Pillow + imageio-ffmpeg.
  No numba (no 3.14 wheels at the time). Everything temp in `tmp/`, nothing system-wide.
* `demo1`: flow particles → text. **Bug:** attract jumped 0.15→14 at t=3.0 + flat white
  text composited on a timer → unnatural snap ("ghost pop").
* Fix (`engine/api.py`): per-particle staggered activation (`nx*sweep + rand`),
  underdamped spring (k=46, c=7.2), flow decays over first 60% of `form()`,
  text alpha = `min(progress, closeness)` from actual mean particle distance.
  Easy API: `Scene`/`Text`/`FlowParticles`/`Camera`, `construct_and_render()` 1-liner,
  CLI `./oanim render ... --mode preview/draft/final/short`, auto `.png` thumbnails.
* Font fix: Montserrat-Bold fought the dust aesthetic → default `weight="Light"`,
  `tracking` (letter-spacing) support. `demo2.mp4` (5.2s, 960x540@30, 156 frames).

## 2026-09-12 — Rust splat backend (slice 1)

* Split agreed: users write Python, Rust accelerates engine internals only.
* Toolchain problem: no gcc, no `python3-devel` on system. Solved project-local:
  `tmp/uv-python` (uv standalone Python 3.14 **with** headers = build interpreter),
  zig linker from pip `ziglang` via `tmp/zig-cc.sh`, rustup 1.98.1 into
  `tmp/rustup`+`tmp/cargo`. abi3 wheel bridges build/runtime interpreters.
* Crates: pyo3 0.29 + `numpy` (rust-numpy) **0.29** — 0.26 conflicts pyo3-ffi `links`.
  Gotcha: `num-traits` is not a pyo3 feature. PyO3 0.29 needs `mut` bindings
  (`mut canvas: PyReadwriteArray2`).
* Kernels: `splat_add`, `splat_add_glow` (fused center+neighbours, one call).
* Bench (`bench/bench_splat.py`): **43x@n1500, 79x@n4000, 59x@n10000**, bit-exact
  (2.4e-07 at n=10000).
* **Edge bug found by parity check:** numpy fallback clipped OOB glow neighbours
  (double-bright edge rows), Rust skipped them (~0.66 canvas-sum gap on frame 0).
  Fixed fallback to skip semantics. After fix: **all 156 raw frames bit-identical**,
  mp4 worst-diff 0. Lesson: compare raw `_draw` frames in one process, not mp4s
  (mp4 seeking can mislead).
* Vendored crates → `tmp/vendor`, offline `cargo build --release` verified.
  Rebuild: `sh rust-core/rebuild.sh`. Full render ~3.3s (splat was ~5% of frame
  time; Pillow+x264 dominate — real payoff comes with fused step/flock).
