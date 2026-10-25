from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas import ScanCreated, ScanDetail, ScanSummary
from app.services.mock_data import get_mock_scan, list_mock_scans, start_mock_scan


router = APIRouter(tags=["scans"])


@router.post("/scans", response_model=ScanCreated, status_code=status.HTTP_202_ACCEPTED)
async def upload_scan(video: Annotated[UploadFile, File()]) -> dict:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Video filename is required")
    return start_mock_scan()


@router.get("/scans", response_model=list[ScanSummary])
def list_scans() -> list[dict]:
    return list_mock_scans()


@router.get("/scans/{scan_id}", response_model=ScanDetail)
def get_scan(scan_id: int) -> dict:
    scan = get_mock_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
