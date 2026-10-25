import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from analyze import ANCHORS, analyze_video, build_prompt, clean_items, normalize_anchor, normalize_label  # noqa: E402
from run_eval import match_items  # noqa: E402


def item(label, seconds, confidence=0.9, description="x", position="on the desk", anchor="desk"):
    return {"label": label, "description": description, "anchor": anchor,
            "position": position, "confidence": confidence, "video_seconds": seconds}


def test_aliases_become_one_label():
    assert normalize_label("Earbuds") == "earbuds"
    assert normalize_label("earphones") == "earbuds"
    assert normalize_label("Air Pods") == "airpods"
    assert normalize_label("bottle") == "water bottle"
    assert normalize_label("Mechanical Pencil") == "pencil"
    assert normalize_label("pen") == "pen"
    assert normalize_label("Ballpoint Pen") == "pen"


def test_low_confidence_dropped():
    assert clean_items([item("keys", 1, confidence=0.3)]) == []


def test_furniture_and_unknown_items_dropped():
    assert clean_items([item("desk", 1), item("monitor", 2)]) == []


def test_watchlist_item_kept():
    assert clean_items([item("stapler", 1)], watchlist=["stapler"])[0]["label"] == "stapler"


def test_small_valuables_kept():
    labels = [i["label"] for i in clean_items([item("airpods", 1), item("charger", 2), item("pencil", 3)])]
    assert labels == ["airpods", "charger", "pencil"]


def test_person_text_is_removed():
    out = clean_items([item("glasses", 1, description="worn by a man", position="on his face")])
    assert out[0]["description"] == "glasses"
    assert out[0]["position"] == "near the desk"


def test_surface_is_not_mistaken_for_face():
    out = clean_items([item("keys", 1, position="on the desk surface")])
    assert out[0]["position"] == "on the desk surface"


def test_prompt_mentions_privacy_and_watchlist():
    prompt = build_prompt(["stapler"])
    assert "stapler" in prompt and "airpods" in prompt and "PRIVACY" in prompt


def test_mock_mode(monkeypatch):
    monkeypatch.setenv("GEMINI_MOCK", "1")
    assert analyze_video("whatever.mp4")[0]["label"] == "wallet"


def test_match_items_scores_found_missed_false_alarms():
    truth = [item("keys", 8), item("airpods", 14), item("wallet", 26)]
    found = [item("keys", 9), item("wallet", 40), item("laptop", 4)]
    matched, missed, false_alarms = match_items(found, truth)
    assert len(matched) == 1
    assert [m["label"] for m in missed] == ["airpods", "wallet"]
    assert [f["label"] for f in false_alarms] == ["wallet", "laptop"]


def test_anchor_synonyms_become_one_anchor():
    assert normalize_anchor("Television") == "tv stand"
    assert normalize_anchor(" Sofa ") == "couch"
    assert normalize_anchor("bookshelf") == "shelf"
    assert normalize_anchor("desk") == "desk"


def test_unknown_anchor_is_kept():
    assert normalize_anchor("Window Seat") == "window seat"


def test_clean_items_standardizes_the_anchor():
    cleaned = clean_items([item("keys", 1, anchor="Television")])
    assert cleaned[0]["anchor"] == "tv stand"


def test_prompt_lists_the_standard_anchors():
    prompt = build_prompt()
    assert "{anchors}" not in prompt
    assert all(anchor in prompt for anchor in ANCHORS)
