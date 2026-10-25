"""Answer "where are my keys?" from a list of found items.

answer_question(items, query) returns a dict:
    {"status": "found" | "ambiguous" | "not_found",
     "message": text to show the user,
     "matches": the matching items (best first),
     "question": a follow-up question, only when status is "ambiguous",
     "choices": [{"label", "description", "position"}, ...] lined up with matches}

When status is "ambiguous", ask the user the question, then call
answer_question(items, query, choice=<index into choices>) to get the answer.
"""
import re
from difflib import SequenceMatcher

from analyze import normalize_label

STOPWORDS = {
    "where", "wheres", "whats", "what", "is", "are", "was", "were", "my", "me", "the", "a", "an",
    "did", "do", "does", "i", "put", "leave", "left", "find", "show", "last", "seen", "see",
    "you", "know", "have", "can", "of", "to", "in", "at", "on", "it", "them", "that", "this",
    "please", "locate", "get", "got",
}

MIN_SCORE = 0.6
EXACT = 1.0
TIE_MARGIN = 0.1  # lower-scoring matches this close to the best one are still shown


def _words(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _stem(word):
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _same(a, b):
    return _stem(a) == _stem(b)


def query_words(query):
    return [w for w in _words(query.replace("'", "")) if w not in STOPWORDS]


def score_item(item, words):
    """How well one item matches the query words, from 0 to 1."""
    if not words:
        return 0.0
    phrase = " ".join(words)
    label = normalize_label(item["label"])  # saved items may hold an older name, like "id card"
    label_words = _words(label)
    text_words = label_words + _words(item.get("description"))

    if _same(normalize_label(phrase), label) or _same(phrase, label):
        return EXACT
    head = normalize_label(words[-1])  # "phone charger" -> "charger"
    if _same(head, label):
        return 0.9
    if all(any(_same(w, t) for t in text_words) for w in words):
        return 0.8
    if any(_same(w, t) for w in words for t in label_words):
        return 0.7
    return round(SequenceMatcher(None, phrase, label).ratio() * 0.9, 2)


def find_matches(items, query):
    """Items that match the query, best first, keeping only the closest ones."""
    words = query_words(query)
    scored = sorted(
        ((score_item(item, words), item) for item in items),
        key=lambda pair: (-pair[0], pair[1].get("video_seconds", 0)),
    )
    scored = [(s, i) for s, i in scored if s >= MIN_SCORE]
    if not scored:
        return []
    best = scored[0][0]
    cutoff = best if best >= EXACT else best - TIE_MARGIN
    return [item for s, item in scored if s >= cutoff]


def _choice(item):
    return {
        "label": item["label"],
        "description": item.get("description", ""),
        "position": item.get("position", ""),
    }


def _found(item):
    where = item.get("position") or f"near the {item.get('anchor', 'room')}"
    return {
        "status": "found",
        "message": f"Last seen {where}.",
        "matches": [item],
        "question": None,
        "choices": [],
    }


def _ambiguous(matches):
    labels = list(dict.fromkeys(m["label"] for m in matches))
    if len(labels) > 1:
        names = " or ".join(f"your {label}" for label in labels)
        question = f"Did you mean {names}?"
    else:
        question = f"I see {len(matches)} {labels[0]}. Which one do you mean?"
    return {
        "status": "ambiguous",
        "message": question,
        "matches": matches,
        "question": question,
        "choices": [_choice(m) for m in matches],
    }


def answer_question(items, query, choice=None):
    """Find where the query item was last seen; ask a follow-up if it could mean two things."""
    if not query_words(query):
        return {"status": "not_found", "message": "What are you looking for?",
                "matches": [], "question": None, "choices": []}

    matches = find_matches(items, query)
    if not matches:
        return {"status": "not_found", "message": f"I couldn't find \"{query.strip()}\" in the scan.",
                "matches": [], "question": None, "choices": []}
    if choice is not None and 0 <= choice < len(matches):
        return _found(matches[choice])
    if len(matches) == 1:
        return _found(matches[0])
    return _ambiguous(matches)
