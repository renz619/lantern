# Devpost draft

Submit at hacktx26.devpost.com. Soft submission: Saturday 11:30 PM. Final: Sunday 11:30 AM. Submit with time to spare.

## Name

Lantern (team vote on alternatives was still open in the outline: Memento, Magpie, Engram, Déjà Where).

## Problem

We constantly lose small things at home (keys, wallet, glasses, chargers) and can only remember "somewhere in my room".

## What it does

Film a slow spin around your room. Gemini watches the video and lists the small movable items it sees and where they are, using furniture as location words. Later, ask "where are my keys?" and the app shows where they were last seen and plays the video at that exact moment. It also shows what moved, went missing, or is new between scans.

## How we built it

- Gemini API (Files API for video) for object detection with timestamps
- FastAPI backend, SQLite, ffmpeg for clips
- React mobile-friendly web app
- *(Add only what we really built: Tiger Data, Vultr, SerpApi, Meta Muse, .TECH domain, Raspberry Pi camera.)*

## Challenges

- Gemini misses small items, so we guide users to record slowly with good lighting.
- Consistent names for the same item ("earbuds" vs "headphones").
- Keeping scans to 30-60 seconds for cost and accuracy.

## What it can't do yet

*(Fill in honestly at the end.)*

## Privacy

Processing and saving stay on our own backend, and users can delete scans.

## Checklist

- [ ] Demo video
- [ ] List of what we built it with
- [ ] Clear problem statement
- [ ] Sponsor tracks claimed only if built
- [ ] Optional: DEV article for the $100 writing challenge
