from fastapi.testclient import TestClient

from app.main import create_app, get_frontend_dir


def make_site(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Lantern site</h1>", encoding="utf-8")
    return tmp_path


def test_no_build_means_api_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_FRONTEND_DIST", str(tmp_path))  # empty folder, no index.html

    assert get_frontend_dir() is None
    assert TestClient(create_app()).get("/").status_code == 404


def test_built_site_is_served_from_the_same_address(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_FRONTEND_DIST", str(make_site(tmp_path)))
    client = TestClient(create_app())

    page = client.get("/")
    assert page.status_code == 200
    assert "Lantern site" in page.text
    assert client.get("/health").json() == {"status": "ok"}  # API routes still win
