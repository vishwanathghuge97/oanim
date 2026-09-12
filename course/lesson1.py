"""Lesson 1: your first render."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson1(Video):
    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6)
        self.rest(1.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson1.preview.mp4"))
    Lesson1(save=out, mode="preview").run()
