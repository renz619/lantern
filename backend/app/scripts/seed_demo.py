"""Create an explicitly synthetic morning/evening demo without calling Gemini."""
import argparse
import shutil
from pathlib import Path
from uuid import uuid4

from app.database import connect_database, create_tables
from app.schemas import Item
from app.services.uploads import SUPPORTED_VIDEO_SUFFIXES, get_upload_directory


DEFAULT_DEMO_DATABASE = Path(__file__).resolve().parents[2] / "demo.sqlite"


def _item(label: str, description: str, anchor: str, seconds: float) -> dict:
    return Item(
        label=label,
        description=description,
        anchor=anchor,
        position=f"on the {anchor}",
        confidence=0.9,
        video_seconds=seconds,
    ).model_dump()


def _demo_scans() -> list[tuple[str, str, list[dict]]]:
    water_bottle = _item("water bottle", "blue reusable water bottle", "table", 12.0)
    return [
        (
            "morning",
            "2026-10-24T09:00:00Z",
            [
                _item("keys", "silver keys on a blue lanyard", "desk", 4.5),
                _item("wallet", "brown leather wallet", "dresser", 8.0),
                water_bottle,
            ],
        ),
        (
            "evening",
            "2026-10-24T18:00:00Z",
            [
                _item("keys", "silver keys on a blue lanyard", "nightstand", 9.2),
                _item("phone", "black phone in a clear case", "bed", 11.2),
                water_bottle,
            ],
        ),
    ]


def _validate_videos(morning: Path | None, evening: Path | None) -> None:
    if (morning is None) != (evening is None):
        raise ValueError("Provide both --morning-video and --evening-video, or neither.")
    for video in (morning, evening):
        if video is None:
            continue
        if not video.is_file():
            raise ValueError(f"Video not found: {video}")
        if video.suffix.lower() not in SUPPORTED_VIDEO_SUFFIXES or video.stat().st_size == 0:
            raise ValueError(f"Video must be nonempty and use a supported video extension: {video}")


def _insert_scan(connection, created_at: str, items: list[dict], video_path: Path | None) -> int:
    cursor = connection.execute(
        "INSERT INTO scans (created_at, status, video_path) VALUES (?, 'done', ?)",
        (created_at, str(video_path) if video_path else None),
    )
    scan_id = int(cursor.lastrowid)
    fields = ("label", "description", "anchor", "position", "confidence", "video_seconds")
    connection.executemany(
        """INSERT INTO sightings
           (scan_id, label, description, anchor, position, confidence, video_seconds)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [(scan_id, *(item[field] for field in fields)) for item in items],
    )
    return scan_id


def seed_demo(
    database_path: str | Path = DEFAULT_DEMO_DATABASE,
    *,
    morning_video: Path | None = None,
    evening_video: Path | None = None,
) -> tuple[int, int]:
    """Seed an empty database once; later calls reuse the same two scan IDs.

    A marker table distinguishes this demo from existing user data. All records
    are written in one transaction; copied videos are removed if seeding fails.
    """
    _validate_videos(morning_video, evening_video)
    connection = connect_database(database_path)
    copied_videos: list[Path] = []
    try:
        create_tables(connection)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS demo_seed_scans (
                    name TEXT PRIMARY KEY,
                    scan_id INTEGER NOT NULL UNIQUE REFERENCES scans(id) ON DELETE CASCADE
                )"""
            )
            existing = dict(connection.execute("SELECT name, scan_id FROM demo_seed_scans"))
            if existing:
                if set(existing) != {"morning", "evening"}:
                    raise ValueError("Incomplete demo data; choose a new empty demo database.")
                return existing["morning"], existing["evening"]
            if connection.execute("SELECT COUNT(*) FROM scans").fetchone()[0]:
                raise ValueError("Database already contains scans; choose a separate empty demo database.")

            scan_ids = []
            for (name, created_at, items), source in zip(
                _demo_scans(), (morning_video, evening_video), strict=True
            ):
                saved_video = None
                if source is not None:
                    upload_directory = get_upload_directory().resolve()
                    upload_directory.mkdir(parents=True, exist_ok=True)
                    saved_video = upload_directory / f"{uuid4().hex}{source.suffix.lower()}"
                    copied_videos.append(saved_video)
                    shutil.copyfile(source, saved_video)
                scan_id = _insert_scan(connection, created_at, items, saved_video)
                connection.execute(
                    "INSERT INTO demo_seed_scans (name, scan_id) VALUES (?, ?)", (name, scan_id)
                )
                scan_ids.append(scan_id)
        return scan_ids[0], scan_ids[1]
    except Exception:
        for video in copied_videos:
            video.unlink(missing_ok=True)
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DEMO_DATABASE)
    parser.add_argument("--morning-video", type=Path)
    parser.add_argument("--evening-video", type=Path)
    arguments = parser.parse_args()
    try:
        morning, evening = seed_demo(
            arguments.database,
            morning_video=arguments.morning_video,
            evening_video=arguments.evening_video,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"Demo seed failed: {error}\n")
    print(f"Synthetic demo data ready: morning scan {morning}, evening scan {evening}.")
    print(f"Database: {arguments.database.resolve()}")
    print("No Gemini requests. These sightings are fake demo data, not AI analysis.")
    print("Existing demo records are reused. Without video arguments, fresh demo scans have no media URL.")
    print("Start the backend with LANTERN_DB_PATH set to this database to use the demo.")


if __name__ == "__main__":
    main()
