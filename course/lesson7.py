"""Lesson 7: motion follows a beat."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Lesson7(Video):
    dots = 900
    seed = 21

    def build(self):
        self.pulse(132)
        self.drift(1.0)
        self.show("PULSE", "132 BPM", 1.6, tracking=18)
        self.rest(0.5)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson7.preview.mp4"))
    Lesson7(save=out, mode="preview").run()
