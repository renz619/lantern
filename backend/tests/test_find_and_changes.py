"""/find and /changes read real scans from the database, using member A's search and diff."""
import pytest
from fastapi.testclient import TestClient

from app.database import add_sightings, connect_database, create_scan, create_tables, update_scan_status
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("LANTERN_DB_PATH", str(tmp_path / "lantern.sqlite"))
    monkeypatch.setenv("LANTERN_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("LANTERN_ANALYZER", "mock")
    return tmp_path


def item(label, description, anchor, seconds=1.0, position=None):
    return {"label": label, "description": description, "anchor": anchor,
            "position": position or f"on the {anchor}", "confidence": 0.9, "video_seconds": seconds}


def add_scan(items, created_at, status="done", video_path=None):
    connection = connect_database()
    create_tables(connection)
    try:
        scan_id = create_scan(connection, status="processing", created_at=created_at, video_path=video_path)
        add_sightings(connection, scan_id, items)
        update_scan_status(connection, scan_id, status)
    finally:
        connection.close()
    return scan_id


def test_find_with_no_scans_finds_nothing() -> None:
    body = client.get("/find", params={"q": "keys"}).json()

    assert body == {"found": False, "items": [], "past_sightings": [], "clarify": None}


def test_find_returns_where_the_item_was_last_seen() -> None:
    scan_id = add_scan([item("keys", "silver keys", "desk", 4.5, "on the desk, left of the monitor")],
                       "2026-10-24T18:00:00Z")

    body = client.get("/find", params={"q": "where are my keys?"}).json()

    assert body["found"] is True
    [found] = body["items"]
    assert found["label"] == "keys"
    assert found["position"] == "on the desk, left of the monitor"
    assert found["scan_id"] == scan_id
    assert found["clip_start_seconds"] == 4.5
    assert body["clarify"] is None


def test_find_shows_every_item_when_two_share_a_label() -> None:
    add_scan([item("keys", "silver keys on a blue lanyard", "desk"),
              item("keys", "gold car key with a black fob", "dresser")], "2026-10-24T18:00:00Z")

    body = client.get("/find", params={"q": "keys"}).json()

    assert len(body["items"]) == 2
    assert {i["anchor"] for i in body["items"]} == {"desk", "dresser"}
    assert body["past_sightings"] == []


def test_find_uses_the_newest_scan_and_lists_earlier_sightings() -> None:
    old = add_scan([item("keys", "silver keys", "counter")], "2026-10-23T09:00:00Z")
    new = add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z")

    body = client.get("/find", params={"q": "keys"}).json()

    assert [i["scan_id"] for i in body["items"]] == [new]
    assert body["past_sightings"] == [
        {"scan_id": old, "seen_at": "2026-10-23T09:00:00Z", "position": "on the counter"}
    ]


def test_find_still_answers_for_an_item_the_latest_scan_missed() -> None:
    old = add_scan([item("wallet", "brown wallet", "dresser")], "2026-10-23T09:00:00Z")
    add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z")

    body = client.get("/find", params={"q": "wallet"}).json()

    assert [i["scan_id"] for i in body["items"]] == [old]


def test_find_ignores_failed_scans() -> None:
    add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z", status="failed")

    assert client.get("/find", params={"q": "keys"}).json()["found"] is False


def test_find_asks_which_item_when_the_search_matches_different_labels() -> None:
    add_scan([item("headphones", "white over-ear headphones", "nightstand"),
              item("airpods", "white earbud case", "desk")], "2026-10-24T18:00:00Z")

    body = client.get("/find", params={"q": "white"}).json()

    assert body["found"] is True and body["items"] == []
    assert set(body["clarify"]["options"]) == {"headphones", "airpods"}


def test_find_unknown_item_is_not_found() -> None:
    add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z")

    assert client.get("/find", params={"q": "trombone"}).json()["found"] is False


def test_find_includes_a_playable_clip_url_when_the_video_is_saved(isolated_storage) -> None:
    uploads = isolated_storage / "uploads"
    uploads.mkdir()
    video = uploads / "room.mp4"
    video.write_bytes(b"video")
    scan_id = add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z", video_path=str(video))

    [found] = client.get("/find", params={"q": "keys"}).json()["items"]

    assert found["clip_url"] == f"/media/scans/{scan_id}/video"


def test_changes_needs_two_finished_scans() -> None:
    add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z")

    body = client.get("/changes").json()

    assert body == {"from_scan": None, "to_scan": None, "moved": [], "missing": [], "new": []}


def test_changes_reports_moved_missing_and_new() -> None:
    old = add_scan([item("keys", "silver keys", "counter"), item("wallet", "brown wallet", "desk")],
                   "2026-10-23T09:00:00Z")
    new = add_scan([item("keys", "silver keys", "desk"), item("phone", "black phone", "bed")],
                   "2026-10-24T18:00:00Z")

    body = client.get("/changes").json()

    assert (body["from_scan"], body["to_scan"]) == (old, new)
    assert [m["label"] for m in body["moved"]] == ["keys"]
    assert body["moved"][0]["from_position"] == "on the counter"
    assert body["moved"][0]["to_position"] == "on the desk"
    assert [m["label"] for m in body["missing"]] == ["wallet"]
    assert [n["label"] for n in body["new"]] == ["phone"]


def test_changes_compares_only_the_two_newest_finished_scans() -> None:
    add_scan([item("keys", "silver keys", "bed")], "2026-10-22T09:00:00Z")
    old = add_scan([item("keys", "silver keys", "counter")], "2026-10-23T09:00:00Z")
    add_scan([item("keys", "silver keys", "dresser")], "2026-10-23T12:00:00Z", status="failed")
    new = add_scan([item("keys", "silver keys", "desk")], "2026-10-24T18:00:00Z")

    body = client.get("/changes").json()

    assert (body["from_scan"], body["to_scan"]) == (old, new)


def test_full_flow_upload_then_find() -> None:
    """Upload a video, let the (mock) analyzer finish, then search for what it found."""
    upload = client.post("/scans", files={"video": ("room.mp4", b"fake video", "video/mp4")})
    scan_id = upload.json()["scan_id"]
    assert client.get(f"/scans/{scan_id}").json()["status"] == "done"

    body = client.get("/find", params={"q": "wallet"}).json()

    assert body["found"] is True
    assert body["items"][0]["scan_id"] == scan_id
    assert body["items"][0]["clip_url"] == f"/media/scans/{scan_id}/video"
