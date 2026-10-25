"""Compare two scans: what moved, went missing, or is new.

Items are paired up by label first, then by how alike their descriptions are, so
two sets of keys are tracked separately. A paired item "moved" when its anchor
(the furniture it sits on) changed. We compare anchors, not the position
sentence, because the AI words that sentence differently on every run.
"""
from difflib import SequenceMatcher

# Two same-label items only count as the same object if their descriptions are
# at least this alike (or they share an anchor). A lone item of its label on
# both sides is always paired.
MIN_DESCRIPTION_MATCH = 0.5


def _norm(text):
    return (text or "").strip().lower()


def _score(old, new):
    similarity = SequenceMatcher(None, _norm(old.get("description")), _norm(new.get("description"))).ratio()
    same_anchor = _norm(old.get("anchor")) == _norm(new.get("anchor")) and _norm(old.get("anchor")) != ""
    return similarity + (0.25 if same_anchor else 0), similarity, same_anchor


def _pair(old_items, new_items):
    """Pair items of ONE label. Returns (pairs, unmatched_old, unmatched_new)."""
    if len(old_items) == 1 and len(new_items) == 1:
        return [(old_items[0], new_items[0])], [], []

    candidates = []
    for i, old in enumerate(old_items):
        for j, new in enumerate(new_items):
            total, similarity, same_anchor = _score(old, new)
            if similarity >= MIN_DESCRIPTION_MATCH or same_anchor:
                candidates.append((total, i, j))

    pairs, used_old, used_new = [], set(), set()
    for _, i, j in sorted(candidates, reverse=True):  # best matches first
        if i in used_old or j in used_new:
            continue
        used_old.add(i)
        used_new.add(j)
        pairs.append((old_items[i], new_items[j]))
    left_old = [o for i, o in enumerate(old_items) if i not in used_old]
    left_new = [n for j, n in enumerate(new_items) if j not in used_new]
    return pairs, left_old, left_new


def _where(item):
    return item.get("position") or item.get("anchor") or ""


def diff_scans(old, new):
    """Return {"moved": [...], "missing": [...], "new": [...]} for two lists of items."""
    labels = []
    for item in [*old, *new]:
        if item["label"] not in labels:
            labels.append(item["label"])

    moved, missing, added = [], [], []
    for label in labels:
        pairs, left_old, left_new = _pair(
            [i for i in old if i["label"] == label],
            [i for i in new if i["label"] == label],
        )
        for before, after in pairs:
            if _norm(before.get("anchor")) != _norm(after.get("anchor")):
                moved.append({
                    "label": label,
                    "description": after.get("description", ""),
                    "from_position": _where(before),
                    "to_position": _where(after),
                })
        missing += [
            {"label": label, "description": i.get("description", ""), "last_position": _where(i)}
            for i in left_old
        ]
        added += [
            {"label": label, "description": i.get("description", ""), "position": _where(i)}
            for i in left_new
        ]
    return {"moved": moved, "missing": missing, "new": added}
