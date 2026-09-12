"""Lesson 6: no words, just growth."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, FlowParticles, Bloom


class Lesson6(Scene):
    def construct(self):
        bloom = Bloom(scale=0.46, jitter=0.8)
        dots = FlowParticles(n=1100, seed=9)
        self.particles = dots
        self.text_obj = bloom
        self.play(dots.drift(duration=0.6))
        self.play(dots.form(bloom, duration=2.0, sweep=0.9))
        self.play(self.hold(duration=0.5))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson6.preview.mp4"))
    Lesson6(out=out, mode="preview", thumbnail=False).construct_and_render()
