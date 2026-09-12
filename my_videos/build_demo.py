"""BUILD guide demo: words melt into a flower, then burst. Built from zero."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles, Bloom, Camera


class BuildDemo(Scene):
    def construct(self):
        title = Text("OCEAN", subtitle="MY FIRST BUILD",
                     weight="Light", tracking=18)
        dots = FlowParticles(n=1500, seed=11)
        self.particles = dots
        self.text_obj = title
        self.attach_camera(Camera().push_in(1.0, 1.06).handheld(1.2))
        self.play(dots.drift(duration=1.2))
        self.play(dots.form(title, duration=2.2, sweep=1.0))
        self.play(self.hold(duration=0.8))
        self.play(dots.form(Bloom(scale=0.44, jitter=0.9),
                            duration=2.2, sweep=0.8))
        self.play(self.hold(duration=0.6))
        self.play(dots.scatter(duration=1.2, power=300.0))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "build_demo.preview.mp4"))
    BuildDemo(out=out, mode="preview", thumbnail=False).construct_and_render()
