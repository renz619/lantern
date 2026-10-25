from fastapi import APIRouter, Query

from app.schemas import FindResponse
from app.services.mock_data import find_mock_items


router = APIRouter(tags=["search"])


@router.get("/find", response_model=FindResponse)
def find_item(q: str = Query(min_length=1)) -> dict:
    return find_mock_items(q)
