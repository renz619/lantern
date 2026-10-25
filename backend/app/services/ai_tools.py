"""Loads member A's search and diff code from the ai/ folder.

ai/answer.py and ai/diff.py import each other by plain name, so ai/ itself has to
be on the import path (the same reason the Gemini adapter in analyzer.py exists).
"""
import sys
from pathlib import Path


AI_DIRECTORY = Path(__file__).resolve().parents[3] / "ai"


def _ensure_ai_on_path() -> None:
    path = str(AI_DIRECTORY)
    if path not in sys.path:
        sys.path.insert(0, path)


def answer_question(items: list[dict], query: str) -> dict:
    _ensure_ai_on_path()
    from answer import answer_question as answer

    return answer(items, query)


def diff_scans(old_items: list[dict], new_items: list[dict]) -> dict:
    _ensure_ai_on_path()
    from diff import diff_scans as diff

    return diff(old_items, new_items)
