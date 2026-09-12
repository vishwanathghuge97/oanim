# my_videos — YOUR workspace (the tool lives outside this folder)

Everything in here is yours. The engine (`engine/`), examples (`scenes/`),
and build files are the tool — you never need to touch them.

New here? Read `LEARN.md` first (15 minutes, plain language).

## Make a video (3 steps)

```sh
./oanim new ep01                  # scaffold my_videos/ep01.py
# ... edit TITLE / SUBTITLE / theme in ep01.py ...
./oanim render my_videos/ep01.py --mode preview   # fast check (seconds)
./oanim render my_videos/ep01.py --mode draft     # full check
./oanim render my_videos/ep01.py --mode final     # 1080p upload
```

Each video is one `.py` file; its mp4 + png land next to it.
`*.mp4` files are never committed to git (thumbnails `.png` are).

## Rules of thumb

* One idea per file: `hook.py`, `chapter2.py`, `outro.py`, …
* Preview while writing, draft to judge, final once for upload.
* Final 1080p: use `FlowParticles(n=4500)` (4x pixels need ~3x particles).
* Vertical Short: add `--mode short` (title auto-shrinks to fit).
* Voiceover beat-sync: `drv = AudioDrive("vo.wav")`, pass `drive=drv`
  to `drift`/`form` (see `scenes/showcase.py` DriveClip + README recipes).
* Recipes for every look (ember hook, growth, flock, loop, …): root `README.md`.
* Stuck? Copy the closest file in `scenes/` — they are examples, not the tool.
