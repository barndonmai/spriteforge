from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ModeValue = Literal["character", "object", "auto"]
ResolvedModeValue = Literal["character", "object"]


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    stage: str | None
    requested_mode: str
    resolved_mode: str | None
    target_size: int
    error: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class JobResultAsset(BaseModel):
    filename: str
    label: str
    storage_path: str
    width: int
    height: int
    url: str


class JobResultsResponse(BaseModel):
    job_id: str
    status: str
    requested_mode: str
    resolved_mode: str
    target_size: int
    provider: str
    reference_image_path: str
    reference_summary: dict[str, Any] | None
    manifest_path: str
    download_url: str
    completed_at: datetime | None
    outputs: list[JobResultAsset]
