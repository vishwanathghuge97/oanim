"""Lesson 1: your first render."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles


class Lesson1(Scene):
    def construct(self):
        title = Text("GROWTH", subtitle="ORGANIC MOTION",
                     weight="Light", tracking=16)
        dots = FlowParticles(n=1500, seed=7)
        self.particles = dots
        self.text_obj = title
        self.play(dots.drift(duration=1.6))
        self.play(dots.form(title, duration=2.6, sweep=0.9))
        self.play(self.hold(duration=1.0))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson1.preview.mp4"))
    Lesson1(out=out, mode="preview", thumbnail=False).construct_and_render()
