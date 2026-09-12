# LEARN — 7 small lessons (~40 minutes)

Do them in order. Files `lesson1.py` … `lesson7.py` are in this folder.
Every lesson works the same way: run the command, open the mp4 it makes,
compare with the picture here. Then change one thing and run again.

---

## Lesson 0 — three lines (2 minutes, no running)

Open `lesson1.py`. The whole video is this:

```python
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6)
        self.rest(1.0)
```

The middle line is your words — title, small line, seconds. The other two
are the time plan: wander, then words, then rest. Words + moments, done.

---

## Lesson 1 — run it

```sh
./oanim render course/lesson1.py --mode preview
```

Open `course/lesson1.preview.mp4`:

![Lesson 1](learn_frames/l1_first.png)

Grainy dust letters, a small subtitle line, a few dots still floating.
Alive, not frozen — that feeling is the whole tool.

Same command with `--mode draft` gives the sharper version. From now on:
preview while you work, draft to judge, final once.

→ Lesson 2 puts your own words in.

---

## Lesson 2 — your words

Only one line differs from Lesson 1:

```python
        self.show("DREAM", "EPISODE ONE", 2.6, tracking=18)
```

```sh
./oanim render course/lesson2.py --mode preview
```

![Lesson 2](learn_frames/l2_words.png)

Now put one of your words where `"DREAM"` is, and run again. Watching your
own word gather from dust never gets old. The full file, for copying:

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

→ Lesson 3 blows the words up at the end.

---

## Lesson 3 — words burst at the end

`lesson3.py` ends with a new moment:

```python
        self.burst(1.4)
```

```sh
./oanim render course/lesson3.py --mode preview
```

![Lesson 3](learn_frames/l3_outro.png)

That frame is mid-explosion — letters flying outward, dissolving. Try
`strength=600.0` inside the brackets for violence, `strength=150.0` for a
sigh. One number, two opposite feelings.

→ Lesson 4 changes the mood entirely.

---

## Lesson 4 — warm mood

First line of `lesson4.py` does all the work:

```python
        self.mood("ember", trails=0.6, zoom=1.06, shake=1.2)
```

Warm colors, light trails behind fast dots, a slow push-in:

```sh
./oanim render course/lesson4.py --mode preview
```

![Lesson 4](learn_frames/l4_mood.png)

Delete that one line and you're back to moonlight blue with a still shot.
Same words, same dust — only the feeling changed. `"moss"` goes green,
`"bone"` goes grey.

→ Lesson 5 gets a new look without touching words or mood.

---

## Lesson 5 — new look for free

Two small edits in `lesson5.py`:

```python
class Lesson5(Video):
    seed = 21
```

```python
        self.show("GROWTH", "ORGANIC MOTION", 2.6, wave=0.4)
```

New seed, new dust — same words, new artwork. Faster wave (`0.4` instead
of `0.9`; `0` means all letters at once):

```sh
./oanim render course/lesson5.py --mode preview
```

![Lesson 5](learn_frames/l5_seed.png)

Hold it next to the Lesson 1 picture. Out of ideas on any video? Change
the seed. Free variations, forever.

→ Lesson 6 drops words completely.

---

## Lesson 6 — a flower, no words

Dust doesn't need words. From `lesson6.py`:

```python
        self.grow(Bloom(scale=0.46, jitter=0.8), 2.0, wave=0.9)
```

```sh
./oanim render course/lesson6.py --mode preview
```

![Lesson 6](learn_frames/l6_bloom.png)

Swap in `Branch(depth=7, seed=11)` (and fix the import) and a tree grows.
`Lightning(pieces=900, seed=13)` gives you lightning. One line per wonder.

→ Last one: Lesson 7 adds sound.

---

## Lesson 7 — dance to a beat

`lesson7.py` sets a beat for the whole video, then plays as usual:

```python
        self.pulse(132)
        self.drift(1.0)
        self.show("PULSE", "132 BPM", 1.6, tracking=18)
        self.rest(0.5)
```

Louder beat, stronger flow, brighter dots. Got a real sound file? This one
line replaces the pulse:

```python
        self.music("vo.wav")
```

```sh
./oanim render course/lesson7.py --mode preview
```

![Lesson 7](learn_frames/l7_pulse.png)

That's the whole tool in your hands. `02_TASKS.md` → "Start a new video
from zero" makes it yours.

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
