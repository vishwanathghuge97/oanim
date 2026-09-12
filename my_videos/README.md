# my_videos — your place. Tool stays out.

**Start:** `START.md` (first video in 5 minutes).
**Learn:** `LEARN.md` (7 small lessons).
**Work:** `TASKS.md` (one job at a time).
**Look up:** `REFERENCE.md` (all functions, one page).
**Why:** `IDEAS.md` (short).

```sh
./oanim new NAME                              # new video file
./oanim render my_videos/NAME.py --mode preview   # fast check
./oanim render my_videos/NAME.py --mode draft     # judge the look
./oanim render my_videos/NAME.py --mode final     # 1080p upload (n=4500)
```

Your `.py` files are safe here. Your `.mp4` files sit beside them and are
never committed to git.
