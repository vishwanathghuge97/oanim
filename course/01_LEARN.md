# LEARN — 7 small lessons (~40 minutes)

Do them in order. Each one: run a file, look, change one thing.
Files `lesson1.py` … `lesson7.py` are in this folder. They all run.
Every picture is a real frame from running them.

---

## Lesson 0 — three lines (2 minutes, no running)

Open `lesson1.py`. The whole video is this:

```python
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6)
        self.rest(1.0)
```

- `show(...)` = your words. The line holds the title, the small line, the seconds.
- `drift` / `rest` = the time plan. Wander 1.6s, words 2.6s, rest 1.0s.

Words + moments. That is all there is. Go to Lesson 1.

---

## Lesson 1 — run it (5 minutes)

Goal: see the tool work.

```sh
./oanim render course/lesson1.py --mode preview
```

Open `course/lesson1.preview.mp4`. The end looks like this:

![Lesson 1](learn_frames/l1_first.png)

Look for: grainy dust letters. Small subtitle line. A few dots still
floating. Alive, not frozen.

Run once more with `--mode draft` (same video, sharper). Rule from now on:
preview while you work, draft to judge, final once. Next lesson.

---

## Lesson 2 — your words (5 minutes)

Goal: your words on screen. Open `lesson2.py`. One line holds everything:

```python
        self.show("DREAM", "EPISODE ONE", 2.6, tracking=18)
```

```sh
./oanim render course/lesson2.py --mode preview
```

![Lesson 2](learn_frames/l2_words.png)

Change `"DREAM"` to one of your words. Run again. Your word gathers from
dust. Full file below (copy it if you want your own copy):

```python
"""Lesson 2: your own words."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson2(Video):
    def build(self):
        self.drift(1.6)
        self.show("DREAM", "EPISODE ONE", 2.6, tracking=18)
        self.rest(1.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson2.preview.mp4"))
    Lesson2(save=out, mode="preview").run()
```

Next lesson.

---

## Lesson 3 — words burst at the end (5 minutes)

Goal: add a moment. Open `lesson3.py`. New last line:

```python
        self.burst(1.4)
```

`burst` blows words back into dust. Good for endings.

```sh
./oanim render course/lesson3.py --mode preview
```

Mid-burst looks like this:

![Lesson 3](learn_frames/l3_outro.png)

Change it to `self.burst(1.4, strength=600.0)`. Run. Wild burst. Change to
`strength=150.0`. Soft sigh. That number is the burst strength. Next lesson.

---

## Lesson 4 — warm mood (5 minutes)

Goal: same words, new feeling. Open `lesson4.py`. New first line:

```python
        self.mood("ember", trails=0.6, zoom=1.06, shake=1.2)
```

One line sets warm colors, light trails, slow push-in.

```sh
./oanim render course/lesson4.py --mode preview
```

![Lesson 4](learn_frames/l4_mood.png)

Warm orange. Streaky trails. Slow push-in. Delete the mood line and the
video goes back to moonlight blue, still camera. Try `self.mood("moss")`
(green) or `self.mood("bone")` (grey). Next lesson.

---

## Lesson 5 — new look for free (5 minutes)

Goal: same title, new dust. Open `lesson5.py`. Two changes:

```python
class Lesson5(Video):
    seed = 21

    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6, wave=0.4)
        self.rest(1.0)
```

- `seed = 21` (was 7): new random dust. Same words, new art.
- `wave=0.4` (was 0.9): faster letter wave. `0` = all at once.

```sh
./oanim render course/lesson5.py --mode preview
```

![Lesson 5](learn_frames/l5_seed.png)

Put it next to the Lesson 1 picture. Same word, different dust. Next lesson.

---

## Lesson 6 — a flower, no words (5 minutes)

Goal: dust can grow shapes. Open `lesson6.py`:

```python
        self.grow(Bloom(scale=0.46, jitter=0.8), 2.0, wave=0.9)
```

```sh
./oanim render course/lesson6.py --mode preview
```

![Lesson 6](learn_frames/l6_bloom.png)

Change `Bloom(...)` to `Branch(depth=7, seed=11)` (fix the import too). A
tree grows. Then `Lightning(pieces=900, seed=13)`. Lightning. Next lesson.

---

## Lesson 7 — dance to a beat (5 minutes)

Goal: motion follows sound. Open `lesson7.py`:

```python
        self.pulse(132)
        self.drift(1.0)
        self.show("PULSE", "132 BPM", 1.6, tracking=18)
        self.rest(0.5)
```

`pulse` sets a beat for the whole video. Louder beat = stronger flow +
brighter dots. For your real sound file, use this instead:

```python
        self.music("vo.wav")
```

```sh
./oanim render course/lesson7.py --mode preview
```

![Lesson 7](learn_frames/l7_pulse.png)

You know the whole tool now. Make your own: `02_TASKS.md` → "Start a new
video from zero".

---

## When something looks wrong

| You see | It means | Fix |
|---|---|---|
| `ModuleNotFoundError: engine` | File moved somewhere deep (scripts must live one folder below the project, like `my_videos/` or `course/`) | Put it back |
| Empty video message | Your `build()` has no moments yet | Add a line like `self.drift(1.0)` |
| Same dust every time | Same seed | Write `seed = 21` (or any number) in your class |
| Music changes nothing | No beat set | Add `self.music("vo.wav")` or `self.pulse(132)` |
| Can't hear audio in the mp4 | Normal — the tool makes silent film | Add music in your editor |
| Title too wide / cut off | Long word on narrow screen | Shorter word, or lower `tracking` |

Stuck after that? Open the closest `course/` lesson, read it, copy the
idea into your file. Never edit `engine/` or `scenes/` — those are the tool.
