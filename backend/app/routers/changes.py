"""FastAPI route groups for the Lantern backend."""
from fastapi import APIRouter

from app.dependencies import DatabaseConnection
from app.schemas import ChangesResponse
from app.services.search import get_changes as compute_changes


router = APIRouter(tags=["changes"])


@router.get("/changes", response_model=ChangesResponse)
def get_changes(database: DatabaseConnection) -> dict:
    return compute_changes(database)
