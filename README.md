# oanim — living titles for storytellers

Code-driven organic motion graphics for YouTube. Users write tiny videos
(`Video` + plain moments like `drift`/`show`/`rest`), the engine renders
cinematic particle-flow title reveals to MP4. Rust accelerates hot loops
behind an identical Python API with numpy fallback.

## Quickstart (this folder only — nothing system-wide)

```sh
./oanim new ep01                              # scaffold my_videos/ep01.py
./oanim render my_videos/ep01.py --mode preview   # fast check
./oanim render my_videos/ep01.py --mode final     # 1080p upload
mpv my_videos/ep01.final.mp4
```

Your videos live in `my_videos/` (see its README). The tool
(`engine/`, `scenes/` examples, `rust-core/`, `bench/`) stays untouched.
Legacy demo: `./.venv/bin/python scenes/demo2.py` (renders `demo2.mp4`).

User starter: `./oanim new NAME` (writes `my_videos/NAME.py`):

```python
from engine.api import Video

class MyVideo(Video):
    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6)
        self.rest(1.0)
```

## Layout

* `engine/api.py` — user API + renderer (`Video` moments, `Shape`s, modes)
* `engine/_core.py` — Rust fast path with numpy fallback (`OANIM_CORE=off` forces numpy)
* `rust-core/` — PyO3 extension `oanim_core` (`splat_add`, `splat_add_glow`, abi3)
* `rust-core/rebuild.sh` — rebuild wheel + reinstall + bench (one command)
* `scenes/` — `template.py` (starter), `demo2.py`, `showcase.py`, `hero.py`
* `my_videos/` — personal videos (never touch during engine work)
* `tmp/` — ALL temp output: renders, wheels, cargo/rustup/uv-python toolchains, caches
* `logs/` — session log with decisions + numbers (read before changing things)
* `bench/` — parity/benchmark scripts

## Render modes

`preview` 640x360@15 · `draft` 960x540@30 · `final` 1920x1080@30 · `short` 720x1280@30.
Every render also writes a `.png` thumbnail next to the mp4.

## Recipes (copy-paste)

Hook intro (ember + streaks + push-in):
```python
self.mood("ember", trails=0.6, zoom=1.07, shake=1.5)
self.drift(1.6); self.show("TITLE", "SUB", 2.6); self.rest(1.0)
```
Section card: `show("CHAPTER 2", tracking=20, wave=1.2)` + thin weight.
Final 1080p: dots picked by size, nothing to remember (`dots = 900` to force).
Vertical Short: `--mode short` just works; title auto-shrinks to fit 720 wide.
Real voiceover: one line `self.music("vo.wav")` at the top of `build()`.
Subscribe outro: `show(...)` then `rest(...)` then `burst(1.4)`.
Follow title: `follow("FLOCK", "TOGETHER", 3.0)` — dust moves after each other.
Growth interstitials: `grow(Bloom())`, `grow(Branch(depth=7))`, `grow(Lightning(pieces=900))`.
Beat-synced: `pulse(132)` for practice; brightness + flow follow the beat.
Ambient bed: `drift(60)` + `render_loop(blend=0.6)` for a seamless loop.
All showcase clips: `./.venv/bin/python scenes/showcase.py` (preview, in `tmp/`).

## Environment facts (do not assume otherwise)

* No dGPU. AMD 680M iGPU, Mesa has **no VAAPI encode profiles** — CPU libx264 is the path.
* System Python 3.14 has **no `-devel` headers** and no gcc. Rust builds use:
  `tmp/uv-python` (build interpreter with headers) + zig linker from `.venv`.
* Toolchain env (see `rust-core/rebuild.sh`): `RUSTUP_HOME`/`CARGO_HOME`/`TMPDIR`/`PIP_CACHE_DIR`
  all point inside `tmp/`. Crates vendored in `tmp/vendor` (offline builds work).
