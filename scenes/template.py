"""oanim starter — your video starts here. Change the words, then:
  ./oanim render scenes/template.py --mode preview
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class MyVideo(Video):
    def build(self):
        self.drift(1.6)
        self.show("GROWTH", "ORGANIC MOTION", 2.6)
        self.rest(1.0)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(prog="oanim template")
    ap.add_argument("--out", default="template.preview.mp4")
    ap.add_argument("--mode", default="preview",
                    choices=["preview", "draft", "final", "short"])
    a = ap.parse_args()
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), a.out))
    MyVideo(save=out, mode=a.mode).run()
