# oanim session log — chronological context for AI agents (and the human)## 2026-09-12 — Project birth + first demos (CPU-only engine)

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

## 2026-09-12 — Repo hygiene + fused step kernel (slice 2)

* GitHub connected (`vishwanathghuge97/oanim`, branch `main`). Ignored: `.venv/`,
  `tmp/`, `*.mp4`, `*.so`. `demo2.png` thumbnail committed as visual proof;
  mp4s go to Releases, not git. Added `README.md`, `AGENTS.md`, this log.
  Bench moved `tmp/bench_splat.py` → `bench/` (tracked); `rebuild.sh` updated.
* Fused `step_form` kernel: analytic flow trig + staggered spring + cap + integrate
  in one rayon-parallel pass (`pos/vel` inout, returns `mean_act, mean_dist`).
  `form()` in `api.py` now delegates to `engine/_core.py::step_form`.
* Contiguity gotcha: `pos`/`vel`/`targets` were `.T` views (non-contiguous) —
  Rust `as_slice_mut` needs C-contiguous. Fixed at creation (`ascontiguousarray`,
  values unchanged). `nx` cast to float32.
* Bench (`bench/bench_step.py`, full 78-step form run): **1.6-1.8x @n1500,
  ~1x @n4000+** — trig+bandwidth bound; numpy's vectorized libm already near-optimal.
  Even f32 trig didn't move it (overhead dominates at these N). Parity: max pos diff
  1.2e-04 @1500, exact @4000/10000 (≤1e-3 policy ✓).
* Full-scene parity: raw frames 0–120 bit-identical; final frame maxdiff 58 =
  sub-perceptual sparkle grain (verified visually, letters identical).
* Honest perf picture: sim is ~1% of frame time; total render still ~3.3s
  (Pillow colormap/composite + x264 dominate). Next high-value Rust targets:
  colormap+composite fusion, or `flock()` O(n²) neighbor search. Do NOT chase
  trig micro-opts further.

## 2026-09-12 — Full feature landing (one session)

* Core: `form(k, c)` tuning, `scatter()` burst-outro (radial kick + flow, alpha
  decays), 4 `THEMES` (ink/ember/bone/moss, `_draw` fully theme-driven),
  `motion_blur` tail stamp along `-vel` (0 = off, parity-safe).
* `step_form` gained `boost` (audio energy → flow strength); rebuilt wheel.
* `engine/audio.py` (dep-free): `AudioDrive` (ffmpeg PCM → RMS envelope,
  beats ~1.0) + `SineDrive` (bpm pulse). `drift`/`form`/`scatter`/`flock` take
  `drive=`; `_draw` brightens stamps with `state["energy"]`.
* `Scene.render_loop(blend)` crossfades tail→head for seamless ambient loops.
  Verified first-last meandiff 1.57/255 (no pop). Fixed `LoopClip.render`
  override bug (overrode `render` while `render_loop` calls it → RecursionError).
* `Targets` base: `Bloom` (phyllotaxis, jitter 0.8/scale 0.46 after formless-cloud
  fix), `Branch` (recursive tree, trunk-first weighting fix, depth 7),
  `DLA` (batched walks + kill radius: gen 60s → 0.2s for 900 sticks; empty-grid
  guard). `form()` uses `order` attr when present, else x-sweep.
* `flock()`: grid-hash boids (same-cell separation + alignment, weak home spring).
  Verified: FLOCK/TOGETHER crisp with living dust.
* `scenes/showcase.py`: 8 preview clips (ember/scatter/bloom/branch/dla/flock/
  drive/loop), all frame-checked. README recipes added.
* Bench stays green (splat 36-43x exact; step 1.5x, ≤1.2e-04). Full draft +
  fallback + CLI preview re-verified after every engine change.

## 2026-09-12 — Hero reel + two engine bugfixes

* `scenes/hero.py`: 5-act capacity reel (ember hook / bloom→tree growth /
  DLA lightning / flock+scatter / beat-sync wordmark), concat to `hero.mp4`
  (25.3s, 960x540@30, ~30s wall). Every act frame-verified.
* **Bug: multi-form retarget.** `form()` closures read `self.targets/_nx/_dur`
  at render time, so a second `form()` silently retargeted the first phase
  (bloom phase grew the tree). Fixed: capture per-call copies in the closure.
  Same latent hazard noted for `flock()` (reads `self.*` live) — single use OK.
* **Bug: fps-dependent damping.** Per-frame `vel *= 0.985/0.93` made 30fps morphs
  slower than 15fps previews. Fixed: `damp=0.985**(dt*30)` through the fused
  kernel (new param, default preserves old 30fps behavior bit-exactly).
* Growth pacing measured: dist 339→97 (text), 313→79 (bloom), 355→139 (branch)
  over 2s — hero gives growth acts 2.6–2.8s.
* Parity re-verified after fixes: frames 0–120 bit-identical rust-vs-numpy,
  late sparkle grain ≤29 (same known 1e-4 drift, visually identical).

## 2026-09-12 — Ink reveal landing (particle-baked letters, default on)

* Uncommitted draft found: `Scene(reveal="ink"|"dots"|"solid")` + `splat_vals`
  kernel + persistent `self.ink` buffer baked by settled particles
  (`w=gain*exp(-d²/2σ²)`, triple `_blur3`, smoothstep to solid, sparkle on top).
  Finished + fixed it; no Rust change needed (`splat_vals` reuses `splat_add`).
* Bench: splat 34-48x exact; step 0.8-1.0x, ≤1.2e-04 (unchanged, green).
  `splat_vals` parity: bit-exact vs `np.add.at` @1500/10000 + fallback path.
* **Bugs found in draft, all fixed (`engine/api.py`):**
  1. Drift pre-ghost — deposits ran in every phase, so chance flybys hazed
     letters before form. Fix: bake only in form/flock/hold (drift ink ≡ 0).
  2. Unbounded accumulation — ink max hit 79, threshold meaningless across
     modes (final = 9x pixels would starve). Fix: `clip(ink,0,1)` per frame.
     Gain/σ grid (6-12 × 1.2-4.0) confirmed structural, not parametric.
  3. Wasted composite — blur+composite ran on empty ink every drift frame.
     Fix: skip when `ink.max() < 1e-3`.
  4. Multi-form ghost — bloom ink persisted under tree (same-scene form→form).
     Fix: form/flock closures set `state["ink_reset"]` on first step;
     `_draw` consumes it (`ink.fill(0)`). Verified: tree frame has no disc.
  5. Subtitle lost — 24px strokes can't bake from sparse ink (subt med 0.12
     vs title 0.57). Fix: `Text` now stores `sub_mask_np`; ink mode composites
     it crisply at closeness-gated `text_alpha` (dots mode zeroes it).
  6. `flock()` retarget hazard (log-noted): captured per-call copies
     (`_targ/_nx/_sw/_dur/_drv/_radius/_sep/_ali`) like `form()`.
* Verification: draft demo2 7.3s (ink path ~2x baseline 3.3s — blur+composite
  per form/hold frame; future fuse target), raw-frame rust-vs-numpy 64/64
  bit-identical incl. scatter dissolve, CLI preview OK (note: must run as
  `./.venv/bin/python oanim ...` — system python3 lacks imageio),
  all 8 showcase clips + hero ActGrowth frame-checked (flock ink+subtitle,
  scatter clean dissolve, bloom disc, tree no-ghost). `solid`/`dots` compat OK.
* Look: textured baked-ink title + crisp subtitle + sparkle; reveal still
  left-to-right, no pop. `demo2.png` regenerated.

## 2026-09-12 — Ink tuning + full close-out (defaults locked, verified, pushed)

* `tmp/` sprawl cleaned by user (52-frame dumps breached image-review budget).
  New protocol: max 3 mp4s + ≤4 PNGs per check, numeric-first, view ≤4.
* **Fix: `rust-core/rebuild.sh`.** maturin ran from repo root → `Can't find
  Cargo.toml`. Fix: `cd "$ROOT/rust-core"` before build, back after. Rebuild OK.
* Bench today: splat **42.8x@n1500, 42.3x@n4000, 37.6x@n10000** exact
  (2.4e-07 @10000); step **1.2x/1.0x/1.0x**, maxdpos 1.22e-04 (green).
* A/B/C re-rendered (preview, `GROWTH`): ink vs dots meandiff 8.9, ink vs
  solid 6.4, dots vs solid 5.0 (max ~234) — modes genuinely diverge. Dots too
  faint standalone, solid flat; ink stays default.
* Ink tuning probe (solid-fill/spill vs mask): early-form fill ≈ 0.0 all
  settings (no pre-ghost ✓). Grid: 1.2/0.35 → 0.69/0.024 (blotchy);
  1.0/0.50 → 0.45/0.010; locked **`ink_gain=1.0, ink_sharp=0.45`**
  (~0.5 fill, ~0.014 spill). 4 frames viewed (A/B/C + tuned).
* **Fix: `oanim` shebang** (`/usr/bin/env python3` = system py, no imageio).
  Now `#!/home/vishwanath/Desktop/exp/.venv/bin/python` — `./oanim render
  scenes/template.py --mode preview` works directly, CLI verified.
* Full verification: draft `demo2.py` 7.1s wall; fallback mp4 compare
  frames 0–120 bit-identical, late grain ≤24 (known 1e-4 drift); all 8
  showcase clips healthy (last-mean 12–18, max 255); hero re-rendered under
  final defaults — 25.3s, 26.7M, 38s wall. `demo2.png` + `hero.png`
  regenerated, both visually checked (textured, readable).

## 2026-09-12 — Gap close-out: final 1080p + vertical short + real audio

* **1080p needed a fix.** First `final` render (n=1500) came out starved —
  same particles over 4x pixels, thin faint letters. Two-part fix
  (`engine/api.py`): `ink_sigma` now draft-relative with auto-scale
  (`ink_sigma_eff = ink_sigma * min(w,h)/540` → 6/9/18 across modes) +
  particle rule `n=1500 preview/draft, n=4500 final` (README recipe).
  Probe: end solid-fill 0.59 preview / 0.61 final. Real final: 5.2s in
  31s wall, 14.6M, frame-checked — full textured letters, subtitle legible.
* **Vertical short: works, no fix.** `short_check.mp4` thumbnail looked like
  clipped "H" at small scale; numeric check overruled: mask x-range 72–641,
  ink 64–647, zero bright pixels past x=680 (40px margin). Shrink loop fits
  size 106 at 720 wide. Lesson logged: measure, don't eyeball thumbnails.
* **Real-file audio verified.** Synthesized `tmp/voice_test.wav` (speech-like
  phrases+gaps) → `AudioDrive` envelope 1.00 on phrases, ~0.01 in gaps;
  `show_voice.mp4` picture follows it (p99 119–165 phrase vs 77–83 gap).
  File-based beat-sync path closed (only `SineDrive` was proven before).
* Side effect noted: preview ink grain tightened slightly vs yesterday's
  A/B/C (sigma 9→6 eff; meandiff ~3.8, frame re-checked — looks as good or
  better). Draft/final behavior unchanged at 540p scale.   Showcase re-rendered
  (8/8), benches green (splat 45–48x exact; step ≤1.22e-04).

## 2026-09-12 — Personal workspace: my_videos/ + `./oanim new`

* Split tool vs. videos: `my_videos/` (user-owned, has its own README with
  3-step workflow + rules of thumb) vs. `engine/`/`scenes/`/`rust-core/`/`bench/`
  (tool, frozen). AGENTS.md + root README quickstart updated to match.
* `./oanim new <name>` scaffolds `my_videos/<name>.py` from
  `scenes/template.py` (sanitized name, CamelCase class, out default beside
  the script, `--force` guard). Verified scaffold + double-run guard.
* **Bug found by verification:** CLI `--out` default resolved against CWD,
  so renders landed in repo root. Fix: default is now beside the scene file
  (`my_videos/ep01.py` → `my_videos/ep01.preview.mp4`); explicit `--out`
  still wins. End-to-end proven (preview mp4+png healthy, frame 77 checked),
  test artifacts removed — `my_videos/` ships with README only.

## 2026-09-12 — Learning doc for personal use

* `my_videos/LEARN.md`: plain-language guide (big picture → 3 things you
  create → 5 moments → knobs → modes → recipes → troubleshooting → what not
  to touch). Fixed loop recipe to match real API (`construct()` +
  `render_loop()`). Linked from `my_videos/README.md`.
