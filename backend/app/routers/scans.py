from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from app.database import create_scan, get_database_path, get_scan as get_stored_scan
from app.database import list_scans as list_stored_scans
from app.dependencies import DatabaseConnection
from app.schemas import ScanCreated, ScanDetail, ScanSummary
from app.services.processing import process_scan
from app.services.uploads import (
    EmptyUploadError,
    UnsupportedVideoTypeError,
    UploadTooLargeError,
    save_upload,
)


router = APIRouter(tags=["scans"])


@router.post("/scans", response_model=ScanCreated, status_code=status.HTTP_202_ACCEPTED)
async def upload_scan(
    background_tasks: BackgroundTasks,
    video: Annotated[UploadFile, File()],
    database: DatabaseConnection,
    watchlist: Annotated[list[str] | None, Form()] = None,
) -> dict:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Video filename is required")
    try:
        video_path = await save_upload(video)
    except UnsupportedVideoTypeError as error:
        raise HTTPException(status_code=415, detail="Unsupported video type") from error
    except UploadTooLargeError as error:
        raise HTTPException(status_code=413, detail="Video is too large") from error
    except EmptyUploadError as error:
        raise HTTPException(status_code=400, detail="Video is empty") from error

    try:
        scan_id = create_scan(database, video_path=str(video_path))
    except Exception:
        Path(video_path).unlink(missing_ok=True)
        raise

    background_tasks.add_task(
        process_scan,
        scan_id,
        get_database_path(),
        video_path,
        watchlist,
    )
    return {"scan_id": scan_id}


@router.get("/scans", response_model=list[ScanSummary])
def list_scans(database: DatabaseConnection) -> list[dict]:
    return list_stored_scans(database)


@router.get("/scans/{scan_id}", response_model=ScanDetail)
def get_scan(scan_id: int, database: DatabaseConnection) -> dict:
    scan = get_stored_scan(database, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "id": scan["id"],
        "created_at": scan["created_at"],
        "status": scan["status"],
        "error": scan["error"],
        "video_url": None,
        "items": scan["items"],
    }
