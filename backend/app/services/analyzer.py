import os
import sys
from copy import deepcopy
from pathlib import Path

from app.services.mock_data import MOCK_ITEMS


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VALID_ANALYZERS = {"mock", "gemini"}


def _analyze_with_gemini(path: str | Path, watchlist: list[str] | None) -> list[dict]:
    repository_path = str(REPOSITORY_ROOT)
    if repository_path not in sys.path:
        sys.path.insert(0, repository_path)

    from ai.analyze import analyze_video as gemini_analyze_video

    return gemini_analyze_video(path, watchlist)


def analyze_video(path: str | Path, watchlist: list[str] | None = None) -> list[dict]:
    """Run the explicitly selected analyzer without falling back on failure."""
    mode = os.getenv("LANTERN_ANALYZER", "mock").strip().lower()
    if mode not in VALID_ANALYZERS:
        raise ValueError(
            f"Invalid LANTERN_ANALYZER {mode!r}; expected one of: gemini, mock"
        )
    if mode == "mock":
        return deepcopy(MOCK_ITEMS)
    if os.getenv("GEMINI_MOCK") == "1":
        raise RuntimeError(
            "GEMINI_MOCK cannot be enabled when LANTERN_ANALYZER is gemini"
        )
    return _analyze_with_gemini(path, watchlist)
