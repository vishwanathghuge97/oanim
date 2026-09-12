# REFERENCE — facts only, no lessons

Look up values here. Learn in `01_LEARN.md`. Do jobs in `02_TASKS.md`.

## Your video

`class Mine(Video):` + `def build(self):` with moment lines.
`Video(save=..., mode="preview", encoder="cpu", thumbnail=True)`
`seed = 21` / `dots = 900` lines in your class (same number = same film;
dots picked by size if you skip it: 1500 practice, 2600 short, 4500 final).

## Moments

`drift(seconds)` — dust wanders, no words.
`show(title, subtitle="", duration=2.6, wave=0.9, tracking=16, weight="Light")` — words appear.
`grow(shape, duration=2.4, wave=1.0)` — a shape grows.
`follow(shape or "WORDS", subtitle="", duration=3.0, wave=1.0, tracking=16)` — dust moves after each other, then settles.
`rest(seconds)` — words rest.
`burst(seconds, strength=340.0)` — words burst into dust (`150` sigh … `600` boom).

## Feeling

`mood("ink")` — moonlight (default). `"ember"` fire · `"bone"` grey · `"moss"` green.
`mood("ember", trails=0.6, zoom=1.06, shake=1.2)` — trails `0` off … `~1` strong; zoom-in + tiny shake.
`music("vo.wav")` — your sound drives all moments. `pulse(132)` — fake beat for practice.

## Shapes (inside `grow`, or `follow`)

`Bloom(scale=0.40, jitter=2.0, seed=7)` — flower.
`Branch(depth=9, spread=0.55, shrink=0.74, seed=7)` — tree.
`Lightning(pieces=2200, seed=7)` — lightning.
Own shape: subclass `Shape`, write `points(n)` returning dots + `self.order`. See `neuron_sun.py`.

## Sizes

`preview` 640×360@15 · `draft` 960×540@30 · `final` 1920×1080@30 · `short` 720×1280@30.

## Commands

`./oanim new NAME` · `./oanim render FILE --mode preview|draft|final|short`
`--out PATH` (default: beside the script).
`Video.render_loop(blend=0.6)` for seamless loops (call after `build()`, not `run()`).
