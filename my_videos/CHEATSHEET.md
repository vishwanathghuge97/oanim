# CHEATSHEET — every function on one page

Pin this. Each row: **what it is in plain words**, its inputs, one tiny
example. Defaults are marked `=`. All examples below run (they come from
the lessons and `build_demo.py`).

## Make things (the nouns)

| Write this | Plain meaning | Inputs |
|---|---|---|
| `Text("OCEAN", subtitle="MY FIRST BUILD", weight="Light", tracking=18)` | The words the dust becomes. | `title` (required, big word) · `subtitle="ORGANIC MOTION"` (small line) · `weight="Light"` (`Thin`/`Light`/`Regular` = thin/normal/thick) · `tracking=14` (letter space, try 14–22) · `seed=7` |
| `FlowParticles(n=1500, seed=7)` | The dust — `n` moving dots. | `n=1500` (practice) / `n=4500` (final 1080p) · `seed=7` (which random pattern — change for a new look) |
| `Scene(out=..., mode="draft", theme="ink", motion_blur=0.0)` | The video itself + its settings. You get this free from `./oanim new`. | `mode="draft"` (`preview` fast / `draft` judge / `final` 1080p / `short` vertical) · `theme="ink"` (`ink` moonlight / `ember` fire / `bone` grey / `moss` green) · `motion_blur=0.0` (trails; try `0.6`) · `reveal="ink"` (how letters appear; leave it) |

Always hand words + dust to the video (forget = black screen):
```python
self.particles = dots
self.text_obj = title
```

## Moments (the verbs — your timeline)

| Write this | Plain meaning | Inputs |
|---|---|---|
| `dots.drift(1.6)` | Dust wanders. No words. Start here. | `duration=1.8` (seconds) |
| `dots.form(title, 2.6, sweep=0.9)` | Dust gathers INTO words (or a shape). The main event. | `title` (required) · `duration=2.4` · `sweep=1.1` (letter wave: `0` together … `1.2` slow wave) · `k=46.0, c=7.2` (fly feel — leave alone; snappy `60, 9`, jelly `28, 5.5`) |
| `dots.flock(title, 2.6)` | Like `form`, but dust flies like birds. | Same as `form` (`duration=3.0`, `sweep=1.0`) |
| `self.hold(1.0)` | Words rest on screen, gently alive. | `duration=1.0` |
| `dots.scatter(1.4, power=340.0)` | Words burst back into dust. End here. | `duration=1.6` · `power=300.0` (burst strength: `150` sigh … `600` explosion) |

Chain anything after anything — words can melt into flowers:
```python
self.play(dots.form(title, 2.2))                 # words appear
self.play(dots.form(Bloom(scale=0.44), 2.2))     # words melt into a flower
self.play(dots.scatter(1.2))                     # flower bursts
```

## Shapes (instead of words in `form`)

| Write this | Plain meaning | Inputs |
|---|---|---|
| `Bloom(scale=0.46, jitter=0.8)` | A flower that grows. | `scale=0.40` (size) · `jitter=2.0` (rough edge: lower = neat) |
| `Branch(depth=7, seed=11)` | A tree that grows. | `depth=9` (branches: 7 bushy … 9 fine) |
| `DLA(sticks=900, seed=13)` | Lightning / coral crackle. | `sticks=2200` (pieces: 900 fast … 2200 rich) |

```python
from engine.api import Bloom, Branch, DLA
self.play(dots.form(Branch(depth=7, seed=11), 2.8))
```

## Beat (motion follows sound)

| Write this | Plain meaning | Inputs |
|---|---|---|
| `SineDrive(bpm=132)` | Fake pulse for practice. No file needed. | `bpm=100.0` (speed) |
| `AudioDrive("vo.wav")` | YOUR sound file drives the motion. | `path` (required) · `gain=1.0` (louder motion if raised) |

Plug into any moment with `drive=`:
```python
from engine.audio import SineDrive, AudioDrive
beat = SineDrive(bpm=132)
self.play(dots.drift(1.0, drive=beat))
self.play(dots.form(title, 1.6, drive=beat))
```
Louder beat = stronger flow + brighter dots. (Sound is NOT saved into the
mp4 — add music in your editor.)

## Camera (one line, delete for a still shot)

| Write this | Plain meaning | Inputs |
|---|---|---|
| `Camera().push_in(1.0, 1.06).handheld(1.2)` | Slow zoom in + tiny shake. | `push_in(from, to)` zoom · `pull_out(from, to)` zoom out · `handheld=2.0` shake amount (`0` still) |

```python
from engine.api import Camera
self.attach_camera(Camera().push_in(1.0, 1.06).handheld(1.2))
```

## Sizes (how sharp / which shape)

| Mode | Size | Use it for |
|---|---|---|
| `preview` | 640×360, 15fps | Writing (seconds per render), `n=1500` |
| `draft` | 960×540, 30fps | Judging the real look, `n=1500` |
| `final` | 1920×1080, 30fps | Uploading (~30s per 5s video), `n=4500` |
| `short` | 720×1280, 30fps | Vertical Shorts (title auto-shrinks) |

## Commands (terminal)

```sh
./oanim new myvideo                              # new file my_videos/myvideo.py
./oanim render my_videos/myvideo.py --mode preview   # fast check
./oanim render my_videos/myvideo.py --mode draft     # judge
./oanim render my_videos/myvideo.py --mode final     # 1080p upload
./oanim render my_videos/myvideo.py --mode short     # vertical
./oanim render my_videos/myvideo.py --mode draft --out tmp/try.mp4  # custom output
```

## Numbers to memorize (only 5)

1. `n=1500` practice, `n=4500` final. 2. `sweep`: `0` together … `1.2` slow wave.
3. `power`: `150` sigh … `600` explosion. 4. `tracking`: 14 tight … 22 airy.
5. Modes: preview → draft → final, in that order.
