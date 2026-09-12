"""Lesson 6: no words, just growth."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video, Bloom


class Lesson6(Video):
    dots = 1100
    seed = 9

    def build(self):
        self.drift(0.6)
        self.grow(Bloom(scale=0.46, jitter=0.8), 2.0, wave=0.9)
        self.rest(0.5)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "lesson6.preview.mp4"))
    Lesson6(save=out, mode="preview").run()
