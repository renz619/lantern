from fastapi import APIRouter, Query

from app.dependencies import DatabaseConnection
from app.schemas import FindResponse
from app.services.search import find_items


router = APIRouter(tags=["search"])


@router.get("/find", response_model=FindResponse)
def find_item(database: DatabaseConnection, q: str = Query(min_length=1)) -> dict:
    return find_items(database, q)
