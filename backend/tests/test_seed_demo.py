"""The demo uses real SQLite endpoints with explicitly synthetic sightings."""
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import connect_database, create_scan, create_tables, get_scan, list_scans
from app.main import app
from app.scripts.seed_demo import seed_demo


@pytest.fixture
def demo_storage(tmp_path, monkeypatch):
    database_path = tmp_path / "demo.sqlite"
    monkeypatch.setenv("LANTERN_DB_PATH", str(database_path))
    monkeypatch.setenv("LANTERN_UPLOAD_DIR", str(tmp_path / "uploads"))
    # Search/diff and seed must work even with no Gemini credentials.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    return database_path


def test_seed_exercises_real_search_changes_and_history(demo_storage):
    morning, evening = seed_demo(demo_storage)
    client = TestClient(app)

    history = client.get("/scans")
    assert history.status_code == 200
    assert [scan["id"] for scan in history.json()] == [evening, morning]
    assert [scan["item_count"] for scan in history.json()] == [3, 3]
    assert all(scan["status"] == "done" for scan in history.json())

    keys = client.get("/find", params={"q": "where are my keys?"}).json()
    assert keys["items"][0]["scan_id"] == evening
    assert keys["items"][0]["anchor"] == "nightstand"
    assert keys["items"][0]["clip_url"] is None
    assert keys["past_sightings"][0]["scan_id"] == morning

    wallet = client.get("/find", params={"q": "wallet"}).json()
    assert wallet["items"][0]["scan_id"] == morning

    changes = client.get("/changes").json()
    assert (changes["from_scan"], changes["to_scan"]) == (morning, evening)
    assert [item["label"] for item in changes["moved"]] == ["keys"]
    assert [item["label"] for item in changes["missing"]] == ["wallet"]
    assert [item["label"] for item in changes["new"]] == ["phone"]


def test_seed_is_repeatable_and_preserves_later_real_scans(demo_storage):
    original_ids = seed_demo(demo_storage)
    connection = connect_database(demo_storage)
    try:
        real_id = create_scan(connection, status="done")
        before = list_scans(connection)
        assert seed_demo(demo_storage) == original_ids
        assert list_scans(connection) == before
        assert get_scan(connection, real_id) is not None
    finally:
        connection.close()


def test_seed_refuses_an_existing_database_with_user_scans(demo_storage):
    connection = connect_database(demo_storage)
    try:
        create_tables(connection)
        real_id = create_scan(connection, status="done")
        before = get_scan(connection, real_id)
        with pytest.raises(ValueError, match="contains scans"):
            seed_demo(demo_storage)
        assert get_scan(connection, real_id) == before
        assert len(list_scans(connection)) == 1
    finally:
        connection.close()


def test_seed_can_copy_two_local_videos_for_playback(demo_storage, tmp_path):
    morning_video = tmp_path / "morning.mp4"
    evening_video = tmp_path / "evening.mov"
    morning_video.write_bytes(b"morning video bytes")
    evening_video.write_bytes(b"evening video bytes")
    morning, evening = seed_demo(
        demo_storage, morning_video=morning_video, evening_video=evening_video
    )
    client = TestClient(app)

    found = client.get("/find", params={"q": "keys"}).json()["items"][0]
    assert found["clip_url"] == f"/media/scans/{evening}/video"
    response = client.get(found["clip_url"], headers={"Range": "bytes=0-6"})
    assert response.status_code == 206
    assert response.content == b"evening"
    assert client.get(f"/media/scans/{morning}/video").content == b"morning video bytes"
    assert morning_video.read_bytes() == b"morning video bytes"
    uploads = tmp_path / "uploads"
    files_before = set(uploads.iterdir())
    assert seed_demo(demo_storage, morning_video=morning_video, evening_video=evening_video) == (morning, evening)
    assert set(uploads.iterdir()) == files_before


def test_seed_validates_videos_before_creating_scans(demo_storage, tmp_path):
    with pytest.raises(ValueError, match="both"):
        seed_demo(demo_storage, morning_video=tmp_path / "missing.mp4")
    with pytest.raises(ValueError, match="not found"):
        seed_demo(
            demo_storage,
            morning_video=tmp_path / "missing.mp4",
            evening_video=tmp_path / "missing.mov",
        )
    assert not demo_storage.exists()


def test_seed_rolls_back_records_and_copies_on_failure(demo_storage, tmp_path, monkeypatch):
    from app.scripts import seed_demo as seed_module

    video = tmp_path / "room.mp4"
    video.write_bytes(b"local video")
    original_copy = seed_module.shutil.copyfile
    copied = []

    def fail_second_copy(source, destination):
        copied.append(destination)
        if len(copied) == 2:
            raise OSError("test disk full")
        return original_copy(source, destination)

    monkeypatch.setattr(seed_module.shutil, "copyfile", fail_second_copy)
    with pytest.raises(OSError, match="disk full"):
        seed_demo(demo_storage, morning_video=video, evening_video=video)

    connection = connect_database(demo_storage)
    try:
        assert list_scans(connection) == []
    finally:
        connection.close()
    assert list((tmp_path / "uploads").iterdir()) == []


def test_seed_cli_works_from_backend_and_repo_root(demo_storage):
    backend_dir = Path(__file__).resolve().parents[1]
    commands = [
        (backend_dir, ["-m", "app.scripts.seed_demo"]),
        (backend_dir.parent, ["backend/scripts/seed_demo.py"]),
    ]
    for working_directory, arguments in commands:
        result = subprocess.run(
            [sys.executable, *arguments, "--database", str(demo_storage)],
            cwd=working_directory,
            text=True,
            capture_output=True,
            check=True,
        )
        assert "Synthetic demo data ready" in result.stdout
        assert "No Gemini requests" in result.stdout

    connection = connect_database(demo_storage)
    try:
        assert len(list_scans(connection)) == 2
    finally:
        connection.close()
