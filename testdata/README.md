# Test data

Owner: D. Record 8-10 videos of a room in different situations and write a ground truth (exact answer sheet) for each. A uses these for the eval in `ai/eval/`.

**Do not commit the videos.** `.gitignore` blocks `*.mp4`, `*.mov`, `*.webm` and `*.mkv`. Share them through a shared drive and keep only the answer sheets here.

## Videos to record

| File | Situation | Recorded | Ground truth written |
| --- | --- | --- | --- |
| `baseline` | Tidy room, all items in normal spots | [ ] | [ ] |
| `moved` | One item moved since baseline | [ ] | [ ] |
| `missing` | One item removed | [ ] | [ ] |
| `new_item` | A new item added | [ ] | [ ] |
| `dim_light` | Low lighting | [ ] | [ ] |
| `messy_desk` | Cluttered desk | [ ] | [ ] |
| `fast_pan` | Turned too fast, on purpose | [ ] | [ ] |
| `empty_room` | Furniture only, no small items | [ ] | [ ] |

Keep each video 30-60 seconds. A needs 5 videos first.

## Ground truth format

One JSON file per video, named `<video>.json`, using the item shape from [docs/contract.md](../docs/contract.md). Rough times are fine for `video_seconds`.

```json
{
  "video": "baseline",
  "items": [
    {
      "label": "keys",
      "anchor": "desk",
      "position": "on the desk, left of the monitor",
      "video_seconds": 14.5
    }
  ]
}
```

List only items that really are in the video, so A can count found, missed and false alarms.
