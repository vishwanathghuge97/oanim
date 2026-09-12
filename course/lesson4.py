"""Lesson 4: mood (warm colors + trails + camera)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson4(Video):
    dots = 900
    seed = 3

    def build(self):
        self.mood("ember", trails=0.6, zoom=1.06, shake=1.2)
        self.drift(1.0)
        self.show("EMBER", "WARM DUST", 1.6, tracking=18)
        self.rest(0.5)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson4.preview.mp4"))
    Lesson4(save=out, mode="preview").run()
