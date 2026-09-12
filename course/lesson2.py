"""Lesson 2: your own words."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson2(Video):
    def build(self):
        self.drift(1.6)
        self.show("DREAM", "EPISODE ONE", 2.6, tracking=18)
        self.rest(1.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson2.preview.mp4"))
    Lesson2(save=out, mode="preview").run()
