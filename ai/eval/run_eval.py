"""Score analyze_video against ground-truth sheets.

Usage (from the repo root):
    python ai/eval/run_eval.py testdata/Test_Data_1.mov testdata/Test_Data_1.json
    python ai/eval/run_eval.py testdata            # every sheet in the folder
    python ai/eval/run_eval.py testdata --cache    # reuse saved Gemini answers

--only=a,b restricts a folder run to the sheets named a.json and b.json.
--cache reuses the last Gemini answer for each video instead of calling Gemini again
(videos with no saved answer are skipped). Free-tier Gemini allows about 20 requests
a day, so use --cache while tuning how answers are scored.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze import analyze_video, normalize_label  # noqa: E402

TIME_TOLERANCE = 3.0
PAUSE_BETWEEN_VIDEOS = 20  # seconds
# With PROMPT_VERSION set, answers are saved per version (results/analyze_v5/...)
# so runs of different prompts can be compared without overwriting each other.
CACHE_DIR = Path(__file__).parent / "results" / os.getenv("PROMPT_VERSION", "")


def match_items(found, truth, tolerance=TIME_TOLERANCE):
    """Pair each true item with at most one found item of the same label within tolerance seconds."""
    unused = list(range(len(found)))
    matched, missed = [], []
    for want in truth:
        label = normalize_label(want["label"])
        candidates = [
            i for i in unused
            if found[i]["label"] == label
            and abs(found[i]["video_seconds"] - want["video_seconds"]) <= tolerance
        ]
        if not candidates:
            missed.append(want)
            continue
        best = min(candidates, key=lambda i: abs(found[i]["video_seconds"] - want["video_seconds"]))
        unused.remove(best)
        matched.append((want, found[best]))
    false_alarms = [found[i] for i in unused]
    return matched, missed, false_alarms


def describe(item):
    return f"{item['label']} @ {item['video_seconds']}s ({item.get('position', '')})"


def get_found(video, use_cache):
    """Return Gemini's items for a video, or None if --cache was asked for and nothing is saved."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{Path(video).stem}.json"
    if use_cache:
        if not cache_file.exists():
            return None
        found = json.loads(cache_file.read_text(encoding="utf-8"))
        # Saved answers may predate a vocabulary change; apply today's label standard.
        return [{**item, "label": normalize_label(item["label"])} for item in found]
    found = analyze_video(video)
    cache_file.write_text(json.dumps(found, indent=2), encoding="utf-8")
    return found


def score_video(video, sheet, use_cache):
    """Return (matched, missed, false_alarms) for one video, or None if it was skipped."""
    found = get_found(video, use_cache)
    if found is None:
        return None
    truth = json.loads(Path(sheet).read_text(encoding="utf-8"))["items"]
    return match_items(found, truth)


def report(name, result):
    matched, missed, false_alarms = result
    total = len(matched) + len(missed)
    print(f"{name}: found {len(matched)}/{total}  missed {len(missed)}  false alarms {len(false_alarms)}")
    for want in missed:
        print("  MISSED     ", describe(want))
    for item in false_alarms:
        print("  FALSE ALARM", describe(item))


def find_pairs(folder, only=None):
    """Yield (video, sheet) for every sheet in folder whose video file exists.

    only: optional set of sheet names (without .json) to restrict the run to.
    """
    for sheet in sorted(Path(folder).glob("*.json")):
        if only and sheet.stem not in only:
            continue
        try:
            data = json.loads(sheet.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            print(f"skipping {sheet.name}: not valid JSON (line {error.lineno}: {error.msg})")
            continue
        video = Path(folder) / data["video"]
        if video.exists():
            yield video, sheet
        else:
            print(f"skipping {sheet.name}: video {data['video']} not found")


def run_all(folder, use_cache, only=None):
    found = missed = false_alarms = skipped = 0
    for video, sheet in find_pairs(folder, only):
        if not use_cache and found + missed:
            time.sleep(PAUSE_BETWEEN_VIDEOS)  # stay under Gemini's tokens-per-minute limit
        try:
            result = score_video(video, sheet, use_cache)
        except Exception as error:  # one bad video shouldn't stop the batch
            print(f"{video.stem}: failed ({type(error).__name__}: {str(error)[:80]})")
            skipped += 1
            continue
        if result is None:
            print(f"{video.stem}: no saved answer (run without --cache)")
            skipped += 1
            continue
        report(video.stem, result)
        found += len(result[0])
        missed += len(result[1])
        false_alarms += len(result[2])
    total = found + missed
    rate = f"{found / total:.0%}" if total else "n/a"
    print(f"\nTOTAL: found {found}/{total} ({rate})  missed {missed}  false alarms {false_alarms}  skipped {skipped}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cache = "--cache" in sys.argv
    only = {n for a in sys.argv[1:] if a.startswith("--only=") for n in a[7:].split(",") if n}
    if len(args) == 1 and Path(args[0]).is_dir():
        run_all(args[0], cache, only or None)
    else:
        result = score_video(args[0], args[1], cache)
        report(Path(args[0]).stem, result) if result else print("no saved answer (run without --cache)")
