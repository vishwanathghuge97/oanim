"""Lesson 3: timeline + burst outro."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles


class Lesson3(Scene):
    def construct(self):
        title = Text("DREAM", subtitle="EPISODE ONE",
                     weight="Light", tracking=18)
        dots = FlowParticles(n=1500, seed=7)
        self.particles = dots
        self.text_obj = title
        self.play(dots.drift(duration=1.0))
        self.play(dots.form(title, duration=2.0, sweep=0.9))
        self.play(self.hold(duration=0.6))
        self.play(dots.scatter(duration=1.4, power=340.0))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson3.preview.mp4"))
    Lesson3(out=out, mode="preview", thumbnail=False).construct_and_render()
