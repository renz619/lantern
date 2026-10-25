import sqlite3

import pytest

from app.database import (
    add_sightings,
    connect_database,
    create_scan,
    create_tables,
    get_scan,
    list_scans,
    update_scan_status,
)


@pytest.fixture
def database(tmp_path):
    connection = connect_database(tmp_path / "test.sqlite")
    create_tables(connection)
    yield connection
    connection.close()


def item(label: str, seconds: float) -> dict:
    return {
        "label": label,
        "description": f"test {label}",
        "anchor": "desk",
        "position": "on the desk",
        "confidence": 0.9,
        "video_seconds": seconds,
    }


def test_create_tables_creates_scans_and_sightings(database) -> None:
    rows = database.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()

    table_names = {row["name"] for row in rows}
    assert {"scans", "sightings"}.issubset(table_names)


def test_create_and_update_scan(database) -> None:
    scan_id = create_scan(
        database,
        video_path="uploads/room.mp4",
        created_at="2026-10-24T20:00:00Z",
    )

    scan = get_scan(database, scan_id)
    assert scan == {
        "id": scan_id,
        "created_at": "2026-10-24T20:00:00Z",
        "status": "processing",
        "video_path": "uploads/room.mp4",
        "error": None,
        "items": [],
    }

    update_scan_status(database, scan_id, "failed", "Gemini timed out")
    failed_scan = get_scan(database, scan_id)
    assert failed_scan["status"] == "failed"
    assert failed_scan["error"] == "Gemini timed out"


def test_sightings_are_saved_and_returned_in_video_order(database) -> None:
    scan_id = create_scan(database, created_at="2026-10-24T20:00:00Z")

    add_sightings(database, scan_id, [item("keys", 14.5), item("wallet", 6.0)])

    scan = get_scan(database, scan_id)
    assert [saved["label"] for saved in scan["items"]] == ["wallet", "keys"]
    assert set(scan["items"][0]) == {
        "label",
        "description",
        "anchor",
        "position",
        "confidence",
        "video_seconds",
    }


def test_scan_history_is_newest_first_with_item_counts(database) -> None:
    older_id = create_scan(database, created_at="2026-10-24T10:00:00Z")
    newer_id = create_scan(database, created_at="2026-10-24T20:00:00Z")
    add_sightings(database, older_id, [item("keys", 1.0)])
    add_sightings(database, newer_id, [item("wallet", 2.0), item("phone", 3.0)])

    history = list_scans(database)

    assert [scan["id"] for scan in history] == [newer_id, older_id]
    assert [scan["item_count"] for scan in history] == [2, 1]


def test_sighting_requires_a_real_scan(database) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        add_sightings(database, 999, [item("keys", 1.0)])


def test_invalid_scan_status_is_rejected(database) -> None:
    with pytest.raises(ValueError, match="Invalid scan status"):
        create_scan(database, status="almost done")
