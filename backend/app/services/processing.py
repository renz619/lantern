import logging
from pathlib import Path

from app.database import (
    add_sightings,
    connect_database,
    create_tables,
    update_scan_status,
)
from app.services.analyzer import analyze_video


logger = logging.getLogger(__name__)


def process_scan(
    scan_id: int,
    database_path: str | Path,
    video_path: str | Path,
    watchlist: list[str] | None = None,
) -> None:
    """Analyze one saved video and record either success or failure."""
    connection = connect_database(database_path)
    create_tables(connection)
    try:
        items = analyze_video(video_path, watchlist)
        add_sightings(connection, scan_id, items)
        update_scan_status(connection, scan_id, "done")
    except Exception as error:
        logger.exception("Scan %s failed during analysis", scan_id)
        update_scan_status(connection, scan_id, "failed", str(error)[:500])
    finally:
        connection.close()
