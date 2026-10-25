from fastapi import APIRouter

from app.schemas import ChangesResponse
from app.services.mock_data import get_mock_changes


router = APIRouter(tags=["changes"])


@router.get("/changes", response_model=ChangesResponse)
def get_changes() -> dict:
    return get_mock_changes()
