from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_scan_returns_an_id_without_saving_or_analyzing() -> None:
    response = client.post(
        "/scans",
        files={"video": ("room.mp4", b"fake video bytes", "video/mp4")},
    )

    assert response.status_code == 202
    assert response.json() == {"scan_id": 99}


def test_list_scans_returns_the_frontend_shape() -> None:
    response = client.get("/scans")

    assert response.status_code == 200
    scans = response.json()
    assert isinstance(scans, list)
    assert scans[0] == {
        "id": 3,
        "created_at": "2026-10-24T18:42:00Z",
        "status": "done",
        "item_count": 7,
    }


def test_scan_detail_contains_contract_items() -> None:
    response = client.get("/scans/3")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert len(body["items"]) == 7
    assert set(body["items"][0]) == {
        "label",
        "description",
        "anchor",
        "position",
        "confidence",
        "video_seconds",
    }


def test_uploaded_scan_becomes_done_after_three_checks() -> None:
    client.post(
        "/scans",
        files={"video": ("room.mp4", b"fake video bytes", "video/mp4")},
    )

    statuses = [client.get("/scans/99").json()["status"] for _ in range(3)]

    assert statuses == ["processing", "processing", "done"]


def test_unknown_scan_returns_404() -> None:
    response = client.get("/scans/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scan not found"}


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
