import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from answer import answer_question  # noqa: E402


def item(label, description, position, anchor="desk", seconds=1.0):
    return {"label": label, "description": description, "anchor": anchor, "position": position,
            "confidence": 0.9, "video_seconds": seconds}


ITEMS = [
    item("wallet", "white Bank of America card holder", "on the desk, in front of the keyboard", seconds=6),
    item("keys", "multicolored keys with a UT orange decoration", "on the desk, between the monitors", seconds=8),
    item("water bottle", "black Owala water bottle", "on the desk, between the monitors", seconds=9),
    item("phone", "black smartphone lying face up", "on the desk, in front of the keyboard", seconds=10),
    item("airpods", "airpods in a black case", "on top of the PC", seconds=14),
    item("backpack", "backpack", "on the chair", anchor="chair", seconds=15),
    item("charger", "phone charger", "plugged into the PC", seconds=21),
    item("wallet", "larger brown wallet", "on the desk, in front of the monitor", seconds=26),
    item("keys", "blue key chain with a small room key", "on the desk, in front of the monitor", seconds=27),
]


def test_single_match_is_found():
    result = answer_question(ITEMS, "where are my airpods?")
    assert result["status"] == "found"
    assert result["matches"][0]["position"] == "on top of the PC"
    assert "on top of the PC" in result["message"]


def test_fuzzy_charger_matches_phone_charger():
    assert answer_question(ITEMS, "phone charger")["matches"][0]["label"] == "charger"
    assert answer_question(ITEMS, "where is my charger")["matches"][0]["label"] == "charger"


def test_phone_does_not_match_phone_charger_when_phone_exists():
    result = answer_question(ITEMS, "phone")
    assert result["status"] == "found"
    assert result["matches"][0]["label"] == "phone"


def test_alias_and_plural_queries():
    earbuds = [item("earbuds", "white earbuds in a case", "on the nightstand", anchor="nightstand")]
    assert answer_question(earbuds, "earphones")["matches"][0]["label"] == "earbuds"
    assert answer_question(ITEMS, "earbuds")["status"] == "not_found"  # airpods are a different label now
    assert answer_question(ITEMS, "my bottle")["matches"][0]["label"] == "water bottle"


def test_typo_still_matches():
    assert answer_question(ITEMS, "walet")["status"] == "ambiguous"
    assert answer_question(ITEMS, "airpodz")["matches"][0]["label"] == "airpods"


def test_two_of_the_same_label_asks_which_one():
    result = answer_question(ITEMS, "where are my keys")
    assert result["status"] == "ambiguous"
    assert "2 keys" in result["question"]
    assert len(result["choices"]) == 2
    assert result["choices"][0]["description"].startswith("multicolored")


def test_choice_resolves_the_follow_up():
    result = answer_question(ITEMS, "wallet", choice=1)
    assert result["status"] == "found"
    assert result["matches"][0]["description"] == "larger brown wallet"


def test_description_words_find_the_right_item():
    result = answer_question(ITEMS, "the blue key chain")
    assert result["status"] == "found"
    assert result["matches"][0]["position"].endswith("in front of the monitor")


def test_different_labels_ask_which_kind():
    items = [item("wallet", "card holder", "on the desk"), item("gift card", "store gift card", "on the shelf", anchor="shelf")]
    result = answer_question(items, "card")
    assert result["status"] == "ambiguous"
    assert "wallet" in result["question"] and "gift card" in result["question"]


def test_id_and_bank_cards_are_found_as_a_wallet():
    items = [item("id card", "student id", "on the couch cushion", anchor="couch")]
    assert answer_question(items, "where is my wallet")["status"] == "found"
    assert answer_question([item("wallet", "black wallet", "on the desk")], "debit card")["status"] == "found"


def test_not_found_and_empty_query():
    assert answer_question(ITEMS, "umbrella")["status"] == "not_found"
    assert answer_question(ITEMS, "where are my")["status"] == "not_found"
    assert answer_question([], "keys")["status"] == "not_found"
