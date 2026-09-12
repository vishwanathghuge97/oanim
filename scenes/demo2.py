"""Demo2 - what users actually write (easy API, natural morph)."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video

# User code: 3 lines of intent, no numpy, no writer, no loops.
class Demo2(Video):
    def build(self):
        self.drift(duration=1.6)
        self.show("GROWTH", "ORGANIC MOTION", duration=2.6)
        self.rest(duration=1.0)

if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo2.mp4"))
    Demo2(save=out, mode="draft").run()
