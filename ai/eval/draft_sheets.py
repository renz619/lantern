"""Write a draft ground-truth sheet for every video in testdata/ that has none.

The drafts are Gemini's guesses. Check each one against its video, fix it, and
rename it from <name>.draft.json to <name>.json before using it in the eval.

Usage (from the repo root): python ai/eval/draft_sheets.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze import analyze_video  # noqa: E402

TESTDATA = Path(__file__).resolve().parents[2] / "testdata"
SHEET_FIELDS = ("label", "description", "anchor", "position", "video_seconds")


def main():
    for video in sorted(TESTDATA.glob("*.[mM][oO][vV]")):
        sheet = TESTDATA / f"{video.stem}.json"
        draft = TESTDATA / f"{video.stem}.draft.json"
        if sheet.exists() or draft.exists():
            continue
        print(f"analyzing {video.name}...", flush=True)
        try:
            items = analyze_video(video)
        except Exception as error:  # keep going so one bad video doesn't stop the batch
            print(f"  failed: {error}", flush=True)
            continue
        rows = [{key: item[key] for key in SHEET_FIELDS} for item in items]
        draft.write_text(json.dumps({"video": video.name, "items": rows}, indent=4) + "\n", encoding="utf-8")
        print(f"  wrote {draft.name} ({len(rows)} items)", flush=True)


if __name__ == "__main__":
    main()
