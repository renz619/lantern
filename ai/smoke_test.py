"""Throwaway check: upload a video to Gemini and ask for items with timestamps.

Usage: python ai/smoke_test.py testdata/IMG_1184.mov
"""
import os
import sys
import time

from dotenv import load_dotenv
from google import genai

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
PROMPT = (
    "List the small movable items (keys, wallet, phone, headphones, charger, "
    "glasses, bottle, remote, bag, laptop, book) you can see. Treat furniture only "
    "as locations. For each item give the label, where it is, and the timestamp "
    "in MM:SS."
)


def main(path):
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY") or "paste-your-key" in os.environ["GEMINI_API_KEY"]:
        sys.exit("Set GEMINI_API_KEY in .env first")

    client = genai.Client()
    video = client.files.upload(file=path)
    while video.state.name == "PROCESSING":
        time.sleep(5)
        video = client.files.get(name=video.name)
    if video.state.name != "ACTIVE":
        sys.exit(f"Video processing failed: {video.state.name}")

    try:
        response = client.models.generate_content(model=MODEL, contents=[video, PROMPT])
        print(response.text)
    finally:
        client.files.delete(name=video.name)


if __name__ == "__main__":
    main(sys.argv[1])
