"""Lesson 5: free variations (seed + wave)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson5(Video):
    seed = 21

    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6, wave=0.4)
        self.rest(1.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson5.preview.mp4"))
    Lesson5(save=out, mode="preview").run()
