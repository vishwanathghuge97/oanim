"""oanim showcase: every feature in short preview clips.
Run: ./.venv/bin/python scenes/showcase.py [--only ember,scatter,bloom,branch,lightning,flock,drive,loop]
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video, Bloom, Branch, Lightning

OUT = lambda name: os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tmp", f"show_{name}.mp4"))


class EmberIntro(Video):
    dots = 900
    seed = 3

    def build(self):
        self.mood("ember", trails=0.6, zoom=1.06, shake=1.2)
        self.drift(1.0)
        self.show("EMBER", "WARM DUST", 1.6, tracking=18)
        self.rest(0.5)


class ScatterOut(Video):
    dots = 900
    seed = 5

    def build(self):
        self.drift(0.6)
        self.show("BURST", "OUTRO", 1.2, wave=0.8, tracking=18)
        self.burst(1.2)


class BloomClip(Video):
    dots = 1100
    seed = 9

    def build(self):
        self.drift(0.6)
        self.grow(Bloom(scale=0.46, jitter=0.8), 2.0, wave=0.9)
        self.rest(0.5)


class BranchClip(Video):
    dots = 1100
    seed = 11

    def build(self):
        self.drift(0.5)
        self.grow(Branch(depth=7, seed=11), 2.0, wave=1.2)
        self.rest(0.5)


class LightningClip(Video):
    dots = 1100
    seed = 13

    def build(self):
        self.drift(0.5)
        self.grow(Lightning(pieces=900, seed=13), 2.0, wave=1.2)
        self.rest(0.5)


class FlockClip(Video):
    dots = 800
    seed = 17

    def build(self):
        self.drift(0.6)
        self.follow("FLOCK", "TOGETHER", duration=2.2, tracking=18)
        self.rest(0.5)


class DriveClip(Video):
    dots = 900
    seed = 21

    def build(self):
        self.pulse(132)
        self.drift(1.0)
        self.show("PULSE", "132 BPM", 1.6, tracking=18)
        self.rest(0.5)


class LoopClip(Video):
    dots = 900
    seed = 29

    def build(self):
        self.drift(3.0)


ALL = {"ember": EmberIntro,
       "scatter": ScatterOut,
       "bloom": BloomClip,
       "branch": BranchClip,
       "lightning": LightningClip,
       "flock": FlockClip,
       "drive": DriveClip,
       "loop": LoopClip}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(ALL))
    a = ap.parse_args()
    for name in a.only.split(","):
        cls = ALL[name.strip()]
        print(f"===== {name} =====", flush=True)
        s = cls(save=OUT(name), mode="preview")
        if name == "loop":
            s.build()
            s.render_loop(blend=0.5)
        else:
            s.run()
