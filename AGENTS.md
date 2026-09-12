# AGENTS.md — instructions for AI coding agents working in this repo

Read `README.md` and `logs/SESSION_LOG.md` before changing anything.

## 1. Hard rules

* **Project-local only.** Never `pip install` system-wide, never `dnf`/write to `~/`.
  Use `./.venv/bin/...`. Caches: `PIP_CACHE_DIR=tmp/pip-cache`,
  `UV_CACHE_DIR=tmp/uv-cache`, `TMPDIR=tmp/`.
* **All temp/generated files go in `tmp/`.** Renders, wheels, frame dumps,
  toolchains, vendor dirs. `tmp/` is git-ignored.
* **User API is frozen unless the user asks.** `scenes/*.py` express intent
  (`drift`/`form`/`hold`); keep them short. Engine changes must not break them.
  Personal videos live in `my_videos/` (scaffolded by `./oanim new`) — never
  edit or move them during engine work; verify with copies in `tmp/` instead.
  Course files in `course/` (lessons + learning docs) are runnable teaching
  material — keep every snippet working; update frames if engine output changes.
* **Rust is an accelerator, never a requirement.** Every Rust kernel ships with a
  numpy fallback in `engine/_core.py`. If the `.so` is missing, everything runs.
  `OANIM_CORE=off` forces the fallback path for debugging.
* **Parity policy.** New Rust kernels: bit-exact where possible (splat),
  else max abs diff ≤ 1e-3 on positions after a full scene run + visual frame check.
  Debug recipe that worked before: compare raw `_draw` frames in one process, not mp4s.
* **Verify before claiming done.** Rebuild → bench → draft render → fallback render
  (`OANIM_CORE=off`) → CLI preview. Compare frames numerically, view at least 3.

## 2. Toolchain (no system gcc, no python3-devel)

* Build interpreter (has headers): `tmp/uv-python/cpython-3.14.7-linux-x86_64-gnu/bin/python3`
* Runtime interpreter: `./.venv/bin/python` (system 3.14). abi3 wheel bridges them.
* Linker: zig via `tmp/zig-cc.sh` (wired in `rust-core/.cargo/config.toml`).
* Env: `RUSTUP_HOME=tmp/rustup CARGO_HOME=tmp/cargo CARGO_TARGET_DIR=tmp/rust-target`.
* Rebuild everything: `sh rust-core/rebuild.sh`. Offline-safe (`tmp/vendor`).

## 3. Architecture notes

* `Scene.__init__` publishes `W,H,FPS` globals so `FlowParticles`/`Text` created in
  `construct()` follow the render mode. `Text.render_mask(w=None,h=None)` resolves dims
  at call time (defaults bind at def time — do not use `w=W` defaults for dims).
* Morph design: per-particle staggered activation (`nx*sweep + rand`), underdamped
  spring (k≈46, c≈7.2), flow decays over first 60% of `form()`. Text reveal alpha =
  `min(progress, closeness)` where closeness tracks actual mean particle distance —
  never time-only (that caused the old "ghost pop").
* `Targets` base (`Bloom`/`Branch`/`DLA`/`Text`): `sample_targets()` + optional
  `order` array for reveal sequence; `mask=None` skips the solid-text composite.
  `form()`/`flock()` accept any Targets. Particle arrays must stay C-contiguous
  float32 (Rust slices) — never store `.T` views in `pos`/`vel`/`targets`.
* `engine/audio.py` is dep-free (ffmpeg PCM pipe + numpy RMS). `Scene._draw`
  reads `state["energy"]`; phases set it from `drive.energy(t)` or leave 0.
* Themes live in `THEMES` (`ink` default); `_draw` derives all colors from them.
  `motion_blur` adds a second tail stamp along `-vel` (0 = off, keeps parity).
* `Camera` is a 2.5D crop-zoom applied post-composite in `_draw` (~2ms/frame).
* VAAPI encode is dead on this Mesa (no encode profiles) — don't re-add it without
  re-testing `ffmpeg ... -c:v h264_vaapi` on a testsrc first.

## 4. Logging

* Append every work session to `logs/SESSION_LOG.md`: date, what changed, bench numbers,
  bugs found + root cause, verification commands + results. Next agent continues from there.
