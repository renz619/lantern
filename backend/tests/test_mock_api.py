from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import connect_database, get_scan
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    database_path = tmp_path / "lantern.sqlite"
    upload_directory = tmp_path / "uploads"
    monkeypatch.setenv("LANTERN_DB_PATH", str(database_path))
    monkeypatch.setenv("LANTERN_UPLOAD_DIR", str(upload_directory))
    monkeypatch.setenv("LANTERN_ANALYZER", "mock")
    monkeypatch.delenv("GEMINI_MOCK", raising=False)
    return {
        "database_path": database_path,
        "upload_directory": upload_directory,
    }


def upload_video(filename: str = "room.mp4", content: bytes = b"fake video bytes"):
    return client.post(
        "/scans",
        files={"video": (filename, content, "video/mp4")},
    )


def test_upload_scan_saves_a_safe_filename_and_finishes_analysis(
    isolated_storage,
) -> None:
    response = upload_video()

    assert response.status_code == 202
    scan_id = response.json()["scan_id"]
    saved_files = list(isolated_storage["upload_directory"].iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].name != "room.mp4"
    assert saved_files[0].suffix == ".mp4"
    assert saved_files[0].read_bytes() == b"fake video bytes"

    connection = connect_database(isolated_storage["database_path"])
    try:
        scan = get_scan(connection, scan_id)
    finally:
        connection.close()
    assert scan["status"] == "done"
    assert scan["error"] is None
    assert len(scan["items"]) == 7


def test_list_scans_reads_from_the_database() -> None:
    first_scan_id = upload_video("first.mp4").json()["scan_id"]
    second_scan_id = upload_video("second.mp4").json()["scan_id"]

    response = client.get("/scans")

    assert response.status_code == 200
    scans = response.json()
    assert [scan["id"] for scan in scans] == [second_scan_id, first_scan_id]
    assert [scan["item_count"] for scan in scans] == [7, 7]
    assert all(scan["status"] == "done" for scan in scans)


def test_scan_detail_reads_contract_items_from_the_database() -> None:
    scan_id = upload_video().json()["scan_id"]

    response = client.get(f"/scans/{scan_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["video_url"] is None
    assert len(body["items"]) == 7
    assert set(body["items"][0]) == {
        "label",
        "description",
        "anchor",
        "position",
        "confidence",
        "video_seconds",
    }


def test_analysis_failure_is_stored_without_fake_success(
    isolated_storage,
    monkeypatch,
) -> None:
    monkeypatch.setenv("LANTERN_ANALYZER", "unknown")

    response = upload_video()

    assert response.status_code == 202
    scan_id = response.json()["scan_id"]
    connection = connect_database(isolated_storage["database_path"])
    try:
        scan = get_scan(connection, scan_id)
    finally:
        connection.close()
    assert scan["status"] == "failed"
    assert "Invalid LANTERN_ANALYZER" in scan["error"]
    assert scan["items"] == []


def test_unsupported_upload_is_rejected(isolated_storage) -> None:
    response = upload_video("notes.txt", b"not a video")

    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported video type"}
    assert not isolated_storage["upload_directory"].exists()


def test_empty_upload_is_rejected(isolated_storage) -> None:
    response = upload_video(content=b"")

    assert response.status_code == 400
    assert response.json() == {"detail": "Video is empty"}
    assert list(isolated_storage["upload_directory"].iterdir()) == []


def test_unknown_scan_returns_404() -> None:
    response = client.get("/scans/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scan not found"}


def test_missing_video_is_rejected() -> None:
    response = client.post(
        "/scans",
    )

    assert response.status_code == 422


def test_find_returns_a_list_for_duplicate_labels() -> None:
    response = client.get("/find", params={"q": "keys"})

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert len(body["items"]) == 2
    assert {item["label"] for item in body["items"]} == {"keys"}
    assert body["clarify"] is None


def test_find_can_request_clarification() -> None:
    response = client.get("/find", params={"q": "charger"})

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["items"] == []
    assert body["clarify"]["options"] == ["phone charger", "laptop charger"]


def test_changes_returns_moved_missing_and_new_lists() -> None:
    response = client.get("/changes")

    assert response.status_code == 200
    body = response.json()
    assert body["from_scan"] == 2
    assert body["to_scan"] == 3
    assert set(body) == {"from_scan", "to_scan", "moved", "missing", "new"}
    assert body["moved"][0]["label"] == "keys"
