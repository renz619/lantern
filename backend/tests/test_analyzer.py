import pytest

from app.services import analyzer


def test_mock_analyzer_is_explicit_and_returns_contract_items(monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_ANALYZER", "mock")

    items = analyzer.analyze_video("unused.mp4")

    assert len(items) == 7
    assert items[0]["label"] == "keys"


def test_gemini_failure_is_not_replaced_with_mock_results(monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_ANALYZER", "gemini")
    monkeypatch.delenv("GEMINI_MOCK", raising=False)

    def fail(_path, _watchlist):
        raise RuntimeError("Gemini unavailable")

    monkeypatch.setattr(analyzer, "_analyze_with_gemini", fail)

    with pytest.raises(RuntimeError, match="Gemini unavailable"):
        analyzer.analyze_video("room.mp4")


def test_gemini_mode_rejects_ai_mock_environment(monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_ANALYZER", "gemini")
    monkeypatch.setenv("GEMINI_MOCK", "1")

    with pytest.raises(RuntimeError, match="GEMINI_MOCK"):
        analyzer.analyze_video("room.mp4")


def test_adapter_can_import_member_a_analyzer(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_MOCK", "1")

    items = analyzer._analyze_with_gemini("unused.mp4", None)

    assert [item["label"] for item in items] == ["wallet", "keys"]


def test_unknown_analyzer_mode_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("LANTERN_ANALYZER", "mystery")

    with pytest.raises(ValueError, match="Invalid LANTERN_ANALYZER"):
        analyzer.analyze_video("room.mp4")
