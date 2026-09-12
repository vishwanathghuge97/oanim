"""oanim showcase: every feature in short preview clips.
Run: ./.venv/bin/python scenes/showcase.py [--only ember,scatter,bloom,branch,dla,flock,drive,loop]
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles, Camera, Bloom, Branch, DLA
from engine.audio import SineDrive

OUT = lambda name: os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tmp", f"show_{name}.mp4"))


class EmberIntro(Scene):
    def construct(self):
        t = Text("EMBER", subtitle="WARM DUST", weight="Light", tracking=18)
        d = FlowParticles(n=900, seed=3)
        self.particles, self.text_obj = d, t
        self.attach_camera(Camera().push_in(1.0, 1.06).handheld(1.2))
        self.play(d.drift(1.0))
        self.play(d.form(t, 1.6, sweep=0.9))
        self.play(self.hold(0.5))


class ScatterOut(Scene):
    def construct(self):
        t = Text("BURST", subtitle="OUTRO", weight="Light", tracking=18)
        d = FlowParticles(n=900, seed=5)
        self.particles, self.text_obj = d, t
        self.play(d.drift(0.6))
        self.play(d.form(t, 1.2, sweep=0.8))
        self.play(d.scatter(1.2, power=340.0))


class BloomClip(Scene):
    def construct(self):
        b = Bloom(scale=0.46, jitter=0.8)
        d = FlowParticles(n=1100, seed=9)
        self.particles, self.text_obj = d, b
        self.play(d.drift(0.6))
        self.play(d.form(b, 2.0, sweep=0.9))
        self.play(self.hold(0.5))


class BranchClip(Scene):
    def construct(self):
        b = Branch(depth=7, seed=11)
        d = FlowParticles(n=1100, seed=11)
        self.particles, self.text_obj = d, b
        self.play(d.drift(0.5))
        self.play(d.form(b, 2.0, sweep=1.2))
        self.play(self.hold(0.5))


class DlaClip(Scene):
    def construct(self):
        d_ = DLA(sticks=900, seed=13)
        d = FlowParticles(n=1100, seed=13)
        self.particles, self.text_obj = d, d_
        self.play(d.drift(0.5))
        self.play(d.form(d_, 2.0, sweep=1.2))
        self.play(self.hold(0.5))


class FlockClip(Scene):
    def construct(self):
        t = Text("FLOCK", subtitle="TOGETHER", weight="Light", tracking=18)
        d = FlowParticles(n=800, seed=17)
        self.particles, self.text_obj = d, t
        self.play(d.drift(0.6))
        self.play(d.flock(t, 2.2))
        self.play(self.hold(0.5))


class DriveClip(Scene):
    def construct(self):
        drv = SineDrive(bpm=132)
        t = Text("PULSE", subtitle="132 BPM", weight="Light", tracking=18)
        d = FlowParticles(n=900, seed=21)
        self.particles, self.text_obj = d, t
        self.play(d.drift(1.0, drive=drv))
        self.play(d.form(t, 1.6, sweep=0.9, drive=drv))
        self.play(self.hold(0.5))


class LoopClip(Scene):
    def construct(self):
        d = FlowParticles(n=900, seed=29)
        self.particles = d
        self.play(d.drift(3.0))


ALL = {"ember": (EmberIntro, {"theme": "ember", "motion_blur": 0.6}),
       "scatter": (ScatterOut, {}),
       "bloom": (BloomClip, {}),
       "branch": (BranchClip, {}),
       "dla": (DlaClip, {}),
       "flock": (FlockClip, {}),
       "drive": (DriveClip, {}),
       "loop": (LoopClip, {})}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(ALL))
    a = ap.parse_args()
    for name in a.only.split(","):
        cls, kw = ALL[name.strip()]
        print(f"===== {name} =====", flush=True)
        s = cls(out=OUT(name), mode="preview", **kw)
        if name == "loop":
            s.construct()
            s.render_loop(blend=0.5)
        else:
            s.construct_and_render()
