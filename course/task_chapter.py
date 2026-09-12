"""Chapter card: thin wide title, slow wave in, punch-out."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Scene, Text, FlowParticles


class Chapter(Scene):
    def construct(self):
        title = Text("CHAPTER 2", subtitle="THE TURNING POINT",
                     weight="Thin", tracking=20)
        dots = FlowParticles(n=1500, seed=31)
        self.particles = dots
        self.text_obj = title
        self.play(dots.drift(duration=0.6))
        self.play(dots.form(title, duration=1.6, sweep=1.2))
        self.play(self.hold(duration=1.2))
        self.play(dots.scatter(duration=1.0, power=500.0))


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "task_chapter.preview.mp4"))
    Chapter(out=out, mode="preview", thumbnail=False).construct_and_render()
