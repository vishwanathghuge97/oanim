"""oanim HERO reel: full capacity in one video.
Run: ./.venv/bin/python scenes/hero.py
Renders 5 draft acts to tmp/, concatenates to hero.mp4 (project root).
"""
import os
import sys
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles, Camera, Bloom, Branch, DLA
from engine.audio import SineDrive

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP = os.path.join(ROOT, "tmp")
N = 1600


def base(out, **kw):
    kw.setdefault("mode", "draft")
    return kw


class ActEmber(Scene):  # hook: warm streaks + push-in title
    def construct(self):
        t = Text("EMBER", subtitle="FLOW INTO FORM", weight="Light", tracking=20)
        d = FlowParticles(n=N, seed=101)
        self.particles, self.text_obj = d, t
        self.attach_camera(Camera().push_in(1.0, 1.07).handheld(1.4))
        self.play(d.drift(1.6))
        self.play(d.form(t, 2.6, sweep=0.9))
        self.play(self.hold(0.8))


class ActGrowth(Scene):  # bloom -> tree, no words
    def construct(self):
        d = FlowParticles(n=N, seed=102)
        self.particles = d
        self.play(d.drift(0.8))
        self.play(d.form(Bloom(scale=0.44, jitter=0.9), 2.6, sweep=0.8))
        self.play(d.form(Branch(depth=7, seed=102), 2.8, sweep=1.2))
        self.play(self.hold(0.8))


class ActLightning(Scene):  # DLA strike
    def construct(self):
        c = DLA(sticks=1400, seed=103)
        d = FlowParticles(n=N, seed=103)
        self.particles, self.text_obj = d, c
        self.play(d.drift(0.5))
        self.play(d.form(c, 2.4, sweep=1.2))
        self.play(self.hold(0.8))


class ActFlock(Scene):  # boids title + burst outro
    def construct(self):
        t = Text("FLOCK", subtitle="MOVE TOGETHER", weight="Light", tracking=20)
        d = FlowParticles(n=N, seed=104)
        self.particles, self.text_obj = d, t
        self.attach_camera(Camera().push_in(1.0, 1.05).handheld(1.0))
        self.play(d.drift(0.8))
        self.play(d.flock(t, 2.6))
        self.play(d.scatter(1.4, power=340.0))


class ActPulse(Scene):  # beat-synced wordmark finale
    def construct(self):
        drv = SineDrive(bpm=132)
        t = Text("OANIM", subtitle="LIVING TITLES", weight="Light", tracking=22)
        d = FlowParticles(n=N, seed=105)
        self.particles, self.text_obj = d, t
        self.attach_camera(Camera().push_in(1.02, 1.09))
        self.play(d.drift(1.2, drive=drv))
        self.play(d.form(t, 2.4, sweep=0.9, drive=drv))
        self.play(self.hold(1.2))


ACTS = [
    ("hero_1_ember", ActEmber, {"theme": "ember", "motion_blur": 0.6}),
    ("hero_2_growth", ActGrowth, {}),
    ("hero_3_lightning", ActLightning, {"theme": "bone"}),
    ("hero_4_flock", ActFlock, {}),
    ("hero_5_pulse", ActPulse, {"theme": "moss"}),
]

if __name__ == "__main__":
    parts = []
    for name, cls, kw in ACTS:
        out = os.path.join(TMP, name + ".mp4")
        print(f"===== {name} =====", flush=True)
        s = cls(out=out, **base(out, **kw))
        s.construct_and_render()
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
