import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze import ALIASES, ALLOWLIST, ANCHOR_ALIASES, ANCHORS, normalize_anchor, normalize_label  # noqa: E402


def test_no_duplicate_names():
    assert len(ALLOWLIST) == len(set(ALLOWLIST))
    assert len(ANCHORS) == len(set(ANCHORS))


def test_every_alias_points_at_a_real_label():
    for alias, target in ALIASES.items():
        assert target in ALLOWLIST, f"alias '{alias}' -> '{target}' is not in labels"


def test_every_anchor_alias_points_at_a_real_anchor():
    for alias, target in ANCHOR_ALIASES.items():
        assert target in ANCHORS, f"anchor alias '{alias}' -> '{target}' is not in anchors"


def test_names_are_lowercase_and_trimmed():
    for name in [*ALLOWLIST, *ALIASES, *ANCHORS, *ANCHOR_ALIASES]:
        assert name == name.strip().lower(), name


def test_an_alias_is_not_also_a_separate_label_that_it_overrides():
    # "earbud case" is both a label and an alias on purpose in the past; flag new clashes.
    clashes = {a for a in ALIASES if a in ALLOWLIST and ALIASES[a] != a}
    assert clashes <= {"earbud case", "earbuds", "pen"}, clashes


def test_new_objects_resolve():
    assert normalize_label("Kindle") == "tablet"
    assert normalize_label("AirTag") == "tracker"
    assert normalize_label("thumb drive") == "usb drive"
    assert normalize_label("scissors") == "scissors"
    assert normalize_anchor("Kitchen Counter") == "counter"
    assert normalize_anchor("Standing Desk") == "desk"
