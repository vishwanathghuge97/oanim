# FUNCTIONS — what each line does (one page)

## Make a video

```sh
./oanim new myvideo                             # new file: my_videos/myvideo.py
./oanim render my_videos/myvideo.py --mode preview   # fast check (seconds)
./oanim render my_videos/myvideo.py --mode draft     # judge the true look
./oanim render my_videos/myvideo.py --mode final     # 1080p upload
```

Video + thumbnail land next to your script. Rule: preview while you work,
draft to judge, final once.

Smallest working video (this exact file renders):

```python
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Mine(Video):
    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "SUB", 2.6)
        self.rest(1.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "mine.preview.mp4"))
    Mine(save=out, mode="preview").run()
```

## Moments (lines inside `build`)

| Line | Job |
|---|---|
| `self.drift(1.6)` | Dust wanders. No words. `duration` = seconds. |
| `self.show("BIG", "small", 2.6)` | Dust gathers into your words. `subtitle=""`, `duration=2.6`, `wave=0.9` (`0` together … `1.2` slow wave), `tracking=16` (letter space), `weight="Light"`. |
| `self.grow(Bloom(), 2.4)` | Dust grows a shape. `duration=2.4`, `wave=1.0`. |
| `self.follow("A", "B", 3.0)` | Dust moves after each other, then settles. Words or a shape. `duration=3.0`, `wave=1.0`. |
| `self.rest(1.0)` | Words rest on screen. `duration` = seconds. |
| `self.burst(1.2)` | Words burst into dust. `duration=1.2`, `strength=340.0` (`150` sigh … `600` boom). |
| `self.mood("ember", trails=0.6, zoom=1.06, shake=1.2)` | Feeling. `"ink"` moonlight (default), `"ember"` fire, `"bone"` grey, `"moss"` green. `trails=0.0` off … `~1` strong. |
| `self.music("vo.wav")` | Your sound file drives all moments. |
| `self.pulse(132)` | Fake beat for practice (`bpm=132`). |

## Settings (lines in your class, all optional)

```python
class Mine(Video):
    seed = 21    # same number = same film. Any number. Default 7.
    dots = 900   # how many dots. Skip it: tool picks by size (1500 / 2600 / 4500).
```

## Shapes (inside `grow` or `follow`)

`Bloom(scale=0.40, jitter=2.0)` — flower. `Branch(depth=9)` — tree.
`Lightning(pieces=2200)` — lightning. (`seed=7` on each for a new look.)

## Sizes

`preview` small+fast · `draft` true look · `final` 1080p upload · `short` vertical.

## If wrong

Empty video message → `build()` has no moments yet. Black screen can't
happen anymore. No sound in mp4 is normal — add music in your editor.
