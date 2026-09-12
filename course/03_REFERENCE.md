# REFERENCE — facts only, no lessons

Look up values here. Learn in `01_LEARN.md`. Do jobs in `02_TASKS.md`.

## Things

`Text(title, subtitle="ORGANIC MOTION", seed=7, weight="Light", tracking=14)`
`FlowParticles(n=1500, seed=7)`
`Scene(out=..., mode="draft", encoder="cpu", thumbnail=True, theme="ink", motion_blur=0.0, reveal="ink", ink_gain=1.0, ink_sharp=0.45, ink_sigma=9.0)`

## Moments

`drift(duration=1.8, drive=None)`
`form(text, duration=2.4, sweep=1.1, k=46.0, c=7.2, drive=None)`
`flock(text, duration=3.0, sweep=1.0, drive=None, radius=26.0, sep=90.0, ali=0.9)`
`hold(duration=1.0)`
`scatter(duration=1.6, sweep=0.8, power=300.0, drive=None)`

## Looks

`theme`: `ink` / `ember` / `bone` / `moss`. `motion_blur`: `0.0` off … `~1.0` strong.
`reveal`: `ink` / `dots` / `solid` (default `ink`, leave it).
`Camera().push_in(z0=1.0, z1=1.08)` · `.pull_out(z0=1.08, z1=1.0)` · `.handheld(amp=2.0)`

## Shapes (use inside `form` instead of `Text`)

`Bloom(scale=0.40, jitter=2.0, seed=7)`
`Branch(depth=9, spread=0.55, shrink=0.74, seed=7)`
`DLA(sticks=2200, seed=7)`

## Beat

`SineDrive(bpm=100.0, base=0.25, amp=0.75)`
`AudioDrive(path, sr=22050, win=0.12, gain=1.0)` — plug in with `drive=`.

## Sizes

`preview` 640×360@15 · `draft` 960×540@30 · `final` 1920×1080@30 · `short` 720×1280@30.
Practice `n=1500`, final `n=4500`.

## Commands

`./oanim new NAME` · `./oanim render FILE --mode preview|draft|final|short`
`--out PATH` (default: beside the script) · `--encoder cpu|vaapi` (vaapi dead on this machine, `cpu` works)
`Scene.render_loop(blend=0.6)` for seamless loops (call after `construct()`, not `construct_and_render()`).
