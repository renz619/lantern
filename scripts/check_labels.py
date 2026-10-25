"""Check that every item label in the answer sheets and frontend mocks is a standard name.

Usage (from the repo root):
    python scripts/check_labels.py

The standard names are the ALLOWLIST in ai/analyze.py. A label that is only an
alias (for example "pen" for "pencil") or is not on the list at all is reported.
Exits with 1 if anything is reported, so it can run in CI.

The lists are read from ai/analyze.py without importing it, so this needs no
packages beyond Python itself.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZE = ROOT / "ai" / "analyze.py"
FILES = [*sorted((ROOT / "testdata").glob("*.json")), *sorted((ROOT / "frontend" / "src" / "mocks").glob("*.json"))]


def read_standard_names():
    """Return (ALLOWLIST, ALIASES) from ai/analyze.py."""
    wanted = {"ALLOWLIST": None, "ALIASES": None}
    for node in ast.parse(ANALYZE.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            name = getattr(node.targets[0], "id", None)
            if name in wanted:
                wanted[name] = ast.literal_eval(node.value)
    missing = [name for name, value in wanted.items() if value is None]
    if missing:
        sys.exit(f"Could not find {', '.join(missing)} in {ANALYZE}")
    return wanted["ALLOWLIST"], wanted["ALIASES"]


def find_labels(data):
    """Yield every value stored under a "label" key, at any depth."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "label" and isinstance(value, str):
                yield value
            else:
                yield from find_labels(value)
    elif isinstance(data, list):
        for value in data:
            yield from find_labels(value)


def check_file(path, allowlist, aliases):
    problems = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for label in sorted(set(find_labels(data))):
        standard = aliases.get(label.strip().lower(), label.strip().lower())
        if label in allowlist:
            continue
        if standard in allowlist:
            problems.append(f'"{label}" should be "{standard}"')
        else:
            problems.append(f'"{label}" is not in the standard list')
    return problems


def main():
    allowlist, aliases = read_standard_names()
    found_any = False
    for path in FILES:
        for problem in check_file(path, allowlist, aliases):
            found_any = True
            print(f"{path.relative_to(ROOT).as_posix()}: {problem}")
    if found_any:
        print("\nUse the names in ALLOWLIST (ai/analyze.py). A real watchlist item is fine to ignore.")
        sys.exit(1)
    print(f"All labels in {len(FILES)} files are standard names.")


if __name__ == "__main__":
    main()
