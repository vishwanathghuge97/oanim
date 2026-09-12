# oanim — living titles for storytellers

Code-driven organic motion graphics for YouTube. Users write Python
(`Scene`/`Text`/`FlowParticles`), the engine renders cinematic
particle-flow title reveals to MP4. Rust accelerates hot loops behind an
identical Python API with numpy fallback.

## Quickstart (this folder only — nothing system-wide)

```sh
./.venv/bin/python scenes/demo2.py        # render 5s draft -> demo2.mp4
./oanim render scenes/template.py --mode preview --out tmp/x.mp4
./oanim render scenes/template.py --mode short --out tmp/short.mp4
mpv demo2.mp4
```

User starter: copy `scenes/template.py`.

```python
from engine.api import Scene, Text, FlowParticles, Camera

class MyVideo(Scene):
    def construct(self):
        title = Text("GROWTH", subtitle="ORGANIC MOTION",
                     weight="Light", tracking=16)
        dots = FlowParticles(n=1500, seed=7)
        self.particles = dots
        self.text_obj = title
        self.attach_camera(Camera().push_in(1.0, 1.07).handheld(1.5))
        self.play(dots.drift(duration=1.6))
        self.play(dots.form(title, duration=2.6, sweep=0.9))
        self.play(self.hold(duration=1.0))
```

## Layout

* `engine/api.py` — user API + renderer (`Scene`, `Text`, `FlowParticles`, `Camera`, modes)
* `engine/_core.py` — Rust fast path with numpy fallback (`OANIM_CORE=off` forces numpy)
* `engine/mini.py` — legacy low-level core (demo1 only, do not extend)
* `rust-core/` — PyO3 extension `oanim_core` (`splat_add`, `splat_add_glow`, abi3)
* `rust-core/rebuild.sh` — rebuild wheel + reinstall + bench (one command)
* `scenes/` — `template.py` (starter), `demo1.py`, `demo2.py`
* `tmp/` — ALL temp output: renders, wheels, cargo/rustup/uv-python toolchains, caches
* `logs/` — session log with decisions + numbers (read before changing things)
* `bench/` — parity/benchmark scripts

## Render modes

`preview` 640x360@15 · `draft` 960x540@30 · `final` 1920x1080@30 · `short` 720x1280@30.
Every render also writes a `.png` thumbnail next to the mp4.

## Recipes (copy-paste)

Hook intro (ember + streaks + push-in):
```python
self = MyScene(out="intro.mp4", mode="draft", theme="ember", motion_blur=0.6)
# ... attach Camera().push_in(1.0, 1.07).handheld(1.5)
self.play(dots.drift(1.6)); self.play(dots.form(title, 2.6)); self.play(self.hold(1.0))
```
Section card: `Text("CHAPTER 2", weight="Thin", tracking=20)` + `form(..., sweep=1.2)`.
Subscribe outro: `form()` then `scatter(1.4, power=340)` back into flow.
Flock title: `dots.flock(title, 3.0)` instead of `form()` — streaming boids.
Growth interstitials: `form(Bloom())`, `form(Branch(depth=7))`, `form(DLA(sticks=900))`.
Beat-synced: `drv = SineDrive(bpm=132)` (or `AudioDrive("vo.wav")`), pass `drive=drv`
to `drift`/`form`; brightness + flow follow energy. No extra deps (ffmpeg + numpy).
Ambient bed: `drift(60)` + `render_loop(blend=0.6)` for a seamless loop.
Stiffer/softer settle: `form(..., k=60, c=9)` snappy, `k=28, c=5.5` jelly.
All showcase clips: `./.venv/bin/python scenes/showcase.py` (preview, in `tmp/`).

## Environment facts (do not assume otherwise)

* No dGPU. AMD 680M iGPU, Mesa has **no VAAPI encode profiles** — CPU libx264 is the path.
* System Python 3.14 has **no `-devel` headers** and no gcc. Rust builds use:
  `tmp/uv-python` (build interpreter with headers) + zig linker from `.venv`.
* Toolchain env (see `rust-core/rebuild.sh`): `RUSTUP_HOME`/`CARGO_HOME`/`TMPDIR`/`PIP_CACHE_DIR`
  all point inside `tmp/`. Crates vendored in `tmp/vendor` (offline builds work).
