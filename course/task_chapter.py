"""Chapter card: thin wide title, slow wave in, punch-out."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.api import Video


class Chapter(Video):
    seed = 31

    def build(self):
        self.drift(0.6)
        self.show("CHAPTER 2", "THE TURNING POINT", 1.6, wave=1.2,
                  weight="Thin", tracking=20)
        self.rest(1.2)
        self.burst(1.0, strength=500.0)


if __name__ == "__main__":
    out = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "task_chapter.preview.mp4"))
    Chapter(save=out, mode="preview").run()
