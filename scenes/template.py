"""oanim starter — copy this file for every new video."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles, Camera

class MyVideo(Scene):
    def construct(self):
        title = Text("GROWTH", subtitle="ORGANIC MOTION",
                     weight="Light", tracking=16)
        dots = FlowParticles(n=1500, seed=7)
        self.particles = dots
        self.text_obj = title
        self.attach_camera(Camera().push_in(1.0, 1.07).handheld(1.5))
        self.play(dots.drift(duration=1.6))
        self.play(dots.form(title, duration=2.6, sweep=0.9))
        self.play(self.hold(duration=1.0))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="oanim template")
    ap.add_argument("--out", default="my_video.mp4")
    ap.add_argument("--mode", default="draft",
                    choices=["preview", "draft", "final", "short"])
    ap.add_argument("--encoder", default="cpu", choices=["cpu", "vaapi"])
    a = ap.parse_args()
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", a.out))
    MyVideo(out=out, mode=a.mode, encoder=a.encoder).construct_and_render()
