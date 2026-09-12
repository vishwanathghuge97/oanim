"""oanim HERO reel: full capacity in one video.
Run: ./.venv/bin/python scenes/hero.py
Renders 5 draft acts to tmp/, concatenates to hero.mp4 (project root).
"""
import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video, Bloom, Branch, Lightning

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP = os.path.join(ROOT, "tmp")


class ActEmber(Video):  # hook: warm streaks + push-in title
    dots = 1600
    seed = 101

    def build(self):
        self.mood("ember", trails=0.6, zoom=1.07, shake=1.4)
        self.drift(1.6)
        self.show("EMBER", "FLOW INTO FORM", 2.6, tracking=20)
        self.rest(0.8)


class ActGrowth(Video):  # bloom -> tree, no words
    dots = 1600
    seed = 102

    def build(self):
        self.drift(0.8)
        self.grow(Bloom(scale=0.44, jitter=0.9), 2.6, wave=0.8)
        self.grow(Branch(depth=7, seed=102), 2.8, wave=1.2)
        self.rest(0.8)


class ActLightning(Video):  # lightning strike
    dots = 1600
    seed = 103

    def build(self):
        self.mood("bone")
        self.drift(0.5)
        self.grow(Lightning(pieces=1400, seed=103), 2.4, wave=1.2)
        self.rest(0.8)


class ActFlock(Video):  # boids title + burst outro
    dots = 1600
    seed = 104

    def build(self):
        self.mood("ink", zoom=1.05, shake=1.0)
        self.drift(0.8)
        self.follow("FLOCK", "MOVE TOGETHER", duration=2.6, tracking=20)
        self.burst(1.4)


class ActPulse(Video):  # beat-synced wordmark finale
    dots = 1600
    seed = 105

    def build(self):
        self.pulse(132)
        self.mood("moss", zoom=1.09, shake=0.0)
        self.drift(1.2)
        self.show("OANIM", "LIVING TITLES", 2.4, tracking=22)
        self.rest(1.2)


ACTS = [
    ("hero_1_ember", ActEmber),
    ("hero_2_growth", ActGrowth),
    ("hero_3_lightning", ActLightning),
    ("hero_4_flock", ActFlock),
    ("hero_5_pulse", ActPulse),
]

if __name__ == "__main__":
    parts = []
    for name, cls in ACTS:
        out = os.path.join(TMP, name + ".mp4")
        print(f"===== {name} =====", flush=True)
        s = cls(save=out, mode="draft")
        s.run()
        parts.append(out)
    lst = os.path.join(TMP, "hero_list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    hero = os.path.join(ROOT, "hero.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", "-movflags", "+faststart", hero],
                   check=True)
    print("HERO", hero)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size", "-of",
                        "default=noprint_wrappers=1", hero],
                       capture_output=True, text=True)
    print(r.stdout.strip())
