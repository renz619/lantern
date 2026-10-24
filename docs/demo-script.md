# Demo script (about 2 minutes)

One sentence for the judges: **"We track movable personal items and use furniture as spatial anchors."**

## Steps

1. **Morning scan.** Film a slow spin around the room. Show the progress message, then the list of found items.
2. **Move things.** Hide the keys under a pillow and move the wallet.
3. **Evening scan.** Scan again.
4. **Search.** Ask "where are my keys?". Show the answer, the time last seen, and the video jumping to that exact moment.
5. **What changed.** Show the summary ("keys moved from desk to nightstand", "wallet moved").

## Before going on stage

- [ ] Seed script run, so the demo works even if a live scan fails (`backend/scripts/seed_demo.py`)
- [ ] Phone charged, camera permission granted, HTTPS tunnel or deployed URL tested
- [ ] Room lit well; keys and wallet placed where Gemini can see them
- [ ] Backup video recorded and on the laptop (in case Wi-Fi fails)
- [ ] Everyone knows who talks and who drives the phone

## If something fails

Switch to the seeded data first, then the backup video. Do not debug live.

## Talking points

- Gemini is the core: it watches the video and returns timestamps.
- Scope choice: small movable items are tracked; furniture is only a location word.
- Privacy: processing and saving stay on our backend; users can delete scans.
- Only mention sponsor prizes we actually built for.
