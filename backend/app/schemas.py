from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ScanStatus = Literal["processing", "done", "failed"]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Item(ApiModel):
    label: str
    description: str
    anchor: str
    position: str
    confidence: float = Field(ge=0, le=1)
    video_seconds: float = Field(ge=0)


class ScanCreated(ApiModel):
    scan_id: int


class ScanSummary(ApiModel):
    id: int
    created_at: datetime
    status: ScanStatus
    item_count: int = Field(ge=0)


class ScanDetail(ApiModel):
    id: int
    created_at: datetime
    status: ScanStatus
    error: str | None
    video_url: str | None
    items: list[Item]


class FindItem(Item):
    scan_id: int
    seen_at: datetime
    clip_url: str | None
    clip_start_seconds: float = Field(ge=0)


class PastSighting(ApiModel):
    scan_id: int
    seen_at: datetime
    position: str


class Clarification(ApiModel):
    question: str
    options: list[str]


class FindResponse(ApiModel):
    found: bool
    items: list[FindItem]
    past_sightings: list[PastSighting]
    clarify: Clarification | None


class MovedChange(ApiModel):
    label: str
    description: str
    from_position: str
    to_position: str


class MissingChange(ApiModel):
    label: str
    description: str
    last_position: str


class NewChange(ApiModel):
    label: str
    description: str
    position: str


class ChangesResponse(ApiModel):
    from_scan: int | None
    to_scan: int | None
    moved: list[MovedChange]
    missing: list[MissingChange]
    new: list[NewChange]
