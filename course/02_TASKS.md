# TASKS — do one job, step by step

Pick your job. Follow the steps. Each step is one action.

---

## Start a new video from zero

1. Draw 3–5 boxes on paper. Each box: what shows + seconds. (Example:
   dust 1s → word 2s → rest 1s → burst 1s.)
2. `./oanim new myvideo` — open `my_videos/myvideo.py`.
3. Write your `show(...)` line (words + subtitle + seconds).
4. Add ONE moment line. Preview. Add the next. Preview.
5. Set mood last: `self.mood("ember", trails=0.6)`.
6. `--mode draft` to judge. `--mode final` to upload.

## Make an intro

1. `./oanim new intro`, write your channel words in `show(...)`.
2. Keep `drift → show → rest` (3–6 seconds total).
3. Warm look: `self.mood("ember", trails=0.6, zoom=1.07, shake=1.4)`.
4. Preview, draft, final. Done.

## Make a chapter card

1. Thin wide title: `show("CHAPTER 2", "THE TURNING POINT", 1.6, wave=1.2, weight="Thin", tracking=20)`.
2. Rest: `rest(1.2)`.
3. Punch out: `burst(1.0, strength=500.0)`.
4. Full file that runs: `task_chapter.py`. Render it, copy it, change words.

![chapter card](learn_frames/task_chapter.png)

## Make an outro burst

1. After your last `rest`, add `burst(1.4)`.
2. `strength=150` = soft sigh, `600` = explosion. Pick one, preview.
3. Full example: `lesson3.py`.

## Add music or voice

1. Put your sound file next to your script (`vo.wav`).
2. Add one line at the top of `build()`: `self.music("vo.wav")`.
3. Preview. Motion and light now follow your sound.
4. Note: sound is NOT saved in the mp4. Add music in your editor.
5. No file yet? Practice with `self.pulse(132)` (`lesson7.py`).

## Make a vertical Short

1. Take any working video file. Change nothing in it.
2. `./oanim render my_videos/myvideo.py --mode short`.
3. Title auto-shrinks to fit. Check the thumbnail.

## Upload in 1080p

1. `./oanim render my_videos/myvideo.py --mode final`.
2. Dots picked for sharp letters by themselves. Wait ~30s per 5s of video.
3. Upload the `.final.mp4`.

## Melt words into a flower

1. After a title `rest`, add `grow(Bloom(scale=0.44, jitter=0.9), 2.2, wave=0.8)`.
2. Add `Bloom` to the import line. Rest, then `burst` to end.
3. Full file that runs: `build_demo.py`.

![flower](learn_frames/build_bloom.png)

## Make a looping bed (video that never ends)

1. One long moment: `drift(60)`. No words.
2. Run with loop mode (not normal render):
```python
s = MyVideo(save="bed.mp4", mode="draft"); s.build(); s.render_loop(blend=0.6)
```
3. End flows back into start. Lay voice over it in your editor.

## FIX-IT — something wrong? Find it here

| You see | Why | Do this |
|---|---|---|
| `ModuleNotFoundError: engine` | File moved somewhere deep (scripts must live one folder below the project, like `my_videos/` or `course/`) | Put it back |
| Empty video message | `build()` has no moments yet | Add a line like `self.drift(1.0)` |
| Same dust every time | Same seed | Write `seed = 21` in your class |
| Music changes nothing | No beat set | Add `self.music("vo.wav")` |
| No sound in mp4 | Normal — tool makes silent film | Add sound in your editor |
| Letters cut at the edge | Long word, small screen | Shorter word, or lower `tracking` |

## Three rules for fast learning

1. One change per preview. Two changes hide which one worked.
2. Copy before big cuts: `cp my_videos/a.py my_videos/a_try2.py`.
3. Keep the `.py`, delete test mp4s. The small file IS the video.
