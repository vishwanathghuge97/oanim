# Learn oanim in 15 minutes (plain language, no jargon)

You write a few lines describing **what happens when**.
The tool turns it into a video. That's the whole idea.

## 1. The big picture

Every video is a list of **moments**, played one after another:

```python
self.play(dots.drift(1.6))       # moment 1: dust wanders (1.6 seconds)
self.play(dots.form(title, 2.6)) # moment 2: dust gathers into your title (2.6 s)
self.play(self.hold(1.0))        # moment 3: title rests, breathing (1.0 s)
```

Think of it like directing: *"first wander, then gather, then rest."*
Total length = 1.6 + 2.6 + 1.0 = 5.2 seconds.

## 2. The only 3 things you create

```python
title = Text("GROWTH", subtitle="ORGANIC MOTION",
             weight="Light", tracking=16)
dots = FlowParticles(n=1500, seed=7)
```

| Thing | What it is | What you change |
|---|---|---|
| `Text` | The words the dust will become | Your title + subtitle. `tracking` = spacing between letters (bigger = airier). `weight` = thickness (`Thin`/`Light`/`Regular`) |
| `FlowParticles` | The dust itself (1500 tiny dots) | `n` = how many dots. `seed` = which random pattern (change it for a fresh look, same words) |
| `self.play(...)` | One moment in your video | The order + the seconds. That's your timeline |

## 3. The 5 moments you can use

| Moment | What the viewer sees | Example |
|---|---|---|
| `drift(seconds)` | Dust wandering, no words. Use at the start | `dots.drift(1.6)` |
| `form(title, seconds)` | Dust flies together and **becomes your words** | `dots.form(title, 2.6)` |
| `hold(seconds)` | Words rest on screen, gently alive | `self.hold(1.0)` |
| `scatter(seconds)` | Words burst apart back into dust. Use at the end | `dots.scatter(1.4)` |
| `flock(title, seconds)` | Like `form`, but the dust moves like a flock of birds | `dots.flock(title, 3.0)` |

A full video is usually: `drift` → `form` → `hold` → (optional `scatter`).

## 4. The knobs you'll actually touch

**Title look** — inside `Text(...)`:
- `tracking=16` → letter spacing. Titles like 14–22. Bigger feels calm and premium.
- `weight="Light"` → thickness. Keep `Light` unless you have a reason.

**Gathering feel** — inside `form(...)`:
- `sweep=0.9` → letters appear left-to-right. `0` = all at once, `1.2` = slow wave.
- `k=46, c=7.2` → how the dust flies. Defaults are good. `k=60, c=9` = snappy, `k=28, c=5.5` = jelly.

**Mood** — when creating the scene (top of file, `MyVideo(out=..., mode=..., theme=...)`):
- `theme=` → `ink` (default, moonlight), `ember` (warm fire), `bone` (grey), `moss` (green).
- `motion_blur=0.6` → streaky trails (great with `ember`, leave `0` otherwise).
- Camera: `Camera().push_in(1.0, 1.07).handheld(1.5)` → slow zoom + tiny shake. Delete the line for a still camera.

**Dust amount** — inside `FlowParticles(...)`:
- Preview/draft: `n=1500`. Final 1080p: `n=4500`. (Bigger screen needs more dust. That's the only rule.)

**Music/voice sync:**
```python
from engine.api import Scene, Text, FlowParticles
from engine.audio import SineDrive, AudioDrive

drv = SineDrive(bpm=132)        # fake pulse, no file needed
drv = AudioDrive("vo.wav")      # your real voiceover/music file
self.play(dots.drift(2.0, drive=drv))  # pass drive=drv to any moment
self.play(dots.form(title, 2.6, drive=drv))
```
Motion and brightness now follow the sound.

## 5. Render modes (which button to press)

```sh
./oanim render my_videos/ep01.py --mode preview   # tiny, seconds — while writing
./oanim render my_videos/ep01.py --mode draft     # judge the real look here
./oanim render my_videos/ep01.py --mode final     # 1080p, remember n=4500 — once
./oanim render my_videos/ep01.py --mode short     # vertical 720x1280 for Shorts
```

Golden rule: **preview while writing, draft to judge, final once.**

## 6. Copy-paste recipes

**Warm hook intro:**
```python
self = MyVideo(out="intro.mp4", mode="draft", theme="ember", motion_blur=0.6)
# ... Camera().push_in(1.0, 1.07).handheld(1.5)
self.play(dots.drift(1.6)); self.play(dots.form(title, 2.6)); self.play(self.hold(1.0))
```

**Chapter card:** `Text("CHAPTER 2", weight="Thin", tracking=20)` + `form(..., sweep=1.2)`.

**Burst outro:** after `form`, add `self.play(dots.scatter(1.4, power=340))`.

**Growing tree / lightning (no words):**
```python
from engine.api import Bloom, Branch, DLA
self.play(dots.form(Bloom(), 2.6))            # flower bloom
self.play(dots.form(Branch(depth=7), 2.8))    # growing tree
self.play(dots.form(DLA(sticks=900), 2.4))    # lightning/coral
```

**Seamless looping background** (for ambient beds under voiceover):
```python
self.play(dots.drift(60))   # long wander, no words
# run it with render_loop instead of a normal render:
#   s = MyScene(out="bed.mp4", mode="draft"); s.construct(); s.render_loop(blend=0.6)
```

## 7. When something looks wrong

| You see | It means | Fix |
|---|---|---|
| Letters thin/faint in final 1080p | Too few dots for 4x pixels | `n=4500` |
| Title too wide / cut off | Long word on narrow screen | Short mode auto-shrinks; or shorten word, or lower `tracking` |
| Motion ignores your music | Forgot `drive=` | Pass `drive=drv` to `drift`/`form` |
| Same boring dust every time | Same seed | Change `seed=` — free new variation |
| Error about ffmpeg | Audio file missing/bad | Check the `vo.wav` path; preview without `drive` first |

## 8. What NOT to touch

`engine/`, `scenes/`, `rust-core/`, `bench/` = the tool.
If a recipe says "see `scenes/showcase.py`" — open it, read, copy the idea into
YOUR file. Never edit those files. If the tool truly needs a change, that's a
separate conversation — your videos in `my_videos/` are always safe.
