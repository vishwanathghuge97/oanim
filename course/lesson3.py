"""Lesson 3: timeline + burst outro."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson3(Video):
    def build(self):
        self.drift(1.0)
        self.show("DREAM", "EPISODE ONE", 2.0, tracking=18)
        self.rest(0.6)
        self.burst(1.4)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson3.preview.mp4"))
    Lesson3(save=out, mode="preview").run()
