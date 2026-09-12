"""Demo2 - what users actually write (easy API, natural morph)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles

# User code: 6 lines of intent, no numpy, no writer, no loops.
class Demo2(Scene):
    def construct(self):
        # weight: Thin/ExtraLight/Light/Regular - Light matches dust best
        title = Text("GROWTH", subtitle="ORGANIC MOTION",
                     weight="Light", tracking=16)
        dots = FlowParticles(n=1500, seed=7)
        self.particles = dots      # engine needs refs for drawing
        self.text_obj = title
        self.play(dots.drift(duration=1.6))
        self.play(dots.form(title, duration=2.6, sweep=0.9))
        self.play(self.hold(duration=1.0))

if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo2.mp4"))
    Demo2(out=out, mode="draft").construct_and_render()
