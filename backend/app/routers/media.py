from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.database import get_scan
from app.dependencies import DatabaseConnection
from app.services.media import resolve_scan_video_path, video_media_type


router = APIRouter(prefix="/media", tags=["media"])


@router.get("/scans/{scan_id}/video", response_class=FileResponse)
def serve_scan_video(scan_id: int, database: DatabaseConnection) -> FileResponse:
    scan = get_scan(database, scan_id)
    video_path = resolve_scan_video_path(scan) if scan is not None else None
    if video_path is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video_path, media_type=video_media_type(video_path))
