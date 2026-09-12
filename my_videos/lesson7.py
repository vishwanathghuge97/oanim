"""Lesson 7: motion follows a beat."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles
from engine.audio import SineDrive


class Lesson7(Scene):
    def construct(self):
        beat = SineDrive(bpm=132)
        title = Text("PULSE", subtitle="132 BPM",
                     weight="Light", tracking=18)
        dots = FlowParticles(n=900, seed=21)
        self.particles = dots
        self.text_obj = title
        self.play(dots.drift(duration=1.0, drive=beat))
        self.play(dots.form(title, duration=1.6, sweep=0.9, drive=beat))
        self.play(self.hold(duration=0.5))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson7.preview.mp4"))
    Lesson7(out=out, mode="preview", thumbnail=False).construct_and_render()
