# my_videos — your place. Tool stays out.

**New? Read in this order:**
1. `LEARN.md` — course: 7 small lessons, run each one (~40 min).
2. `BUILD.md` — make your own video from zero, step by step.
3. `CHEATSHEET.md` — every function on one page. Pin it.

**Daily use (that's all):**
```sh
./oanim new NAME                              # new video file
./oanim render my_videos/NAME.py --mode preview   # fast check
./oanim render my_videos/NAME.py --mode draft     # judge the look
./oanim render my_videos/NAME.py --mode final     # 1080p upload (set n=4500)
```

Your `.py` files are safe here — engine work never touches them.
Your `.mp4` files sit next to your scripts and are never committed to git.
