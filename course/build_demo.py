"""BUILD guide demo: words melt into a flower, then burst. Built from zero."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video, Bloom


class BuildDemo(Video):
    dots = 1500
    seed = 11

    def build(self):
        self.mood("ink", zoom=1.06, shake=1.2)
        self.drift(1.2)
        self.show("OCEAN", "MY FIRST BUILD", 2.2, wave=1.0, tracking=18)
        self.rest(0.8)
        self.grow(Bloom(scale=0.44, jitter=0.9), 2.2, wave=0.8)
        self.rest(0.6)
        self.burst(1.2)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "build_demo.preview.mp4"))
    BuildDemo(save=out, mode="preview").run()
