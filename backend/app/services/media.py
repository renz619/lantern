from pathlib import Path

from app.services.uploads import get_upload_directory


VIDEO_MEDIA_TYPES = {
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
}


def resolve_scan_video_path(scan: dict) -> Path | None:
    """Return a playable upload path without allowing access outside uploads."""
    stored_path = scan.get("video_path")
    if not stored_path:
        return None

    upload_directory = get_upload_directory().resolve()
    video_path = Path(stored_path).resolve()
    try:
        video_path.relative_to(upload_directory)
    except ValueError:
        return None

    return video_path if video_path.is_file() else None


def scan_video_url(scan: dict) -> str | None:
    if resolve_scan_video_path(scan) is None:
        return None
    return f"/media/scans/{scan['id']}/video"


def video_media_type(video_path: Path) -> str:
    return VIDEO_MEDIA_TYPES.get(video_path.suffix.lower(), "application/octet-stream")
