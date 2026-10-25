"""Watch a room video with Gemini and return the small movable items found.

analyze_video(path, watchlist) is the function handed to the backend (B).
Set GEMINI_MOCK=1 to get canned items without calling Gemini.
"""
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
PROMPT_FILE = Path(__file__).parent / "prompts" / f"{os.getenv('PROMPT_VERSION', 'analyze_v2')}.txt"
CONFIDENCE_CUTOFF = 0.5

ALLOWLIST = [
    "keys", "wallet", "phone", "airpods", "headphones", "charger", "cable",
    "glasses", "sunglasses", "water bottle", "remote", "backpack", "bag",
    "laptop", "tablet", "book", "pencil", "pen", "notebook", "watch",
    "mouse", "camera", "umbrella", "hat", "id card", "power bank",
    "usb drive", "calculator", "earbud case", "mug", "credit card", "debit card",
    "gift card"
]

# Variants Gemini might use -> our one standard name.
ALIASES = {
    "key": "keys", "key chain": "keys", "keychain": "keys", "car key": "keys",
    "air pods": "airpods", "airpod": "airpods", "earbuds": "airpods",
    "earbud": "airpods", "earphones": "airpods", "earbud case": "airpods",
    "bottle": "water bottle", "water-bottle": "water bottle", "flask": "water bottle",
    "cell phone": "phone", "smartphone": "phone", "iphone": "phone",
    "eyeglasses": "glasses", "spectacles": "glasses",
    "phone charger": "charger", "charging cable": "charger", "usb cable": "cable",
    "power adapter": "charger", "laptop charger": "charger",
    "purse": "bag", "handbag": "bag", "tote": "bag", "tote bag": "bag",
    "mechanical pencil": "pencil", "pen": "pencil", "ballpoint pen": "pen",
    "rucksack": "backpack", "pc mouse": "mouse", "computer mouse": "mouse",
    "tv remote": "remote", "remote control": "remote",
    "computer": "laptop", "notebook computer": "laptop",
    "card holder": "wallet", "cardholder": "wallet", "card sleeve": "wallet",
    "card wallet": "wallet", "billfold": "wallet",
}

# Words that must never appear in a saved description or position (privacy).
PRIVACY_PATTERN = re.compile(
    r"\b(face|person|people|man|woman|boy|girl|wearing|worn|wears|hair|skin|his|her|head)\b"
)


class Item(BaseModel):
    label: str
    description: str
    anchor: str
    position: str
    confidence: float
    video_seconds: float


def normalize_label(label):
    label = label.strip().lower()
    return ALIASES.get(label, label)


def clean_text(text):
    """Blank out any text that mentions a person, so faces never get stored."""
    if PRIVACY_PATTERN.search(text.lower()):
        return None
    return text.strip()


def clean_items(items, watchlist=None, cutoff=CONFIDENCE_CUTOFF):
    """Apply the label standard, the confidence cutoff and the privacy filter."""
    allowed = set(ALLOWLIST) | {normalize_label(w) for w in (watchlist or [])}
    cleaned = []
    for item in items:
        label = normalize_label(item["label"])
        if label not in allowed or item["confidence"] < cutoff:
            continue
        description = clean_text(item["description"]) or label
        position = clean_text(item["position"]) or f"near the {item['anchor']}"
        cleaned.append({
            "label": label,
            "description": description,
            "anchor": item["anchor"].strip().lower(),
            "position": position,
            "confidence": round(float(item["confidence"]), 2),
            "video_seconds": round(float(item["video_seconds"]), 1),
        })
    return sorted(cleaned, key=lambda i: i["video_seconds"])


def build_prompt(watchlist=None):
    text = PROMPT_FILE.read_text(encoding="utf-8")
    text = text.replace("{allowlist}", ", ".join(ALLOWLIST))
    return text.replace("{watchlist}", ", ".join(watchlist) if watchlist else "none")


def mock_items():
    return [
        {"label": "keys", "description": "silver keys on a blue lanyard", "anchor": "desk",
         "position": "on the desk, left of the monitor", "confidence": 0.87, "video_seconds": 14.5},
        {"label": "wallet", "description": "brown leather wallet", "anchor": "desk",
         "position": "on the desk, in front of the keyboard", "confidence": 0.8, "video_seconds": 6.0},
    ]


def generate_with_retry(client, contents, config, attempts=4):
    """Gemini sometimes answers 503 (high demand); wait and try again."""
    from google.genai import errors

    for attempt in range(attempts):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config)
        except errors.ServerError:
            if attempt == attempts - 1:
                raise
            time.sleep(10 * (attempt + 1))


def call_gemini(path, prompt):
    from google import genai
    from google.genai import types

    client = genai.Client()
    video = client.files.upload(file=str(path))
    try:
        while video.state.name == "PROCESSING":
            time.sleep(3)
            video = client.files.get(name=video.name)
        if video.state.name != "ACTIVE":
            raise RuntimeError(f"Video processing failed: {video.state.name}")
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[Item],
            temperature=0.2,
        )
        response = generate_with_retry(client, [video, prompt], config)
    finally:
        client.files.delete(name=video.name)
    return [item.model_dump() for item in response.parsed]


def analyze_video(path, watchlist=None):
    """Return the list of items (contract shape) found in the video at path."""
    load_dotenv()
    if os.getenv("GEMINI_MOCK") == "1":
        return clean_items(mock_items(), watchlist)
    return clean_items(call_gemini(path, build_prompt(watchlist)), watchlist)
