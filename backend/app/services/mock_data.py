from copy import deepcopy


MOCK_VIDEO_URL = (
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
)

MOCK_ITEMS = [
    {
        "label": "keys",
        "description": "silver keys on a blue lanyard",
        "anchor": "desk",
        "position": "on the desk, left of the monitor",
        "confidence": 0.87,
        "video_seconds": 4.5,
    },
    {
        "label": "keys",
        "description": "gold car key with a black fob",
        "anchor": "dresser",
        "position": "on the dresser, in the dish",
        "confidence": 0.83,
        "video_seconds": 9.2,
    },
    {
        "label": "wallet",
        "description": "brown leather wallet",
        "anchor": "dresser",
        "position": "on the dresser, next to the lamp",
        "confidence": 0.81,
        "video_seconds": 8.0,
    },
    {
        "label": "phone",
        "description": "black phone in a clear case",
        "anchor": "bed",
        "position": "on the bed, near the pillow",
        "confidence": 0.92,
        "video_seconds": 11.2,
    },
    {
        "label": "headphones",
        "description": "white over-ear headphones",
        "anchor": "nightstand",
        "position": "on the nightstand, below the lamp",
        "confidence": 0.78,
        "video_seconds": 13.4,
    },
    {
        "label": "charger",
        "description": "white phone charger with a long cable",
        "anchor": "nightstand",
        "position": "plugged in on the nightstand",
        "confidence": 0.70,
        "video_seconds": 14.0,
    },
    {
        "label": "glasses",
        "description": "black round glasses",
        "anchor": "shelf",
        "position": "on the shelf, above the desk",
        "confidence": 0.74,
        "video_seconds": 6.1,
    },
]

MOCK_SCANS = [
    {
        "id": 3,
        "created_at": "2026-10-24T18:42:00Z",
        "status": "done",
        "item_count": len(MOCK_ITEMS),
    },
    {
        "id": 2,
        "created_at": "2026-10-24T13:10:00Z",
        "status": "done",
        "item_count": 5,
    },
    {
        "id": 1,
        "created_at": "2026-10-23T09:05:00Z",
        "status": "done",
        "item_count": 5,
    },
]

MOCK_CHANGES = {
    "from_scan": 2,
    "to_scan": 3,
    "moved": [
        {
            "label": "keys",
            "description": "silver keys on a blue lanyard",
            "from_position": "on the kitchen counter",
            "to_position": "on the desk, left of the monitor",
        }
    ],
    "missing": [
        {
            "label": "water bottle",
            "description": "black insulated water bottle",
            "last_position": "on the dresser",
        }
    ],
    "new": [
        {
            "label": "headphones",
            "description": "white over-ear headphones",
            "position": "on the nightstand, below the lamp",
        }
    ],
}

_NEW_SCAN_ID = 99
_new_scan_checks = 0


def start_mock_scan() -> dict:
    global _new_scan_checks
    _new_scan_checks = 0
    return {"scan_id": _NEW_SCAN_ID}


def list_mock_scans() -> list[dict]:
    return deepcopy(MOCK_SCANS)


def get_mock_scan(scan_id: int) -> dict | None:
    global _new_scan_checks

    if scan_id == _NEW_SCAN_ID:
        _new_scan_checks += 1
        if _new_scan_checks < 3:
            return {
                "id": scan_id,
                "created_at": "2026-10-24T19:00:00Z",
                "status": "processing",
                "error": None,
                "video_url": None,
                "items": [],
            }
        created_at = "2026-10-24T19:00:00Z"
    else:
        matching_scan = next(
            (scan for scan in MOCK_SCANS if scan["id"] == scan_id),
            None,
        )
        if matching_scan is None:
            return None
        created_at = matching_scan["created_at"]

    return {
        "id": scan_id,
        "created_at": created_at,
        "status": "done",
        "error": None,
        "video_url": MOCK_VIDEO_URL,
        "items": deepcopy(MOCK_ITEMS),
    }


def find_mock_items(query: str) -> dict:
    normalized_query = query.strip().lower()
    if normalized_query == "charger":
        return {
            "found": True,
            "items": [],
            "past_sightings": [],
            "clarify": {
                "question": "Which charger?",
                "options": ["phone charger", "laptop charger"],
            },
        }

    matches = [
        item
        for item in MOCK_ITEMS
        if normalized_query in item["label"] or item["label"] in normalized_query
    ]
    enriched_matches = [
        {
            **item,
            "scan_id": 3,
            "seen_at": "2026-10-24T18:42:00Z",
            "clip_url": MOCK_VIDEO_URL,
            "clip_start_seconds": item["video_seconds"],
        }
        for item in matches
    ]
    return {
        "found": bool(enriched_matches),
        "items": enriched_matches,
        "past_sightings": (
            [
                {
                    "scan_id": 2,
                    "seen_at": "2026-10-24T13:10:00Z",
                    "position": "on the kitchen counter",
                },
                {
                    "scan_id": 1,
                    "seen_at": "2026-10-23T09:05:00Z",
                    "position": "on the nightstand",
                },
            ]
            if len(enriched_matches) == 1
            else []
        ),
        "clarify": None,
    }


def get_mock_changes() -> dict:
    return deepcopy(MOCK_CHANGES)
