"""Lesson 4: mood (theme + trails + camera)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles, Camera


class Lesson4(Scene):
    def construct(self):
        title = Text("EMBER", subtitle="WARM DUST",
                     weight="Light", tracking=18)
        dots = FlowParticles(n=900, seed=3)
        self.particles = dots
        self.text_obj = title
        self.attach_camera(Camera().push_in(1.0, 1.06).handheld(1.2))
        self.play(dots.drift(duration=1.0))
        self.play(dots.form(title, duration=1.6, sweep=0.9))
        self.play(self.hold(duration=0.5))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson4.preview.mp4"))
    Lesson4(out=out, mode="preview", theme="ember",
            motion_blur=0.6, thumbnail=False).construct_and_render()
