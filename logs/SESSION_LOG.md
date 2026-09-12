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

## 2026-09-12 — Real course docs: LEARN.md rebuilt as 7 runnable lessons

* User verdict: old LEARN.md was an overview, not teaching. Rebuilt as a
  course: L0 vocabulary → L1 first render → L2 your words → L3 timeline +
  scatter → L4 mood (ember/blur/camera) → L5 seed/sweep → L6 Bloom growth →
  L7 beat drive → graduation upload checklist. Every lesson: goal, exact
  file, exact command, real rendered frame, things to notice, exercise,
  checkpoint. Troubleshooting table kept + honest notes (tool never mixes
  audio; scripts must live in `my_videos/` for the import path).
* Proof, not claims: all 7 lesson files live in `my_videos/lessonN.py` and
  each was rendered via the exact documented CLI flow (outputs beside
  scripts, since removed). Frames in `my_videos/learn_frames/` (7 PNGs,
  committed like demo2.png). Cross-checks: doc-file renders bit-identical
  to independent runs (meandiff 0.000 ×3 pairs); full-file block (L2)
  verbatim in doc; 11 excerpt lines substring-verified against lesson files.
* L3/L4 frames visually confirmed (radial burst mid-scatter; ember trails +
  crisp subtitle). Tmp lesson scaffolding removed.

## 2026-09-12 — Docs v2: plain words + BUILD guide + CHEATSHEET

* User verdict: docs used heavy words, missed function meanings, no
  from-zero path, no cheatsheet; old fragmented docs had to go.
* New set in `my_videos/`: `LEARN.md` (course, simplified: scaffolding→
  setup lines, flavors→kinds, loop recipe fixed earlier), `BUILD.md`
  (from-zero in 6 steps: paper plan → words → dust → moments one at a
  time → mood → draft/final; 3 ready patterns; playground rules),
  `CHEATSHEET.md` (every function: plain meaning + inputs/defaults + tiny
  example; 5 numbers to memorize). README rewritten as a 10-line index
  (old content folded in, not lost).
* Proof: `build_demo.py` (words→flower→burst, kept runnable) rendered via
  documented flow; frame `learn_frames/build_bloom.png` committed. All 12
  BUILD step lines substring-verified against the file (caught a drift:
  camera line was doc-only → added to the file, re-rendered, frame updated).
  Cheatsheet defaults cross-checked to engine signatures (Text tracking=14,
  flock radius/sep/ali, MODES sizes, Scene kwargs); all lesson/demo files
  compile-clean.

## 2026-09-12 — Personal video: NEURON SUN + engine retarget fix

* `my_videos/neuron_sun.py` (18.1s): drift 5s void → flock into custom
  `Neuron` target (soma ball + 11 dendrite arms, center-out order) → hold →
  `form(PlaneSheet)` flat band → hold → `scatter` → `form(SunSystem)` (dense
  sun + 3 ring-dust + planet blobs, inside-out order) → hold. Custom
  `Targets` use `engine.api` W/H at call time (import-by-value goes stale).
* **Engine bug (same retarget family as form/flock): `hold()` and
  `scatter()` read `self.particles.targets/_nx` LIVE at render time, but
  construct() runs all lines upfront — so every hold/scatter silently used
  the LAST form's targets. Symptom in footage: sun disc+rings ghosted over
  the neuron hold and sheet hold (looked like unconverged particles; probe
  proved positions were perfect, mp4 disagreed → hold spring pulled toward
  sun targets). Fix: both capture creation-time copies. Parity re-verified
  (demo2 frames 0–120 identical, ≤24 late grain); showcase 8/8 + hero
  re-rendered healthy (hero.mp4 size shifted slightly = multi-form acts now
  correct; `hero.png` regenerated).
* Neuron tuning: soma n//4 blew out white → n//6 + wider (R*0.06); arms now
  read. Delivered `my_videos/neuron_sun.draft.mp4` (15.5M) + thumbnail,
  sun/neuron/sheet frames checked in draft.

## 2026-09-12 — Junk removal (~1GB freed, verified harmless)

* `tmp/`: deleted ~30 stale mp4s + ~50 frame PNGs + test wav + hero_list.txt
  (all regenerable; showcase 2min, hero 38s) + emptied `pip-cache` (158M)
  + removed `rust-target` (106M). Kept toolchains: rustup/cargo-reg/uv-python
  /vendor/wheels/zig-cc.sh. tmp 1.8G → 762M.
* `__pycache__` dirs removed; unused `import runpy` dropped from `oanim`.
* Kept deliberately: root demo1/2/hero mp4s (user watches them),
  `engine/mini.py` + `scenes/demo1.py` (linked working pair),
  `smoothstep`/`_ss01` (both live), `pull_out` (public API, documented).
* Verified after: full from-scratch `rebuild.sh` OK, splat bench 42–47x
  exact, CLI `new`+`render` OK, preview render OK, compile-all clean.

## 2026-09-12 — Docs v3: Diátaxis revamp in very simple English

* User verdict: still not good + direction: study real doc practice first.
  Researched Diátaxis (tutorials/how-to/reference/explanation split —
  Cloudflare/Gatsby use it) + Stripe lessons (quickstart first, runnable
  samples, error-handling section, findable single pages). Diagnosis: our
  files mixed teaching + tasks + facts in each file — that blur was the
  confusion.
* New shape in `my_videos/`: `START.md` (3 doors + 5-min first video on the
  page), `LEARN.md` (pure tutorial path, explanations moved out),
  `TASKS.md` (goal-first jobs + FIX-IT table + 3 learning rules),
  `REFERENCE.md` (dry facts only), `IDEAS.md` (short why, plain words).
  `BUILD.md`/`CHEATSHEET.md` deleted (split into TASKS/REFERENCE).
  Sentence rule: short, present tense, define each new word on first use.
* Proof kept: new `task_chapter.py` rendered (chapter frame committed);
  TASKS chapter lines + L2 full block + 11 LEARN excerpts verified against
  files; all 9 doc frames exist; compile-clean.

## 2026-09-12 — Workspace split: course/ vs my_videos/

* User verdict: `my_videos/` was a scary 19-file dump (lessons + docs +
  own video mixed). Fix: teaching material moved to `course/` (5 docs +
  7 lessons + build_demo + task_chapter + learn_frames); `my_videos/`
  keeps only README + user's `neuron_sun.*`. README rewritten as tiny
  index pointing at `../course/START.md`; `course/README.md` added;
  AGENTS.md notes course files are runnable teaching material.
* Path fixes: doc commands now `course/lessonN.py`; FIX-IT row covers both
  folders (scripts must live one level below root). `oanim new` unchanged.
* Refresh forced by move check: re-render from `course/` differed from
  committed frames (meandiff 2.4 — frames predated sigma auto-scale +
  hold/scatter capture fix). Re-rendered all 9 frames from current engine,
  l1 visually confirmed. Moved-file render verified via CLI (outputs land
  in `course/`, compile-clean).
* Follow-up hunt (l4 old-vs-new diff 10.6 looked suspicious): renders are
  bit-identical run-to-run on one binary, but numpy-fallback matches NEW
  (0.42) not OLD (10.58) — old frame was pre-rebuild rayon-scheduling luck,
  new is correct behavior. Same known 1e-4→ink-amplified grain family as
  the logged late-frame sparkle; parity promise holds per-binary. Added one
  honest line to `course/IDEAS.md` (your grain may differ slightly).

## 2026-09-12 — One API in plain words (clean break, no duplication)

* User rules: single way to do everything, no kept-old names (no outside
  users to protect), built from user words. Replaced, not added alongside.
* New surface (`engine/api.py`): `Video` + verbs `drift/show/grow/follow/
  rest/burst/mood/music/pulse` (+`play`), `Shape` base with `points()` +
  `order`, `Bloom/Branch/Lightning` (`DLA(sticks)`→`Lightning(pieces)`).
  Dots auto by size (1500/1500/2600/4500), `seed=`/`dots=` as class lines
  or ctor args. Beat set once per video. `save=` replaces `out=`, default
  mode `preview`. Empty `build()` prints a plain message, not a traceback.
  Old names gone (underscore insides: `_Text/_Dust/_Camera/_Pulse/_Audio`);
  kernels, audio math, Rust untouched.
* Migrated everything: scenes (template/demo2/showcase/hero), course
  (7 lessons + build_demo + task_chapter, now tiny), neuron_sun (custom
  Shapes use `points()`), oanim (finds `Video`, `.run()`, preview default,
  fixed scaffold docstring bug found by reading output). Deleted
  `engine/mini.py`, `scenes/demo1.py`, `demo1.mp4` (dead era).
* Proof: demo2 new-vs-old-API **bit-identical all 156 frames**; hero acts
  1–4 identical, act 5 re-baselined (zoom start 1.02→1.0, intentional);
  7/9 lesson frames identical (l4 = known rebuild luck, build = bugfix
  now correct); fallback identical to frame 120 (≤24 grain); benches
  green; scaffold→render→cleanup loop verified; zero old names in user
  files, docs, or engine surface (grep-proven). Docs rewritten to new API
  with snippet checks green. `oanim new` default template is the 3-line
  video now.

## 2026-09-12 — Perf Q&A: where render time really goes (measured)

* User asked if the engine is slow. Profiled draft/n=1500 per-frame means:
  sim 0.07–0.81ms (drift/form/hold/scatter/flock) vs `_draw` 23–57ms.
  Ink composite adds ~34ms over dots baseline (~25ms); solid +14ms;
  n=100→4500 changes draw by only ~1ms (per-PIXEL bound, not per-particle);
  camera ~1–2ms; x264 append ~1.6ms. Conclusion: sim ≈1%, pixel
  compositing ≈96% — the Rust particle engine is fast, Pillow/numpy
  full-frame ops (esp. triple `_blur3` + composite + sparkle) set the pace.
* Headline: `neuron_sun` 18.1s draft in 23.5s wall (0.77x realtime).
  Feels slow because progress prints every 30 frames with no ETA and every
  mode re-renders from scratch. Candidate future win (not done): fuse
  colormap+composite into Rust (already the logged next target); x264
  preset tuning is pointless (1.6ms). More particles are nearly free.

## 2026-09-12 — Docs wiped by user request

* User rejected learning docs three times; asked to wipe them completely.
  Deleted all 7 learning pages (`course/00_START,01_LEARN,02_TASKS,
  03_REFERENCE,04_IDEAS`, `course/README`, `my_videos/README`) + stray
  render/`__pycache__` leftovers. No stale references remain (grep-clean).
  Kept: tool, runnable lesson/example `.py` films, `learn_frames/`,
  videos, root README (repo front page), AGENTS.md, this log. All
  recoverable from git. Lesson: for this user, docs only on explicit ask,
  one page max, plain words.

## 2026-09-12 — Best docs rebuilt (new API, Diátaxis, proven snippets)

* User asked for the best documentation possible. Rebuilt the wiped set on
  everything learned: numbered doors (00 first, one next step each),
  Diátaxis split (START/LEARN/TASKS/REFERENCE/IDEAS), very simple English,
  new one-way API throughout, no old names anywhere (grep-clean).
* Proof kept: L2 full block verbatim in doc; 13/13 excerpt lines match
  files exactly (one fix: flower line now carries `wave=0.8` like the
  file); all 9 frames exist and current; compile-clean. Docs reference
  only files that exist; no dangling links.
