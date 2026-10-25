import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from diff import diff_scans  # noqa: E402


def item(label, description, anchor, position=None):
    return {"label": label, "description": description, "anchor": anchor,
            "position": position or f"on the {anchor}", "confidence": 0.9, "video_seconds": 1}


def test_nothing_changed():
    scan = [item("keys", "silver keys", "desk")]
    assert diff_scans(scan, scan) == {"moved": [], "missing": [], "new": []}


def test_single_item_moved_even_if_described_differently():
    result = diff_scans([item("keys", "silver keys", "counter")], [item("keys", "a bunch of metal keys", "desk")])
    assert [m["label"] for m in result["moved"]] == ["keys"]
    assert result["moved"][0]["from_position"] == "on the counter"
    assert result["moved"][0]["to_position"] == "on the desk"
    assert result["missing"] == [] and result["new"] == []


def test_reworded_position_is_not_a_move():
    old = [item("keys", "silver keys", "desk", "on the desk, left of the monitor")]
    new = [item("keys", "silver keys", "desk", "next to the monitor on the desk")]
    assert diff_scans(old, new)["moved"] == []


def test_two_sets_of_keys_tracked_separately():
    old = [item("keys", "silver keys on a blue lanyard", "desk"), item("keys", "gold car key with a black fob", "dresser")]
    new = [item("keys", "gold car key with a black fob", "nightstand"), item("keys", "silver keys on a blue lanyard", "desk")]
    result = diff_scans(old, new)
    assert [m["description"] for m in result["moved"]] == ["gold car key with a black fob"]
    assert result["moved"][0]["from_position"] == "on the dresser"
    assert result["missing"] == [] and result["new"] == []


def test_one_of_two_keys_goes_missing():
    old = [item("keys", "silver keys on a blue lanyard", "desk"), item("keys", "gold car key with a black fob", "dresser")]
    new = [item("keys", "silver keys on a blue lanyard", "desk")]
    result = diff_scans(old, new)
    assert [m["description"] for m in result["missing"]] == ["gold car key with a black fob"]
    assert result["moved"] == [] and result["new"] == []


def test_new_and_missing_labels():
    result = diff_scans([item("wallet", "brown wallet", "desk")], [item("phone", "black phone", "bed")])
    assert [m["label"] for m in result["missing"]] == ["wallet"]
    assert [n["label"] for n in result["new"]] == ["phone"]
