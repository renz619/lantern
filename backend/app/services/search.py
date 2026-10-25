"""Answer /find and /changes from the scans saved in the database."""
import sqlite3

from app.database import list_done_scans
from app.services import ai_tools
from app.services.media import scan_video_url

MAX_PAST_SIGHTINGS = 5


def _last_seen_items(scans: list[dict]) -> list[dict]:
    """For each label, the items from the newest scan that contained it.

    Searching "keys" should still find keys the latest scan missed, so the answer
    is where each label was *last seen*, not just what is in the newest scan.
    """
    covered: set[str] = set()
    found: list[dict] = []
    for scan in scans:  # newest first
        new_labels = {item["label"] for item in scan["items"]} - covered
        for item in scan["items"]:
            if item["label"] in new_labels:
                found.append({**item, "_scan": scan})
        covered |= new_labels
    return found


def _find_item(item: dict) -> dict:
    scan = item["_scan"]
    return {
        **{key: value for key, value in item.items() if key != "_scan"},
        "scan_id": scan["id"],
        "seen_at": scan["created_at"],
        "clip_url": scan_video_url(scan),
        "clip_start_seconds": item["video_seconds"],
    }


def _past_sightings(scans: list[dict], match: dict) -> list[dict]:
    """Only show unambiguous history with the same label and description.

    Labels alone cannot identify a physical item. Until the team agrees on
    persistent item IDs, omit uncertain history rather than choosing the first
    same-label object in an older scan.
    """
    sightings = []
    description = match["description"].strip().casefold()
    if not description:
        return sightings
    for scan in scans:
        if scan["id"] == match["scan_id"]:
            continue
        seen = [item for item in scan["items"] if item["label"] == match["label"]]
        if len(seen) == 1 and seen[0]["description"].strip().casefold() == description:
            sightings.append(
                {"scan_id": scan["id"], "seen_at": scan["created_at"], "position": seen[0]["position"]}
            )
    return sightings[:MAX_PAST_SIGHTINGS]


def _nothing_found() -> dict:
    return {"found": False, "items": [], "past_sightings": [], "clarify": None}


def find_items(connection: sqlite3.Connection, query: str) -> dict:
    scans = list_done_scans(connection)
    answer = ai_tools.answer_question(_last_seen_items(scans), query)
    matches = answer["matches"]
    if answer["status"] == "not_found" or not matches:
        return _nothing_found()

    labels = list(dict.fromkeys(match["label"] for match in matches))
    if len(labels) > 1:
        # "Did you mean your keys or your wallet?" Tapping an option searches that label.
        return {
            "found": True,
            "items": [],
            "past_sightings": [],
            "clarify": {"question": answer["question"], "options": labels},
        }

    # One label, possibly several items (two sets of keys): show them all.
    items = [_find_item(match) for match in matches]
    past = _past_sightings(scans, items[0]) if len(items) == 1 else []
    return {"found": True, "items": items, "past_sightings": past, "clarify": None}


def get_changes(connection: sqlite3.Connection) -> dict:
    scans = list_done_scans(connection)
    if len(scans) < 2:
        return {"from_scan": None, "to_scan": None, "moved": [], "missing": [], "new": []}
    newest, previous = scans[0], scans[1]
    changes = ai_tools.diff_scans(previous["items"], newest["items"])
    return {"from_scan": previous["id"], "to_scan": newest["id"], **changes}
