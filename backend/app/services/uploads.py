import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


DEFAULT_UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads"
SUPPORTED_VIDEO_SUFFIXES = {".mkv", ".mov", ".mp4", ".webm"}
DEFAULT_MAX_UPLOAD_BYTES = 250 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class UnsupportedVideoTypeError(ValueError):
    pass


class UploadTooLargeError(ValueError):
    pass


class EmptyUploadError(ValueError):
    pass


def get_upload_directory() -> Path:
    configured_directory = os.getenv("LANTERN_UPLOAD_DIR")
    return (
        Path(configured_directory)
        if configured_directory
        else DEFAULT_UPLOAD_DIRECTORY
    )


def get_max_upload_bytes() -> int:
    return int(os.getenv("LANTERN_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES))


async def save_upload(video: UploadFile) -> Path:
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in SUPPORTED_VIDEO_SUFFIXES:
        raise UnsupportedVideoTypeError

    upload_directory = get_upload_directory()
    upload_directory.mkdir(parents=True, exist_ok=True)
    destination = upload_directory / f"{uuid4().hex}{suffix}"
    total_bytes = 0

    try:
        with destination.open("wb") as saved_video:
            while chunk := await video.read(CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > get_max_upload_bytes():
                    raise UploadTooLargeError
                saved_video.write(chunk)
        if total_bytes == 0:
            raise EmptyUploadError
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await video.close()

    return destination
