import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import Item


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "lantern.sqlite"
VALID_SCAN_STATUSES = {"processing", "done", "failed"}


def get_database_path() -> Path:
    configured_path = os.getenv("LANTERN_DB_PATH")
    return Path(configured_path) if configured_path else DEFAULT_DATABASE_PATH


def connect_database(path: str | Path | None = None) -> sqlite3.Connection:
    database_path = Path(path) if path is not None else get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('processing', 'done', 'failed')),
            video_path TEXT,
            error TEXT
        );

        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            description TEXT NOT NULL,
            anchor TEXT NOT NULL,
            position TEXT NOT NULL,
            confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
            video_seconds REAL NOT NULL CHECK (video_seconds >= 0),
            clip_path TEXT,
            FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sightings_scan_id
            ON sightings(scan_id);
        CREATE INDEX IF NOT EXISTS idx_sightings_label
            ON sightings(label);
        """
    )
    connection.commit()


def initialize_database(path: str | Path | None = None) -> None:
    connection = connect_database(path)
    try:
        create_tables(connection)
    finally:
        connection.close()


def _validate_status(status: str) -> None:
    if status not in VALID_SCAN_STATUSES:
        allowed = ", ".join(sorted(VALID_SCAN_STATUSES))
        raise ValueError(f"Invalid scan status {status!r}; expected one of: {allowed}")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def create_scan(
    connection: sqlite3.Connection,
    *,
    video_path: str | None = None,
    status: str = "processing",
    created_at: str | None = None,
) -> int:
    _validate_status(status)
    with connection:
        cursor = connection.execute(
            """
            INSERT INTO scans (created_at, status, video_path, error)
            VALUES (?, ?, ?, NULL)
            """,
            (created_at or _utc_now(), status, video_path),
        )
    return int(cursor.lastrowid)


def update_scan_status(
    connection: sqlite3.Connection,
    scan_id: int,
    status: str,
    error: str | None = None,
) -> None:
    _validate_status(status)
    with connection:
        cursor = connection.execute(
            "UPDATE scans SET status = ?, error = ? WHERE id = ?",
            (status, error, scan_id),
        )
    if cursor.rowcount == 0:
        raise KeyError(f"Scan {scan_id} does not exist")


def add_sightings(
    connection: sqlite3.Connection,
    scan_id: int,
    items: list[dict],
) -> None:
    validated_items = [Item.model_validate(item) for item in items]
    with connection:
        connection.executemany(
            """
            INSERT INTO sightings (
                scan_id,
                label,
                description,
                anchor,
                position,
                confidence,
                video_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    scan_id,
                    item.label,
                    item.description,
                    item.anchor,
                    item.position,
                    item.confidence,
                    item.video_seconds,
                )
                for item in validated_items
            ],
        )


def _item_from_row(row: sqlite3.Row) -> dict:
    return {
        "label": row["label"],
        "description": row["description"],
        "anchor": row["anchor"],
        "position": row["position"],
        "confidence": row["confidence"],
        "video_seconds": row["video_seconds"],
    }


def get_scan(connection: sqlite3.Connection, scan_id: int) -> dict | None:
    scan = connection.execute(
        """
        SELECT id, created_at, status, video_path, error
        FROM scans
        WHERE id = ?
        """,
        (scan_id,),
    ).fetchone()
    if scan is None:
        return None

    sightings = connection.execute(
        """
        SELECT label, description, anchor, position, confidence, video_seconds
        FROM sightings
        WHERE scan_id = ?
        ORDER BY video_seconds, id
        """,
        (scan_id,),
    ).fetchall()
    return {
        "id": scan["id"],
        "created_at": scan["created_at"],
        "status": scan["status"],
        "video_path": scan["video_path"],
        "error": scan["error"],
        "items": [_item_from_row(row) for row in sightings],
    }


def list_scans(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        """
        SELECT
            scans.id,
            scans.created_at,
            scans.status,
            COUNT(sightings.id) AS item_count
        FROM scans
        LEFT JOIN sightings ON sightings.scan_id = scans.id
        GROUP BY scans.id
        ORDER BY scans.created_at DESC, scans.id DESC
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "status": row["status"],
            "item_count": row["item_count"],
        }
        for row in rows
    ]
