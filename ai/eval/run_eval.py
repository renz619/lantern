"""Score analyze_video against a ground-truth sheet.

Usage (from the repo root):
    python ai/eval/run_eval.py testdata/Test_Data_1.mov testdata/Test_Data_1.json
    python ai/eval/run_eval.py testdata/Test_Data_1.mov testdata/Test_Data_1.json --cache

--cache reuses the last Gemini answer for this video instead of calling Gemini again.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze import analyze_video, normalize_label  # noqa: E402

TIME_TOLERANCE = 3.0
CACHE_DIR = Path(__file__).parent / "results"


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


def main(video, sheet, use_cache):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{Path(video).stem}.json"
    if use_cache and cache_file.exists():
        found = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        found = analyze_video(video)
        cache_file.write_text(json.dumps(found, indent=2), encoding="utf-8")

    truth = json.loads(Path(sheet).read_text(encoding="utf-8"))["items"]
    matched, missed, false_alarms = match_items(found, truth)

    print(f"found {len(matched)}/{len(truth)}  missed {len(missed)}  false alarms {len(false_alarms)}")
    for want in missed:
        print("  MISSED     ", describe(want))
    for item in false_alarms:
        print("  FALSE ALARM", describe(item))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], args[1], "--cache" in sys.argv)
